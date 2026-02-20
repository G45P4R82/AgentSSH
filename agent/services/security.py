"""Security validation service"""

# Blacklist of dangerous command patterns
DANGEROUS_PATTERNS = [
    'rm -rf',
    'rm -fr',
    'shutdown',
    'reboot',
    'mkfs',
    ':(){ :|:& };:',  # fork bomb
    'dd if=/dev/zero',
    '> /dev/sda',
    'mkfs.ext',
    'fdisk',
    'parted',
    'systemctl poweroff',
    'systemctl reboot',
    'init 0',
    'init 6',
    'halt',
    'poweroff',
]


def validate_command(command: str) -> tuple[bool, str]:
    """
    Validate a command against a blacklist of dangerous patterns.
    
    Args:
        command: The bash command to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if command is safe, False if blocked
        - error_message: Empty string if valid, error description if blocked
    """
    # Convert to lowercase for case-insensitive check
    command_lower = command.lower()
    
    # Check against blacklist
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in command_lower:
            return False, f"Comando bloqueado por segurança: contém padrão perigoso '{pattern}'"
    
    return True, ""
