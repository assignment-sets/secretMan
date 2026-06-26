# src/secrets_manager/cli/fetch.py
import argparse
import base64
import os
import sys
from cryptography.fernet import InvalidToken
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import (
    get_repo_url,
    get_env_path,
    hash_repo_url,
    get_password,
    get_fernet,
)


def fetch_env():
    parser = argparse.ArgumentParser(
        description="Download and decrypt environment secrets from S3."
    )
    parser.add_argument(
        "-r", "--repo",
        help="Git repository URL (default: auto-detected from local git remote)"
    )
    parser.add_argument(
        "-o", "--output",
        default=".env",
        help="Path to save the decrypted env file (default: .env)"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force overwrite of existing output file without confirmation"
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

    output_path = os.path.abspath(args.output)

    # Overwrite safety check
    if os.path.exists(output_path) and not args.force:
        print(f"⚠️ Warning: File already exists at: {output_path}")
        confirm = input("Are you sure you want to overwrite it? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("❌ Fetch aborted. File not modified.")
            return

    key = hash_repo_url(repo_url)

    s3 = get_s3_client()
    bucket = get_bucket_name()

    try:
        # 1. Download the encrypted data from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        encrypted_content = response["Body"].read()

        # Extract salt from S3 metadata
        metadata = response.get("Metadata", {})
        salt_b64 = metadata.get("salt")
        if salt_b64:
            salt = base64.b64decode(salt_b64)
        else:
            print("⚠️ Legacy object detected (no salt metadata). Falling back to local FERNET_SALT...")
            salt = None

        # 2. Get password and setup decryption
        password = get_password()
        fernet = get_fernet(password, salt)

        # 3. Decrypt the content
        try:
            decrypted_content = fernet.decrypt(encrypted_content)
        except InvalidToken:
            print("❌ Decryption failed: Invalid password or corrupted data.")
            return

        # 4. Write the decrypted content to the local output file with secure (600) permissions
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600
        with os.fdopen(os.open(output_path, flags, mode), "wb") as f:
            f.write(decrypted_content)

        print(f"✅ Fetched and decrypted {os.path.basename(output_path)} for {repo_url} (S3 key: {key})")

    except s3.exceptions.NoSuchKey:
        print(f"❌ No .env found in S3 for {repo_url}")
    except Exception as e:
        print(f"❌ Error fetching .env: {e}")


if __name__ == "__main__":
    fetch_env()
