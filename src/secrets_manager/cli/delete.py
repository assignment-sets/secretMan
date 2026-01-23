# src/secrets_manager/cli/delete.py
import sys
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import (
    get_repo_url,
    hash_repo_url,
    get_password,
    get_verify_hash,
)


def delete_env(repo_url=None):
    if repo_url is None:
        repo_url = get_repo_url()

    key = hash_repo_url(repo_url)
    s3 = get_s3_client()
    bucket = get_bucket_name()

    try:
        # 1. Fetch metadata to get the stored hash
        response = s3.head_object(Bucket=bucket, Key=key)
        stored_hash = response.get("Metadata", {}).get("verify-hash")

        if not stored_hash:
            print("⚠️ No password metadata found. Deleting without verification...")
        else:
            # 2. Verify password
            password = get_password()
            input_hash = get_verify_hash(password)

            if input_hash != stored_hash:
                print("❌ Incorrect password. Delete aborted.")
                return

        # 3. Proceed with deletion
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"✅ Deleted .env for {repo_url}")

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
