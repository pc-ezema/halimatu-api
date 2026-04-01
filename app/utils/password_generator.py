import random
import string
import secrets

class PasswordGenerator:
    """Generate secure random passwords"""
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        Generate a random password with:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*"
        
        # Ensure at least one of each required character type
        password_chars = [
            secrets.choice(uppercase),      # At least one uppercase
            secrets.choice(lowercase),      # At least one lowercase
            secrets.choice(digits),         # At least one digit
            secrets.choice(special),        # At least one special character
        ]
        
        # Fill the rest with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        remaining_length = length - len(password_chars)
        
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(all_chars))
        
        # Shuffle the password characters
        secrets.SystemRandom().shuffle(password_chars)
        
        return ''.join(password_chars)
    
    @staticmethod
    def generate_easy_password(length: int = 10) -> str:
        """Generate an easy-to-remember password (no special chars)"""
        # Use only alphanumeric for easy remembering
        chars = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        # Ensure it has at least one uppercase and one number
        if not any(c.isupper() for c in password):
            password = password[1:] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[1:] + secrets.choice(string.digits)
        
        return password
    
    @staticmethod
    def generate_pronounceable_password() -> str:
        """Generate a pronounceable password (easier to remember)"""
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        
        # Create a pattern: consonant + vowel + consonant + vowel + number + special
        password = (
            secrets.choice(consonants) +
            secrets.choice(vowels) +
            secrets.choice(consonants) +
            secrets.choice(vowels) +
            secrets.choice(consonants) +
            str(secrets.randbelow(100)).zfill(2) +
            secrets.choice('!@#$%^&*')
        )
        
        # Capitalize first letter
        password = password[0].upper() + password[1:]
        
        return password