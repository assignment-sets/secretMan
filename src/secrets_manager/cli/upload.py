# src/secrets_manager/cli/upload.py
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import (
    get_repo_url,
    get_env_path,
    hash_repo_url,
    get_password,
    get_fernet,
    get_verify_hash,  # Added this
)
import os


def upload_env():
    repo_url = get_repo_url()
    key = hash_repo_url(repo_url)
    env_path = get_env_path()

    if not os.path.exists(env_path):
        print("❌ No .env file found in project root.")
        return

    password = get_password()
    fernet = get_fernet(password)
    verify_hash = get_verify_hash(password)  # Generate verification hash

    with open(env_path, "rb") as f:
        raw_data = f.read()

    encrypted_data = fernet.encrypt(raw_data)

    s3 = get_s3_client()
    s3.put_object(
        Bucket=get_bucket_name(),
        Key=key,
        Body=encrypted_data,
        Metadata={"verify-hash": verify_hash},  # Store hash in S3 metadata
    )
    print(f"✅ Uploaded .env for {repo_url} (S3 key: {key})")


if __name__ == "__main__":
    upload_env()
