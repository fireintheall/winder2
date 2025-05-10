# 디스코드 일정 봇 - Docker & GCP 배포

이 저장소는 [디스코드 일정 봇](https://github.com/fireintheall/winder2.git) 애플리케이션을 컨테이너화하고 Google Cloud Platform에 배포하기 위한 Docker 구성 파일과 배포 스크립트를 포함하고 있습니다.

## 필요 조건

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) 설치됨
- Google Cloud Platform 계정과 프로젝트가 설정됨
- Git이 로컬 머신에 설치됨
- 디스코드 봇 토큰 (Discord Developer Portal에서 획득)

## 시작하기

### 1. 이 저장소를 복제하고 애플리케이션 설정하기

```bash
# 이 저장소 복제
git clone <this-repository-url>
cd <repository-directory>

# 스크립트 실행 가능하게 만들기
chmod +x setup.sh deploy-to-gcp.sh

# 설정 스크립트를 실행하여 디스코드 봇 저장소 복제 및 환경 설정
./setup.sh

# .env 파일 편집하여 디스코드 토큰 및 기타 필요한 환경 변수 설정
nano .env
```

### 2. Google Cloud Platform에 배포하기

1. 먼저 GCP 프로젝트 ID를 설정합니다. `deploy-to-gcp.sh` 파일을 편집하여 `PROJECT_ID` 변수를 자신의 GCP 프로젝트 ID로 바꿉니다:

```bash
nano deploy-to-gcp.sh
# PROJECT_ID="your-gcp-project-id" 행을 찾아 수정하세요
```

2. 배포 스크립트를 실행합니다:

```bash
./deploy-to-gcp.sh
```

3. 메시지가 표시되면 Google Cloud 계정으로 로그인합니다.

4. 배포가 완료되면 Cloud Run 서비스 URL을 통해 애플리케이션에 액세스할 수 있습니다.

### 보안 참고 사항

Discord 봇 토큰은 매우 민감한 정보입니다. 다음 보안 지침을 따라주세요:

1. `.env` 파일에 실제 토큰을 저장할 때는 절대 이 파일을 Git 저장소에 커밋하지 마세요.
2. 이 프로젝트는 `.gitignore` 파일을 통해 `.env` 파일이 Git에 포함되지 않도록 설정되어 있습니다.
3. 토큰이 노출된 경우, Discord Developer Portal에서 즉시 재생성해야 합니다.
4. 프로덕션 환경에서는 Google Cloud Secret Manager를 사용하는 것이 좋습니다:
   ```bash
   # Secret Manager에 토큰 저장
   gcloud secrets create discord-token --replication-policy="automatic"
   echo -n "YOUR_DISCORD_TOKEN" | gcloud secrets versions add discord-token --data-file=-
   
   # Cloud Run 서비스에 Secret 권한 부여
   gcloud secrets add-iam-policy-binding discord-token \
     --member=serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com \
     --role=roles/secretmanager.secretAccessor
   ```

## 파일 구조

- `Dockerfile` - 애플리케이션을 컨테이너화하기 위한 Docker 설정
- `docker-compose.yml` - 로컬 개발 및 테스트용 Docker Compose 구성
- `cloudbuild.yaml` - Google Cloud Build CI/CD 파이프라인 구성
- `setup.sh` - 초기 설정 스크립트
- `deploy-to-gcp.sh` - GCP 배포 스크립트
- `.env` - 환경 변수 파일 (자동 생성됨)

## 참고 사항

- 이 설정은 Discord 봇을 Google Cloud Run에 배포합니다.
- 이 애플리케이션은 항상 실행 상태여야 하며, Cloud Run의 적절한 설정이 필요합니다.
- 추가 설정이나 스케일링이 필요한 경우 GCP 콘솔에서 수동으로 조정할 수 있습니다.
