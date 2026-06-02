import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('HETZNER_ENDPOINT'),
    aws_access_key_id=os.getenv('HETZNER_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('HETZNER_SECRET_KEY'),
    region_name='eu-central-1'
)

buckets = s3.list_buckets()
print("Buckets:", [b['Name'] for b in buckets['Buckets']])

objects = s3.list_objects_v2(Bucket=os.getenv('HETZNER_BUCKET'))
print("Objetos en guadal-lake:")
for obj in objects.get('Contents', []):
    print(f"  {obj['Key']}")