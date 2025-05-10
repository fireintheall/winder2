#!/bin/bash
set -e

# 변수 설정 (필요에 따라 수정)
PROJECT_ID="discord-bot-winder2"
IMAGE_NAME="discord-bot"
REGION="us-central1"
SERVICE_NAME="discord-schedule-bot"

# 필요한 환경 변수 확인
if [ ! -f ".env" ]; then
  echo "오류: .env 파일을 찾을 수 없습니다."
  echo "setup.sh 스크립트를 먼저 실행한 후 .env 파일에 필요한 값을 입력하세요."
  exit 1
fi

# .env 파일에서 환경 변수 로드
source .env

# DISCORD_TOKEN이 기본값인지 확인
if [ "$DISCORD_TOKEN" = "YOUR_TOKEN_HERE" ] || [ -z "$DISCORD_TOKEN" ]; then
  echo "오류: 유효한 DISCORD_TOKEN을 .env 파일에 설정해야 합니다."
  exit 1
fi

# Google Cloud 인증
echo "Google Cloud 인증 중..."
gcloud auth login

# 현재 프로젝트 설정
echo "프로젝트 ID 설정: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
echo "필요한 Google Cloud API 활성화 중..."
gcloud services enable container.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com

# 작업 디렉토리 준비
echo "임시 작업 디렉토리 준비 중..."
mkdir -p deploy_temp
cp cloudbuild.yaml deploy_temp/

# Cloud Build를 사용하여 이미지 빌드 및 배포
echo "Cloud Build를 사용하여 이미지 빌드 및 배포 중..."
gcloud builds submit deploy_temp --config=deploy_temp/cloudbuild.yaml \
  --substitutions=_DISCORD_TOKEN="$DISCORD_TOKEN",_BOT_PREFIX="$BOT_PREFIX",_DEBUG="$DEBUG"

# 임시 디렉토리 정리
rm -rf deploy_temp

echo "배포가 완료되었습니다!"
echo "디스코드 봇 서비스는 이제 Cloud Run에서 액세스할 수 있습니다."
echo "서비스 URL 및 상태를 확인하려면 다음 명령어를 실행하세요:"
echo "gcloud run services describe $SERVICE_NAME --region=$REGION"
