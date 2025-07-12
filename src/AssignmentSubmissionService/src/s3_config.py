import boto3
import os
from botocore.exceptions import ClientError

if os.getenv("S3_ACCESS_KEY") is None:
    raise ValueError("S3_ACCESS_KEY environment variable is not set.")
if os.getenv("S3_SECRET_KEY") is None:
    raise ValueError("S3_SECRET_KEY environment variable is not set.")
if os.getenv("S3_ENDPOINT_URL") is None:
    raise ValueError("S3_ENDPOINT_URL environment variable is not set.")

ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
SECRET_KEY = os.getenv("S3_SECRET_KEY")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1") # required by boto3, not used for Seaweed


def create_s3_client():
    """
    Creates a boto3 S3 client configured for SeaweedFS S3-compatible API."""
    s3_client = boto3.client(
        's3',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=AWS_REGION,
        # Optionally disable SSL verification if needed
        # verify=False
    )
    return s3_client

def create_bucket(s3_client, bucket_name):
    """Creates an S3 bucket. SeaweedFS creates it dynamically if it does not exist."""
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created (or already exists).")
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"Bucket '{bucket_name}' already exists and is owned by you.")
        elif e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"Bucket '{bucket_name}' already exists.")
        else:
            print(f"Error creating bucket: {e}")
            raise

def upload_file(s3_client, file_name, bucket, object_name=None):
    """Uploads a file to the S3 bucket."""
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        s3_client.upload_file(file_name, bucket, object_name)
        print(f"File '{file_name}' successfully uploaded to '{bucket}/{object_name}'.")
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False
    return True

def upload_fileobj(s3_client, file_obj, bucket, object_name=None):
    """Uploads a file object to the S3 bucket."""
    if object_name is None:
        object_name = os.path.basename(file_obj.name)

    try:
        s3_client.upload_fileobj(file_obj, bucket, object_name)
        print(f"File object successfully uploaded to '{bucket}/{object_name}'.")
    except ClientError as e:
        print(f"Error uploading file object: {e}")
        return False
    return True

def list_files(s3_client, bucket):
    """Lists all objects in a bucket."""
    print(f"\nContents of bucket '{bucket}':")
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"  - {obj['Key']} (Size: {obj['Size']} bytes)")
        else:
            print("  The bucket is empty.")
    except ClientError as e:
        print(f"Error listing files: {e}")

def download_file(s3_client, bucket, object_name, download_path):
    """Downloads an object from the S3 bucket."""
    try:
        s3_client.download_file(bucket, object_name, download_path)
        print(f"File '{object_name}' successfully downloaded to '{download_path}'.")
    except ClientError as e:
        print(f"Error downloading file: {e}")
        return False
    return True
