from cryptography.fernet import Fernet # type: ignore

# Gerar uma nova chave
encryption_key = Fernet.generate_key()

# Exibir a chave gerada
print("Sua chave de encriptação é:")
print(encryption_key.decode())  # Exibe a chave no formato string
