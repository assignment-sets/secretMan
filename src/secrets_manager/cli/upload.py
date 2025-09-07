from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import get_repo_url, get_env_path, hash_repo_url
import os

def upload_env():
    repo_url = get_repo_url()
    key = hash_repo_url(repo_url)   # 🔑 use hash for S3 object key
    env_path = get_env_path()

    if not os.path.exists(env_path):
        print("❌ No .env file found in project root.")
        return

    s3 = get_s3_client()
    bucket = get_bucket_name()

    with open(env_path, "rb") as f:
        s3.put_object(Bucket=bucket, Key=key, Body=f)

    print(f"✅ Uploaded .env for {repo_url} (S3 key: {key})")

if __name__ == "__main__":
    upload_env()
