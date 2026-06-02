import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('HETZNER_ENDPOINT'),
        aws_access_key_id=os.getenv('HETZNER_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('HETZNER_SECRET_KEY'),
        region_name='eu-central-1'
    )

BUCKET = os.getenv('HETZNER_BUCKET')

def upload(local_path, s3_key):
    s3 = get_s3_client()
    s3.upload_file(local_path, BUCKET, s3_key)
    print(f"  → Lake: {s3_key}")

def download(s3_key, local_path):
    s3 = get_s3_client()
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3.download_file(BUCKET, s3_key, local_path)
    print(f"  ← Lake: {s3_key}")

def list_objects(prefix=''):
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    return [obj['Key'] for obj in response.get('Contents', [])]