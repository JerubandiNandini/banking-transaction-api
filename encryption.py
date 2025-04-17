from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from cryptography.fernet import Fernet
from logging_config import logger
import os

KEY_VAULT_URL = os.getenv("KEY_VAULT_URL", "https://your-vault.vault.azure.net/")
SECRET_NAME = "encryption-key"

try:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    encryption_key = client.get_secret(SECRET_NAME).value or Fernet.generate_key()
except Exception as e:
    logger.warning(f"Failed to fetch Key Vault secret, using default key: {str(e)}")
    encryption_key = Fernet.generate_key()

fernet = Fernet(encryption_key)

def encrypt_data(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    return fernet.decrypt(data.encode()).decode()