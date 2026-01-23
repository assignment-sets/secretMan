# helpers.py
import os
import sys
import subprocess
import hashlib
import getpass
import base64
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

load_dotenv()


def get_repo_url():
    """Try to extract the repo URL from git config."""
    try:
        return (
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )
    except Exception:
        raise RuntimeError("❌ Not a git repo or no remote.origin.url found")


def get_env_path():
    """Return absolute path to .env in current working directory."""
    return os.path.join(os.getcwd(), ".env")


def hash_repo_url(repo_url: str) -> str:
    """Return a SHA-1 hash of the repo URL (safe for S3 keys)."""
    return hashlib.sha1(repo_url.encode("utf-8")).hexdigest()


def get_password():
    """Prompt user for password securely."""
    password = getpass.getpass("Enter master password: ")
    if not password:
        raise ValueError("Password cannot be empty")
    return password


def get_fernet(password: str) -> Fernet:
    """Derive a Fernet key from the password."""
    password_bytes = password.encode()
    salt_raw = os.getenv("FERNET_SALT")
    
    if salt_raw is None:
        print("❌ Error: FERNET_SALT not found in environment variables.")
        print("Tip: Run 'export FERNET_SALT=your_salt' or add it to ~/.bashrc")
        sys.exit(1)

    salt = salt_raw.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return Fernet(key)


def get_verify_hash(password: str) -> str:
    """Generate a hash to store in S3 metadata for password verification."""
    # We use a different salt or simple hash for the metadata check
    return hashlib.sha256(password.encode()).hexdigest()
