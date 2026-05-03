#!/usr/bin/env bash
# Lambda 컨테이너 이미지 빌드 → ECR 푸시 (추천·보컬 SQS 직접 처리)
# 사용: cd ai && ./lambda/sqs_direct/deploy_lambda_containers.sh [all|recommendation|vocal]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
# Lambda x86_64 이미지와 맞춤. Graviton(arm64) Lambda면 DOCKER_PLATFORM=linux/arm64 로 오버라이드.
DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"
KIND="${1:-all}"

if [ -z "$AWS_ACCOUNT_ID" ]; then
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi
REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Account=$AWS_ACCOUNT_ID Region=$AWS_REGION"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

# Lambda/ECR는 BuildKit 기본 attestations(provenance/SBOM)가 붙은 OCI manifest를 거부하는 경우가 많음
# ("image manifest, config or layer media type ... is not supported").
lambda_image_build() {
  local dockerfile="$1" image_tag="$2"
  if docker buildx version >/dev/null 2>&1; then
    BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker buildx build --platform "$DOCKER_PLATFORM" \
      --provenance=false --load \
      -f "$dockerfile" -t "$image_tag" .
  else
    DOCKER_BUILDKIT=0 docker build --platform "$DOCKER_PLATFORM" -f "$dockerfile" -t "$image_tag" .
  fi
}

push_one() {
  local name="$1"
  local dockerfile="$2"
  local repo="$3"
  local tag="${ECR_TAG:-latest}"
  aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" &>/dev/null \
    || aws ecr create-repository --repository-name "$repo" --region "$AWS_REGION"
  lambda_image_build "$dockerfile" "${repo}:${tag}"
  docker tag "${repo}:${tag}" "${REGISTRY}/${repo}:${tag}"
  docker push "${REGISTRY}/${repo}:${tag}"
  echo "Pushed ${REGISTRY}/${repo}:${tag}"
}

if [ "$KIND" = "all" ] || [ "$KIND" = "recommendation" ]; then
  push_one "singchronize-recommendation-lambda" "lambda/sqs_direct/Dockerfile.recommendation" "singchronize-recommendation-lambda"
fi
if [ "$KIND" = "all" ] || [ "$KIND" = "vocal" ]; then
  push_one "singchronize-vocal-lambda" "lambda/sqs_direct/Dockerfile.vocal" "singchronize-vocal-lambda"
fi

echo "완료. Lambda 함수에서 이미지 URI를 위 ECR 로 지정하고, 트리거를 SQS 로 연결하세요."
