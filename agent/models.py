from django.db import models
from django.contrib.auth.models import User
import uuid

class RemoteHost(models.Model):
    """Model to store SSH host configurations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosts', null=True)
    name = models.CharField(max_length=100, help_text="Display name for the host")
    hostname = models.CharField(max_length=255, help_text="IP address or domain")
    username = models.CharField(max_length=100, help_text="SSH username")
    password = models.CharField(max_length=255, help_text="SSH password (plaintext for MVP)")
    use_sudo = models.BooleanField(default=False, help_text="User has sudo privileges (password used for sudo)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.hostname})"

    class Meta:
        ordering = ['-created_at']


class ChatSession(models.Model):
    """Model to store chat sessions/history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class AgentTask(models.Model):
    """Model to store agent task execution history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    host = models.ForeignKey(RemoteHost, on_delete=models.CASCADE, related_name='tasks')
    prompt = models.TextField(help_text="User's natural language instruction")
    
    # We keep these for backward compatibility or simple summary
    generated_command = models.TextField(help_text="Primary command or summary", blank=True)
    output = models.TextField(help_text="Final analysis or output", blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.host.name} - {self.prompt[:50]} - {self.status}"

    class Meta:
        ordering = ['created_at']


class TaskStep(models.Model):
    """Model to store individual steps in a multi-step agent task"""
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField()
    thought = models.TextField(help_text="AI reasoning before action", blank=True)
    command = models.TextField(help_text="Command executed", blank=True)
    output = models.TextField(help_text="Raw command output", blank=True)
    analysis = models.TextField(help_text="AI analysis of the output", blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['step_number']
