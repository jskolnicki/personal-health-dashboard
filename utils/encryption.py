import os
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json

class EncryptionManager:
    def __init__(self, key=None):
        """
        Initialize encryption manager with a key.
        If no key provided, gets from environment variable ENCRYPTION_KEY.
        """
        if key is None:
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                raise ValueError("ENCRYPTION_KEY environment variable not set")
        
        # Generate a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'personal_health_dashboard',  # Fixed salt for consistent key derivation
            iterations=100000,
        )
        key_bytes = key.encode()
        key = b64encode(kdf.derive(key_bytes))
        
        self.fernet = Fernet(key)

    def encrypt_credentials(self, credentials_dict):
        """
        Encrypt a dictionary of credentials.
        
        Args:
            credentials_dict (dict): Dictionary containing credentials
            
        Returns:
            bytes: Encrypted credentials
        """
        if not isinstance(credentials_dict, dict):
            raise ValueError("credentials_dict must be a dictionary")
            
        # Convert dict to JSON string
        json_data = json.dumps(credentials_dict)
        
        # Encrypt the JSON string
        encrypted_data = self.fernet.encrypt(json_data.encode())
        
        return encrypted_data

    def decrypt_credentials(self, encrypted_data):
        """
        Decrypt encrypted credentials back to a dictionary.
        
        Args:
            encrypted_data (bytes): Encrypted credentials
            
        Returns:
            dict: Decrypted credentials dictionary
        """
        if not encrypted_data:
            return {}
            
        # Decrypt the data
        decrypted_data = self.fernet.decrypt(encrypted_data)
        
        # Parse JSON string back to dictionary
        credentials_dict = json.loads(decrypted_data.decode())
        
        return credentials_dict