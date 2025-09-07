import os
import subprocess
import hashlib

def get_repo_url():
    """Try to extract the repo URL from git config."""
    try:
        return subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        raise RuntimeError("❌ Not a git repo or no remote.origin.url found")

def get_env_path():
    """Return absolute path to .env in current working directory."""
    return os.path.join(os.getcwd(), ".env")

def hash_repo_url(repo_url: str) -> str:
    """Return a SHA-1 hash of the repo URL (safe for S3 keys)."""
    return hashlib.sha1(repo_url.encode("utf-8")).hexdigest()