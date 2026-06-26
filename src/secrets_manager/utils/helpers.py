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
# Define the global config path
global_config_path = os.path.join(os.path.expanduser("~"), ".secrets-manager", ".env")

if os.path.exists(global_config_path):
    load_dotenv(global_config_path)
else:
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

def normalize_repo_url(repo_url: str) -> str:
    """
    Extracts the unique 'owner/repo' identifier from any Git/GitHub URL.
    """
    cleaned = repo_url.strip()
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    cleaned = cleaned.rstrip("/")

    # Already in 'owner/repo' format without protocol or host
    if "/" in cleaned and ":" not in cleaned and "://" not in cleaned:
        parts = cleaned.split("/")
        if len(parts) == 2:
            return f"{parts[0]}/{parts[1]}"

    # SSH format (e.g., git@github.com:owner/repo)
    if ":" in cleaned and not cleaned.startswith("http") and not cleaned.startswith("git://"):
        parts = cleaned.rsplit(":", 1)
        if len(parts) == 2:
            path = parts[1]
            path_parts = path.split("/")
            if len(path_parts) >= 2:
                return f"{path_parts[-2]}/{path_parts[-1]}"

    # HTTP/HTTPS/Git protocols
    if "/" in cleaned:
        path_parts = cleaned.split("/")
        if len(path_parts) >= 2:
            return f"{path_parts[-2]}/{path_parts[-1]}"

    return cleaned


def hash_repo_url(repo_url: str) -> str:
    """Return a SHA-1 hash of the normalized owner/repo identifier."""
    normalized = normalize_repo_url(repo_url)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def get_password():
    """Prompt user for password securely."""
    password = getpass.getpass("Enter master password: ")
    if not password:
        raise ValueError("Password cannot be empty")
    return password


def get_fernet(password: str, salt: bytes = None) -> Fernet:
    """Derive a Fernet key from the password."""
    password_bytes = password.encode()
    if salt is None:
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


