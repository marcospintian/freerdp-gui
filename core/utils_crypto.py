# utils_crypto.py
# Funções utilitárias para criptografia e descriptografia de senhas


from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import binascii

# Chave fixa para exemplo. Em produção, derive de senha mestra ou ambiente.
# 32 bytes para AES-256
SECRET_KEY = os.environ.get("FREERDP_GUI_KEY", "freerdp-gui-key-1234567890123456").encode("utf-8")[:32]
IV_SIZE = 16


def encrypt_password(plain_text: str) -> str:
    backend = default_backend()
    iv = os.urandom(IV_SIZE)
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode("utf-8")) + padder.finalize()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return binascii.hexlify(iv + encrypted).decode("utf-8")


def decrypt_password(enc_text: str) -> str:
    backend = default_backend()
    data = binascii.unhexlify(enc_text)
    iv = data[:IV_SIZE]
    encrypted = data[IV_SIZE:]
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    plain = unpadder.update(padded_data) + unpadder.finalize()
    return plain.decode("utf-8")
