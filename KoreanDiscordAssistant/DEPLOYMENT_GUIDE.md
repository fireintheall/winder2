# 디스코드 일정 관리 봇 배포 가이드

이 가이드는 디스코드 일정 관리 봇을 Google Cloud에 배포하는 방법을 설명합니다.

## 목차
1. [사전 준비](#사전-준비)
2. [GitHub에 코드 업로드](#GitHub에-코드-업로드)
3. [Google Cloud 설정](#Google-Cloud-설정)
4. [배포 방법](#배포-방법)
5. [문제 해결](#문제-해결)

## 사전 준비

다음 항목이 필요합니다:
- GitHub 계정
- Google Cloud 계정
- 디스코드 봇 토큰

## GitHub에 코드 업로드

1. GitHub에서 새 저장소를 생성합니다.
2. 다음 명령어를 사용하여 코드를 업로드합니다:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/your-repo-name.git
   git push -u origin master
   ```

## Google Cloud 설정

### 1. Google Cloud SDK 설치
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)를 설치합니다.

### 2. 프로젝트 설정
```
gcloud init
gcloud config set project YOUR_PROJECT_ID
```

### 3. 필요한 API 활성화
```
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## 배포 방법

### 방법 1: Cloud Run Console에서 배포

1. Google Cloud Console에서 Cloud Run으로 이동합니다.
2. "서비스 생성" 버튼을 클릭합니다.
3. GitHub 저장소를 연결하거나 소스 코드를 업로드합니다.
4. 환경 변수에 다음 값을 추가합니다:
   - `DISCORD_TOKEN`: 디스코드 봇 토큰
   - `BOT_PREFIX`: ! (또는 원하는 접두사)
   - `DEBUG`: False
5. "배포" 버튼을 클릭합니다.

### 방법 2: Cloud Build 사용

1. `cloudbuild.yaml` 파일에서 `_DISCORD_TOKEN`을 실제 토큰 값으로 변경합니다.
2. 다음 명령어를 실행합니다:
   ```
   gcloud builds submit --config=cloudbuild.yaml .
   ```

### 방법 3: gcloud 명령어로 배포

1. Dockerfile이 있는 디렉토리에서 다음 명령어를 실행합니다:
   ```
   gcloud run deploy discord-schedule-bot \
     --source . \
     --platform managed \
     --region us-central1 \
     --set-env-vars="DISCORD_TOKEN=your_token,BOT_PREFIX=!,DEBUG=False" \
     --allow-unauthenticated
   ```

## 문제 해결

### 오류: 6bdbe279-7c1e-4e0a-85b2-45a4da86c316

이 오류는 일반적으로 다음과 같은 원인으로 발생합니다:

1. **환경 변수 설정 문제**:
   - 디스코드 토큰이 올바르게 설정되었는지 확인하세요.
   - 콘솔에서 환경 변수를 직접 설정해보세요.

2. **포트 설정 문제**:
   - Cloud Run은 PORT 환경 변수를 통해 포트를 지정합니다.
   - keep_alive.py 파일에서 이 환경 변수를 읽도록 되어 있는지 확인하세요.

3. **권한 문제**:
   - 서비스 계정에 필요한 권한이 있는지 확인하세요.

4. **로그 확인**:
   - Cloud Run 콘솔에서 로그를 확인하여 더 자세한 오류 메시지를 찾아보세요.