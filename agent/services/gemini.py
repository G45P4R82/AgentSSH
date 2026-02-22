"""Gemini API integration service"""
import os
import google.generativeai as genai
import logging
import re
from typing import Generator, Tuple, List, Dict, Any, Callable
from django.conf import settings
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

# Constants
MAX_TURNS = 5
MODEL_NAME = 'gemini-2.5-flash'  # Using a consistent model name

def generate_command(prompt: str, session_id: str = None) -> str:
    """
    Legacy function wrapper.
    """
    executor = AgentExecutor(session_id=session_id)
    return executor.generate_single_command(prompt)

class AgentExecutor:
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key or self.api_key == 'your-gemini-api-key-here':
            raise ValueError("GEMINI_API_KEY not configured in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(MODEL_NAME)
        
        # Configure liberal safety settings for admin tasks
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def load_history(self) -> List[Dict[str, Any]]:
        history = []
        if self.session_id:
            try:
                from agent.models import AgentTask
                previous_tasks = AgentTask.objects.filter(
                    session_id=self.session_id
                ).exclude(
                    prompt__isnull=True
                ).order_by('created_at')

                for task in previous_tasks:
                    if task.prompt:
                        history.append({"role": "user", "parts": [task.prompt]})
                    
                    # Add task execution history if available
                    response_parts = []
                    if task.generated_command: 
                         response_parts.append(f"COMMAND: {task.generated_command}")
                    if task.output:
                         # This would technically be a user message (observation) in many frameworks,
                         # but for simple chat history, we can just append it as context
                         pass 
                         
                    # Check if there are steps
                    for step in task.steps.all():
                        response_parts.append(f"THOUGHT: {step.thought}")
                        response_parts.append(f"COMMAND: {step.command}")
                        response_parts.append(f"OUTPUT: {step.output}")
                        response_parts.append(f"ANALYSIS: {step.analysis}")
                    
                    if response_parts:
                        history.append({"role": "model", "parts": ["\n".join(response_parts)]})

            except Exception as e:
                logger.warning(f"Failed to load history: {e}")
        return history

    def generate_single_command(self, prompt: str) -> str:
        """Legacy support"""
        system_instruction = "You are a Linux Bash Expert. OUTPUT ONLY THE RAW COMMAND."
        model = genai.GenerativeModel(MODEL_NAME, system_instruction=system_instruction)
        response = model.generate_content(
            prompt, 
            safety_settings=self.safety_settings
        )
        return self._clean_command(self._get_response_text(response))

    def run_loop(self, prompt: str, execute_callback: Callable[[str], str], host_name: str = None, host_ip: str = None) -> Generator[Dict[str, Any], None, None]:
        """
        Executes the ReAct loop (Reason, Act, Observe).
        Yields dictionaries with 'type' and 'content'.
        """
        host_context = ""
        if host_name and host_ip:
            host_context = f"\nVOCÊ ESTÁ ATUALMENTE CONECTADO À MÁQUINA: {host_name} ({host_ip}).\nQualquer comando 'COMMAND:' que você fornecer será executado DIRETAMENTE nesta máquina. Não use 'ssh' para se conectar a ela novamente."

        system_instruction = f"""You are an advanced Linux System Administrator Agent.
        Your goal is to solve the user's request by executing bash commands and analyzing their output.{host_context}

        PROTOCOL:
        1. THOUGHT: Explain your reasoning. 
        2. COMMAND: Provide a valid bash command to execute. (Only one command per turn). 'sudo' is implied if needed, but prefer standard user commands.
        3. OUTPUT: Wait for the result.
        4. ANALYSIS: Analyze the output.
        5. Repeat if necessary (max 5 turns).
        6. ANSWER: Provide the final answer to the user in Portuguese.

        FORMAT:
        Use ONLY these prefixes:
        THOUGHT: [Your reasoning]
        COMMAND: [Bash command]
        ANSWER: [Final response]

        If you have the answer, just output ANSWER: ...
        If you need to check something, output THOUGHT: ... followed by COMMAND: ...
        """
        
        # Initialize chat with system instruction
        model = genai.GenerativeModel(MODEL_NAME, system_instruction=system_instruction)
        chat = model.start_chat(history=self.load_history())
        
        current_prompt = prompt
        
        for turn in range(MAX_TURNS):
            try:
                # Send message to model
                response = chat.send_message(
                    current_prompt, 
                    safety_settings=self.safety_settings
                )
                full_text = self._get_response_text(response)
                
                if not full_text:
                    logger.warning("Empty response received from Gemini.")
                    yield {"type": "thought", "content": "O modelo retornou uma resposta vazia. Tentando reformular..."}
                    continue

                # Parse the response
                thought_match = re.search(r'THOUGHT:(.*?)(?=COMMAND:|ANSWER:|$)', full_text, re.DOTALL)
                command_match = re.search(r'COMMAND:(.*?)(?=THOUGHT:|ANSWER:|$)', full_text, re.DOTALL)
                answer_match = re.search(r'ANSWER:(.*?)(?=THOUGHT:|COMMAND:|$)', full_text, re.DOTALL)
                
                thought = thought_match.group(1).strip() if thought_match else ""
                command = command_match.group(1).strip() if command_match else ""
                answer = answer_match.group(1).strip() if answer_match else ""
                
                # If no specific tags, check if it looks like a raw command or raw text
                if not thought and not command and not answer:
                    if "```" in full_text or full_text.strip().startswith("ls") or full_text.strip().startswith("docker"):
                        command = self._clean_command(full_text)
                    else:
                        answer = full_text

                # Yield Thought
                if thought:
                    yield {"type": "thought", "content": thought}

                # Yield Command & Execute
                if command:
                    clean_cmd = self._clean_command(command)
                    yield {"type": "command", "content": clean_cmd}
                    
                    # Execute
                    output = execute_callback(clean_cmd)
                    yield {"type": "output", "content": output}
                    
                    # Prepare next turn
                    current_prompt = f"OUTPUT:\n{output}\n\nAnalyze this output. Do you need another command or do you have the answer?"
                    continue # Continue to next loop iteration
                
                # Yield Answer
                if answer:
                    yield {"type": "answer", "content": answer}
                    break # Done
                
            except Exception as e:
                logger.error(f"Loop error: {e}")
                error_msg = str(e)
                if "finish_reason" in error_msg:
                    error_msg = "O modelo encerrou inesperadamente (provavelmente filtro de segurança)."
                yield {"type": "error", "content": error_msg}
                break

    def _get_response_text(self, response) -> str:
        """Safely extract text from response, handling blocks/errors"""
        try:
            return response.text.strip()
        except ValueError:
            # This happens if response was blocked
            if response.prompt_feedback:
                 logger.warning(f"Response blocked: {response.prompt_feedback}")
            return ""
        except Exception as e:
            logger.error(f"Error extracting response text: {e}")
            return ""

    def _clean_command(self, cmd: str) -> str:
        """Removes markdown code blocks"""
        cmd = cmd.strip()
        # Remove markdown fences
        cmd = re.sub(r'^```\w*\n', '', cmd)
        cmd = re.sub(r'```$', '', cmd)
        return cmd.strip()
