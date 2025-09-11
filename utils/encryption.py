# utils/encryption.py
import pyAesCrypt
import os

BUFFER_SIZE = 64 * 1024  # 64KB

def encrypt_file(input_path, password):
    encrypted_path = input_path + '.aes'
    pyAesCrypt.encryptFile(input_path, encrypted_path, password, BUFFER_SIZE)
    return encrypted_path

def decrypt_file(encrypted_path, password):
    decrypted_path = encrypted_path.replace('.aes', '.json')
    pyAesCrypt.decryptFile(encrypted_path, decrypted_path, password, BUFFER_SIZE)
    return decrypted_path

# def cleanup_files(*file_paths):
#     for path in file_paths:
#         if os.path.exists(path):
#             os.remove(path)

def cleanup_files(*paths):
    """Menghapus file-file sementara jika ada."""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Gagal menghapus file {path}: {e}")