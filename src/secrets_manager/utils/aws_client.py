# aws_client.py
import boto3
import os
# Define the global config path
global_config_path = os.path.join(os.path.expanduser("~"), ".secrets-manager", ".env")

if os.path.exists(global_config_path):
    load_dotenv(global_config_path)
else:
    load_dotenv()

def get_s3_client():
    """
    Creates and returns an S3 client using environment variables.
    Required envs:
      - AWS_ACCESS_KEY
      - AWS_SECRET_ACCESS_KEY
      - AWS_DEFAULT_REGION
    """
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION")
    )

def get_bucket_name():
    bucket = os.getenv("AWS_S3_BUCKET_NAME")
    if not bucket:
        raise RuntimeError("❌ AWS_S3_BUCKET_NAME is not set in env")
    return bucket
