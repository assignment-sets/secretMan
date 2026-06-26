# src/secrets_manager/cli/fetch.py
import sys
import base64
from cryptography.fernet import InvalidToken
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import (
    get_repo_url,
    get_env_path,
    hash_repo_url,
    get_password,
    get_fernet,
)


def fetch_env(repo_url=None):
    if repo_url is None:
        repo_url = get_repo_url()

    key = hash_repo_url(repo_url)  # 🔑 consistent S3 key

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

        # 4. Write the decrypted content to the local .env file
        env_path = get_env_path()
        with open(env_path, "wb") as f:
            f.write(decrypted_content)

        print(f"✅ Fetched and decrypted .env for {repo_url} (S3 key: {key})")

    except s3.exceptions.NoSuchKey:
        print(f"❌ No .env found in S3 for {repo_url}")
    except Exception as e:
        print(f"❌ Error fetching .env: {e}")


if __name__ == "__main__":
    # Check if a repo URL was passed as a command line argument
    repo_url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_env(repo_url_arg)
