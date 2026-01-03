#!/usr/bin/env python3
"""Generate SSH Ed25519 key pair"""
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os

# Generate private key
private_key = ed25519.Ed25519PrivateKey.generate()

# Serialize private key (PEM format)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Serialize public key (OpenSSH format)
public_key = private_key.public_key()
public_openssh = public_key.public_bytes(
    encoding=serialization.Encoding.OpenSSH,
    format=serialization.PublicFormat.OpenSSH
)

# Create .ssh directory if not exists
os.makedirs(os.path.expanduser("~/.ssh"), mode=0o700, exist_ok=True)

# Save private key
private_key_path = os.path.expanduser("~/.ssh/id_ed25519")
with open(private_key_path, "wb") as f:
    f.write(private_pem)
os.chmod(private_key_path, 0o600)

# Save public key
public_key_path = os.path.expanduser("~/.ssh/id_ed25519.pub")
with open(public_key_path, "wb") as f:
    f.write(public_openssh + b"\n")
os.chmod(public_key_path, 0o644)

print("✅ SSH keys generated successfully!")
print(f"\n📁 Private key: {private_key_path}")
print(f"📁 Public key: {public_key_path}")
print("\n📋 Public key content:")
print(public_openssh.decode())
print("\n📌 Next steps:")
print("1. Copy the public key above")
print("2. Add it to GitHub: https://github.com/settings/keys")
print("3. Click 'New SSH key'")
print("4. Paste the key and save")
print("5. Then run: git push -u origin main")
