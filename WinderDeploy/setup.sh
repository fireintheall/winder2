#!/bin/bash
set -e

# 리포지토리가 이미 존재하는지 확인하고 없는 경우에만 클론
if [ ! -d "app" ] || [ -z "$(ls -A app)" ]; then
  echo "리포지토리 클론 중..."
  rm -rf app
  git clone https://github.com/fireintheall/winder2.git app
fi

echo "Docker 이미지 빌드에 필요한 파일 준비 중..."
echo "참고: 실제 Docker 빌드는 Google Cloud Platform에서 수행됩니다."

# 환경 변수 파일 준비 (예시)
if [ ! -f ".env" ]; then
  echo "환경 변수 샘플 파일 생성 중..."
  cat > .env << EOL
# Discord 봇 환경변수
# 실제 배포 전에 토큰을 입력하되, 저장소에 업로드하지 마세요
DISCORD_TOKEN=YOUR_TOKEN_HERE
BOT_PREFIX=!
DEBUG=False
EOL
  echo ".env 파일이 생성되었습니다. 실제 배포 전에 적절한 값으로 수정하세요."
  echo "주의: 토큰과 같은 민감한 정보는 공개 저장소에 올리지 마세요."
fi

echo "설정이 완료되었습니다!"
echo "Google Cloud에 배포하려면 다음 단계를 따르세요:"
echo "1. .env 파일에 Discord 토큰과 기타 설정을 입력하세요."
echo "2. deploy-to-gcp.sh 스크립트를 실행하세요."
