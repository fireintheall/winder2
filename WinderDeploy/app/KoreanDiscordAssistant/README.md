# 📅 디스코드 일정 관리 봇

디스코드 서버에서 일정을 생성하고 관리하며 참가자 응답을 추적하고 알림을 제공하는 한국어 디스코드 봇입니다.

## 주요 기능

- **일정 생성 및 관리**: 일정 제목, 설명, 시간, BR 등을 설정하여 새로운 일정을 만들 수 있습니다.
- **응답 시스템**: 사용자는 일정에 참가, 보류, 미참가로 응답할 수 있습니다.
- **자동 알림**: 일정 10분 전에 참가자들에게 DM으로 자동 알림을 발송합니다.
- **웹 인터페이스**: 봇 상태 확인을 위한 간단한 웹 인터페이스를 제공합니다.

## 명령어

### 슬래시 명령어
- `/일정추가`: 새 일정을 추가합니다
- `/일정목록`: 모든 일정을 보여줍니다
- `/일정삭제`: 기존 일정을 삭제합니다

### 일반 명령어
- `!일정현황 [ID]`: 특정 일정의 현재 응답 상태를 보여줍니다
- `!help`: 도움말 메시지를 표시합니다

## 설치 방법

1. 이 저장소를 복제합니다
   ```
   git clone https://github.com/username/discord-schedule-bot.git
   cd discord-schedule-bot
   ```

2. 필요한 패키지를 설치합니다
   ```
   pip install -r requirements.txt
   ```

3. `.env` 파일을 생성하고 필요한 환경 변수를 설정합니다
   ```
   # .env 파일 예시
   DISCORD_TOKEN=your_discord_bot_token
   BOT_PREFIX=!
   DEBUG=False
   GUILD_ID=your_guild_id_optional
   ```

4. 봇을 실행합니다
   ```
   python main.py
   ```

## 배포 방법

### Replit에서 배포하기
1. Replit에서 새 프로젝트를 만들고 이 저장소의 코드를 업로드합니다.
2. Secrets 탭에서 `DISCORD_TOKEN` 등의 환경 변수를 설정합니다.
3. Run 버튼을 클릭하여 봇을 실행합니다.
4. (선택) UptimeRobot 등의 서비스를 사용하여 봇이 24/7 실행되도록 설정합니다.

## 프로젝트 구조

```
.
├── bot/                    # 봇 관련 코드
│   ├── cogs/               # 명령어 모듈
│   │   ├── help.py         # 도움말 명령어
│   │   └── schedules.py    # 일정 관련 명령어
│   ├── models.py           # 데이터 모델 및 저장 로직
│   ├── utils.py            # 유틸리티 함수
│   └── views.py            # UI 구성요소 (버튼, 모달 등)
├── templates/              # 웹 인터페이스 템플릿
│   ├── index.html          # 메인 페이지
│   └── ping.html           # 상태 확인 페이지
├── .env.example            # 환경 변수 예시 파일
├── .gitignore              # Git 무시 파일 목록
├── config.py               # 설정 모듈
├── keep_alive.py           # 웹 서버 유지 모듈
├── main.py                 # 메인 실행 파일
├── pyproject.toml          # 프로젝트 메타데이터
└── README.md               # 프로젝트 설명서
```

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 기여하기

기여는 언제나 환영합니다! Issue나 Pull Request를 통해 프로젝트 개선에 참여해주세요.