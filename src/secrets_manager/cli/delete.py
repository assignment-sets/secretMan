# src/secrets_manager/cli/delete.py
import sys
from cryptography.fernet import InvalidToken
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import (
    get_repo_url,
    hash_repo_url,
    get_password,
    get_fernet,
)


def delete_env(repo_url=None):
    if repo_url is None:
        repo_url = get_repo_url()

    key = hash_repo_url(repo_url)
    s3 = get_s3_client()
    bucket = get_bucket_name()

    try:
        # 1. Download the encrypted payload from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        encrypted_content = response["Body"].read()

        # 2. Get password and attempt to decrypt
        password = get_password()
        fernet = get_fernet(password)

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
    repo_url = sys.argv[1] if len(sys.argv) > 1 else None
    delete_env(repo_url)
