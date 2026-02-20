from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from .models import RemoteHost, AgentTask, ChatSession, TaskStep
from .services.gemini import AgentExecutor
from .services.ssh import execute_ssh
from .services.security import validate_command
import threading
import logging
import json

logger = logging.getLogger(__name__)

def home_view(request):
    """Home page - list all registered hosts"""
    hosts = RemoteHost.objects.all()
    return render(request, 'index.html', {'hosts': hosts})


@require_http_methods(["GET", "POST"])
def host_new_view(request):
    """Create a new SSH host"""
    if request.method == 'POST':
        RemoteHost.objects.create(
            name=request.POST.get('name'),
            hostname=request.POST.get('hostname'),
            username=request.POST.get('username'),
            password=request.POST.get('password'),
            use_sudo=request.POST.get('use_sudo') == 'on'
        )
        return redirect('hosts')
    
    return render(request, 'host_form.html')


@require_http_methods(["GET", "POST"])
def host_edit_view(request, host_id):
    """Edit an existing SSH host"""
    host = get_object_or_404(RemoteHost, id=host_id)
    
    if request.method == 'POST':
        host.name = request.POST.get('name')
        host.hostname = request.POST.get('hostname')
        host.username = request.POST.get('username')
        host.use_sudo = request.POST.get('use_sudo') == 'on'
        # Only update password if a new one is provided, or update always? 
        # The form makes it required usually, but for edit maybe not?
        # Current form has required attribute. So let's update it.
        password = request.POST.get('password')
        if password:
            host.password = password
        
        host.save()
        return redirect('hosts')
    
    return render(request, 'host_form.html', {'host': host})


@require_http_methods(["POST"])
def host_delete_view(request, host_id):
    """Delete an SSH host"""
    host = get_object_or_404(RemoteHost, id=host_id)
    host.delete()
    return redirect('hosts')


@require_http_methods(["GET"])
def agent_view(request, session_id=None):
    """Agent interface - chat with AI and execute commands"""
    hosts = RemoteHost.objects.all()
    sessions = ChatSession.objects.all()
    
    current_session = None
    tasks = []
    
    if session_id:
        current_session = get_object_or_404(ChatSession, id=session_id)
        tasks = current_session.tasks.all()
        
    return render(request, 'agent.html', {
        'hosts': hosts,
        'sessions': sessions,
        'current_session': current_session,
        'tasks': tasks
    })


def run_agent_bg(task_id: int):
    """Background task to run the agent loop"""
    from django.db import connection
    
    try:
        task = AgentTask.objects.get(id=task_id)
        task.status = 'running'
        task.save()
        
        executor = AgentExecutor(session_id=str(task.session.id) if task.session else None)
        
        step_counter = 1
        
        def execute_callback(cmd: str) -> str:
            # Validate command
            is_valid, error_msg = validate_command(cmd)
            if not is_valid:
                return f"Security Error: {error_msg}"
            
            try:
                return execute_ssh(
                    hostname=task.host.hostname,
                    username=task.host.username,
                    password=task.host.password,
                    command=cmd,
                    use_sudo=getattr(task.host, 'use_sudo', False)
                )
            except Exception as e:
                return f"SSH Error: {str(e)}"

        # Run the loop
        for step_data in executor.run_loop(task.prompt, execute_callback):
            # Create Step record
            step = TaskStep.objects.create(
                task=task,
                step_number=step_counter,
                thought=step_data.get('content') if step_data.get('type') == 'thought' else '',
                command=step_data.get('content') if step_data.get('type') == 'command' else '',
                output=step_data.get('content') if step_data.get('type') == 'output' else '',
                analysis=step_data.get('content') if step_data.get('type') == 'answer' else ''
            )
            
            # If it's an answer, update main task output too
            if step_data.get('type') == 'answer':
                 task.output = step_data.get('content')
                 task.status = 'success'
                 task.save()
            
            # If it's an error
            if step_data.get('type') == 'error':
                task.status = 'error'
                task.output = step_data.get('content')
                task.save()

            step_counter += 1
            
        # If loop finished without answer (e.g. max turns), ensure status is set
        task.refresh_from_db()
        if task.status == 'running':
            task.status = 'success' # Or error if incomplete? Assume success for now.
            task.save()
            
    except Exception as e:
        logger.error(f"Background task failed: {e}")
        try:
             # Re-fetch task to avoid stale data
             t = AgentTask.objects.get(id=task_id)
             t.status = 'error'
             t.output = f"Internal Error: {str(e)}"
             t.save()
        except:
            pass
    finally:
        # Important: Close DB connection for this thread
        connection.close()


@require_http_methods(["POST"])
def agent_execute_view(request):
    """HTMX endpoint - start agent task"""
    prompt = request.POST.get('prompt', '').strip()
    host_id = request.POST.get('host_id')
    session_id = request.POST.get('session_id')
    client_temp_id = request.POST.get('client_temp_id')
    
    if not prompt or not host_id:
        return HttpResponse("Prompt e host são obrigatórios", status=400)
    
    host = get_object_or_404(RemoteHost, id=host_id)
    
    # Get or create session
    current_session = None
    if session_id:
        current_session = get_object_or_404(ChatSession, id=session_id)
    else:
        current_session = ChatSession.objects.create(
            title=prompt[:50] + "..." if len(prompt) > 50 else prompt
        )
    
    # Create initial task
    task = AgentTask.objects.create(
        session=current_session,
        host=host,
        prompt=prompt,
        status='pending'
    )
    
    # Start background thread
    thread = threading.Thread(target=run_agent_bg, args=(task.id,))
    thread.start()
    
    # Return the Chat Message shell, which will poll for updates
    context = {
        'task': task,
        'client_temp_id': client_temp_id,
        'new_session_id': current_session.id if not session_id else None
    }
    return render(request, 'partials/chat_message_shell.html', context)


@require_http_methods(["GET"])
def agent_task_stream_view(request, task_id):
    """Endpoint for polling task updates"""
    task = get_object_or_404(AgentTask, id=task_id)
    steps = task.steps.all().order_by('step_number')
    
    is_running = task.status in ['pending', 'running']

    context = {
        'task': task,
        'steps': steps,
        'is_running': is_running
    }
    
    return render(request, 'partials/agent_steps.html', context)
