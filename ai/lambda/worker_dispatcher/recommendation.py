"""
[폐지] ECS RunTask 디스패처는 제거되었습니다.

프로덕션: SQS → Lambda(컨테이너) 직접 처리
  - 소스: lambda/sqs_direct/recommendation_handler.py (이미지 내 recommendation.py 로 복사)
  - Docker: lambda/sqs_direct/Dockerfile.recommendation
  - 배포: lambda/sqs_direct/deploy_lambda_containers.sh recommendation

Lambda 콘솔 핸들러: recommendation.handler
"""

def handler(event, context):  # noqa: ARG001
    raise RuntimeError(
        "이 ZIP/레이어 조합은 더 이상 지원하지 않습니다. "
        "lambda/sqs_direct/Dockerfile.recommendation 로 컨테이너 Lambda 를 배포하세요."
    )
