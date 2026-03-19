import boto3
from botocore.exceptions import ClientError
from app.config import settings

# AWS 클라이언트 설정
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

sqs_client = boto3.client(
    "sqs",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

def generate_presigned_url(object_name, expiration=3600):
    """프론트엔드가 S3에 직접 업로드할 수 있는 URL 생성"""
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': object_name,
                'ContentType': 'audio/wav'  # 음성 파일 형식에 맞게 수정 가능
            },
            ExpiresIn=expiration
        )
    except ClientError as e:
        print(f"❌ S3 URL 생성 실패: {e}")
        return None
    return response

def upload_image_to_s3(file_bytes: bytes, key: str, content_type: str = "image/jpeg") -> str | None:
    """S3에 이미지를 직접 업로드하고 public URL 반환"""
    try:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        print(f"❌ S3 이미지 업로드 실패: {e}")
        return None


def send_sqs_message(message_body):
    """SQS 큐에 추천 작업 메시지 전송"""
    try:
        response = sqs_client.send_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MessageBody=message_body
        )
    except ClientError as e:
        print(f"❌ SQS 메시지 전송 실패: {e}")
        return None
    return response['MessageId']