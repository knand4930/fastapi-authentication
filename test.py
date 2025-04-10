import boto3
import settings

s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AES_SECRET_KEY
)

# List files in the bucket
response = s3.list_objects_v2(Bucket=settings.AWS_BUCKET_NAME)
print("Files in the bucket:")
for obj in response.get('Contents', []):
    print(obj['Key'])

# Upload a file to the bucket
file_path = 'local/path/to/your/file.txt'
s3_key = 'your-folder-name/file.txt'

try:
    s3.upload_file(file_path, settings.AWS_BUCKET_NAME, s3_key)
    print(f"File '{file_path}' uploaded successfully to '{s3_key}'.")
except Exception as e:
    print(f"Failed to upload file: {e}")
