import sys
from secrets_manager.utils.aws_client import get_s3_client, get_bucket_name
from secrets_manager.utils.helpers import get_repo_url, hash_repo_url

def delete_env(repo_url=None):
    if repo_url is None:
        repo_url = get_repo_url()

    key = hash_repo_url(repo_url)

    s3 = get_s3_client()
    bucket = get_bucket_name()

    try:
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"✅ Deleted .env for {repo_url} (S3 key: {key})")
    except Exception as e:
        print(f"❌ Error deleting .env: {e}")

if __name__ == "__main__":
    repo_url = sys.argv[1] if len(sys.argv) > 1 else None
    delete_env(repo_url)
