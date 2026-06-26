# src/secrets_manager/cli/delete.py
import argparse
import base64
import sys
from cryptography.fernet import InvalidToken
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import (
    get_repo_url,
    hash_repo_url,
    get_password,
    get_fernet,
)


def delete_env():
    parser = argparse.ArgumentParser(
        description="Verify master password and delete environment secrets from S3."
    )
    parser.add_argument(
        "-r", "--repo",
        help="Git repository URL (default: auto-detected from local git remote)"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt before deleting"
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

    # Deletion safety prompt
    if not args.yes:
        confirm = input(f"⚠️ Are you sure you want to permanently delete secrets for {repo_url}? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("❌ Delete aborted.")
            return

    key = hash_repo_url(repo_url)
    try:
        s3 = get_s3_client()
        bucket = get_bucket_name()
        # 1. Download the encrypted payload from S3
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

        # 2. Get password and attempt to decrypt
        password = get_password()
        fernet = get_fernet(password, salt)

        try:
            fernet.decrypt(encrypted_content)
        except InvalidToken:
            print("❌ Incorrect password. Delete aborted.")
            return

        # 3. If decryption succeeds, proceed with deletion
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"✅ Deleted .env for {repo_url}")

    except s3.exceptions.NoSuchKey:
        print(f"❌ No .env found in S3 for {repo_url}")
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print(f"❌ No .env found in S3 for {repo_url}")
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error deleting .env: {e}")


if __name__ == "__main__":
    delete_env()
