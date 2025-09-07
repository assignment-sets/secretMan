import sys
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import get_repo_url, get_env_path, hash_repo_url

def fetch_env(repo_url=None):
    if repo_url is None:
        repo_url = get_repo_url()

    key = hash_repo_url(repo_url)   # 🔑 consistent S3 key

    s3 = get_s3_client()
    bucket = get_bucket_name()

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")

        env_path = get_env_path()
        with open(env_path, "w") as f:
            f.write(content)

        print(f"✅ Fetched .env for {repo_url} (S3 key: {key})")
    except s3.exceptions.NoSuchKey:
        print(f"❌ No .env found in S3 for {repo_url}")
    except Exception as e:
        print(f"❌ Error fetching .env: {e}")

if __name__ == "__main__":
    repo_url = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_env(repo_url)
