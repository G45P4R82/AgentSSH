"""SSH execution service"""
import paramiko
from io import StringIO


def execute_ssh(hostname: str, username: str, password: str, command: str, use_sudo: bool = False) -> str:
    """
    Execute a command on a remote host via SSH.
    
    Args:
        hostname: IP address or domain of the remote host
        username: SSH username
        password: SSH password
        command: Bash command to execute
        use_sudo: If True, retry command with sudo upon permission error
        
    Returns:
        Combined stdout and stderr output from the command
        
    Raises:
        Exception: If SSH connection or command execution fails
    """
    client = None
    try:
        # Create SSH client
        client = paramiko.SSHClient()
        
        # Auto-add host key (MVP only - not production safe)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the remote host
        client.connect(
            hostname=hostname,
            username=username,
            password=password,
            timeout=10
        )
        
        # Execute the command
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        
        # Read output
        output_text = stdout.read().decode('utf-8')
        error_text = stderr.read().decode('utf-8')
        
        # Check for permission errors
        permission_denied = "permission denied" in error_text.lower() or "permission denied" in output_text.lower()
        
        # Auto-retry with sudo if needed
        if permission_denied and use_sudo:
            # Prepare sudo command (reads password from stdin)
            # -S: read password from stdin
            # -p '': remove password prompt
            sudo_command = f"sudo -S -p '' {command}"
            
            stdin, stdout, stderr = client.exec_command(sudo_command, timeout=30)
            
            # Send password
            stdin.write(password + '\n')
            stdin.flush()
            
            # Read output again
            output_text = stdout.read().decode('utf-8')
            error_text = stderr.read().decode('utf-8')
            
            # Add a note that we used sudo
            output_text = f"[Auto-Sudo] {output_text}"
        
        # Combine stdout and stderr
        combined_output = output_text
        if error_text:
            combined_output += f"\n[STDERR]\n{error_text}"
        
        return combined_output if combined_output else "Command executed successfully (no output)"
        
    except paramiko.AuthenticationException:
        raise Exception(f"Authentication failed for {username}@{hostname}")
    except paramiko.SSHException as e:
        raise Exception(f"SSH error: {str(e)}")
    except Exception as e:
        raise Exception(f"Connection error: {str(e)}")
    finally:
        # Clean up connection
        if client:
            client.close()
