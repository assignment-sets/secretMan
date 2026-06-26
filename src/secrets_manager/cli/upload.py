# src/secrets_manager/cli/upload.py
import argparse
import base64
import os
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import (
    get_repo_url,
    get_env_path,
    hash_repo_url,
    get_password,
    get_fernet,
)


def upload_env():
    parser = argparse.ArgumentParser(
        description="Encrypt and upload a local environment file to S3."
    )
    parser.add_argument(
        "-f", "--file",
        default=".env",
        help="Path to the local env file (default: .env)"
    )
    parser.add_argument(
        "-r", "--repo",
        help="Git repository URL (default: auto-detected from local git config)"
    )
    args = parser.parse_args()

    # Resolve repository URL
    repo_url = args.repo
    if not repo_url:
        try:
            repo_url = get_repo_url()
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Tip: Run inside a git repository or supply the repository URL via --repo / -r flag.")
            return

    # Determine env file path
    env_path = os.path.abspath(args.file)
    if not os.path.exists(env_path):
        print(f"❌ No file found at: {env_path}")
        return

    key = hash_repo_url(repo_url)

    password = get_password()
    salt = os.urandom(16)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    fernet = get_fernet(password, salt)

    with open(env_path, "rb") as f:
        raw_data = f.read()

    encrypted_data = fernet.encrypt(raw_data)

    s3 = get_s3_client()
    s3.put_object(
        Bucket=get_bucket_name(),
        Key=key,
        Body=encrypted_data,
        Metadata={"salt": salt_b64},
    )
    print(f"✅ Uploaded {os.path.basename(env_path)} for {repo_url} (S3 key: {key})")


if __name__ == "__main__":
    upload_env()
