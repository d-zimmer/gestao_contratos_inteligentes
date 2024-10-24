import base64
from cryptography.fernet import Fernet

# Gerar uma chave de criptografia segura e garantir que ela seja mantida segura
key = base64.urlsafe_b64encode(b'sua_chave_de_criptografia_aqui')  # Substitua por uma chave gerada

cipher = Fernet(key)

def encrypt_private_key(private_key):
    encrypted_key = cipher.encrypt(private_key.encode())
    return encrypted_key

def decrypt_private_key(encrypted_key):
    decrypted_key = cipher.decrypt(encrypted_key).decode()
    return decrypted_key
