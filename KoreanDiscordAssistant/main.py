import os
import logging
import threading
import time
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template
import discord
from discord.ext import commands
from bot import create_bot
from bot.models import get_schedules, save_schedules
from keep_alive import keep_alive

# 환경 변수 로드
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# 전역 봇 인스턴스
bot_instance = None

# 봇 시작 함수 정의 (아래에 있는 run_discord_bot 함수를 실행하는 스레드를 시작)
import threading
def start_discord_bot():
    threading.Thread(target=run_discord_bot).start()

@app.route('/')
def index():
    """메인 페이지 라우트"""
    return render_template('index.html')


@app.route('/ping')
def ping():
    """서버 상태 확인 라우트"""
    return render_template('ping.html')


async def check_upcoming_schedules():
    """일정 시간 10분 전에 참가자들에게 알림 발송"""
    global bot_instance

    # 봇 인스턴스 확인
    bot = bot_instance
    if not bot:
        logger.warning("봇 인스턴스가 없어 일정 알림을 보낼 수 없습니다.")
        return

    try:
        # 현재 한국 시간 가져오기
        from bot.utils import get_current_time_kst
        now = get_current_time_kst()
        logger.info(
            f"일정 체크 중... 현재 시간(KST): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        # 로그 추가 - 봇 인스턴스 상태 확인
        logger.info(f"봇 인스턴스 상태: {bot}")

        # 모든 일정 확인
        schedules = get_schedules()
        logger.info(f"총 {len(schedules)}개의 일정 확인 중...")

        for schedule_id, schedule in schedules.items():
            try:
                # 시간대 정보 가져오기
                from bot.utils import KST, format_datetime

                # KST 시간대 설정 (없는 경우)
                if schedule.time.tzinfo is None:
                    schedule.time = schedule.time.replace(tzinfo=KST)

                # 일정 정보 로깅
                formatted_time = format_datetime(schedule.time)
                logger.info(
                    f"일정 #{schedule_id} 확인: {schedule.title}, 시간: {formatted_time}"
                )

                # 일정 시간과 현재 시간의 차이 계산
                time_diff = schedule.time - now
                time_diff_minutes = time_diff.total_seconds() / 60
                logger.info(
                    f"일정 #{schedule_id}까지 남은 시간: {time_diff_minutes:.1f}분")

                # 일정 시간이 10분(600초) 이내인 경우 알림 발송
                if 0 < time_diff.total_seconds() <= 600:
                    # 이미 알림을 보냈는지 확인
                    already_notified = hasattr(
                        schedule, 'notified') and schedule.notified

                    if already_notified:
                        logger.info(f"일정 #{schedule_id}는 이미 알림이 발송되었습니다.")
                        continue

                    logger.info(f"일정 #{schedule_id} 시간이 10분 이내로 다가옴, 알림 발송 시작")

                    # '참가' 응답 참여자 로깅
                    participants = schedule.responses.get("참가", [])
                    logger.info(
                        f"일정 #{schedule_id}의 참가자 수: {len(participants)}")
                    logger.info(f"참가자 데이터: {participants}")

                    # '참가' 응답한 사용자들에게 DM 발송
                    participants_count = 0
                    for user_data in participants:
                        # 사용자 데이터 로그
                        logger.info(f"처리 중인 사용자 데이터: {user_data}")

                        try:
                            # 사용자 ID와 이름 파싱
                            user_id = None
                            display_name = "알 수 없음"

                            if isinstance(user_data, str) and ":" in user_data:
                                user_id_str, display_name = user_data.split(
                                    ":", 1)
                                try:
                                    user_id = int(user_id_str)
                                except ValueError:
                                    logger.warning(
                                        f"유효하지 않은 사용자 ID: {user_id_str}")
                                    continue
                            else:
                                logger.warning(
                                    f"인식할 수 없는 사용자 데이터 형식: {user_data}")
                                continue

                            # 사용자 객체 가져오기
                            if not user_id:
                                logger.warning("사용자 ID가 없어 DM을 보낼 수 없습니다.")
                                continue

                            logger.info(
                                f"사용자 {user_id}({display_name})에게 DM 발송 시도 중..."
                            )

                            # 사용자 조회 시도
                            user = None
                            try:
                                user = await bot.fetch_user(user_id)
                                logger.info(f"사용자 정보 조회 성공: {user}")
                            except Exception as e:
                                logger.error(
                                    f"사용자 정보 조회 실패 (ID: {user_id}): {e}")
                                continue

                            if not user:
                                logger.warning(f"사용자를 찾을 수 없음 (ID: {user_id})")
                                continue

                            # 알림 내용 작성
                            dm_embed = discord.Embed(
                                title="⚔️ 클랜전 알림",
                                description=f"클랜전 시작까지 10분 남았습니다!",
                                color=0xe74c3c  # 빨간색
                            )
                            dm_embed.add_field(
                                name="일정",
                                value=f"#{schedule_id}: {schedule.title}",
                                inline=False)
                            dm_embed.add_field(name="내용",
                                              value=schedule.description,
                                              inline=False)
                            formatted_time = format_datetime(schedule.time)
                            dm_embed.add_field(name="시간",
                                              value=formatted_time,
                                              inline=True)
                            dm_embed.add_field(name="BR",
                                              value=schedule.br,
                                              inline=True)

                            # DM 발송
                            await user.send(embed=dm_embed)
                            logger.info(
                                f"클랜전 알림 DM 발송 성공: {display_name}님에게 일정 #{schedule_id} 알림"
                            )
                            participants_count += 1

                        except discord.Forbidden:
                            logger.warning(f"클랜전 알림 DM 발송 실패: 해당 사용자가 DM을 차단함")
                        except Exception as e:
                            logger.error(f"클랜전 알림 DM 발송 중 오류: {str(e)}")

                    logger.info(f"총 {participants_count}명의 참가자에게 클랜전 알림 발송 완료")

                    # 알림 발송 표시
                    schedule.notified = True
                    save_schedules(schedules)
                    logger.info(
                        f"일정 #{schedule_id}의 알림 발송 상태를 'True'로 변경하고 저장함")

                    # 클랜전을 위한 채널 알림 발송 (메시지가 채널에 있는 경우)
                    if hasattr(schedule, 'channel_id') and schedule.channel_id:
                        try:
                            channel_id = int(schedule.channel_id)
                            logger.info(f"채널 {channel_id}에 알림 발송 시도 중...")

                            # 채널 가져오기
                            channel = bot.get_channel(channel_id)
                            if not channel:
                                try:
                                    channel = await bot.fetch_channel(
                                        channel_id)
                                except:
                                    logger.warning(
                                        f"채널을 찾을 수 없음: {channel_id}")

                            if channel and hasattr(channel, 'send'):
                                channel_embed = discord.Embed(
                                    title="⚔️ 클랜전 시작 10분 전 알림",
                                    description=
                                    f"**{schedule.title}** 클랜전이 곧 시작됩니다!",
                                    color=0xe74c3c)
                                await channel.send(embed=channel_embed)
                                logger.info(
                                    f"클랜전 알림 채널 메시지 발송 성공 (채널 ID: {schedule.channel_id})"
                                )
                            else:
                                logger.warning(
                                    f"채널 {channel_id}에 메시지를 보낼 수 없음")
                        except Exception as e:
                            logger.error(f"클랜전 알림 채널 메시지 발송 실패: {str(e)}")
            except Exception as e:
                logger.error(f"일정 #{schedule_id} 처리 중 오류 발생: {str(e)}")
    except Exception as e:
        logger.error(f"일정 알림 확인 중 오류 발생: {str(e)}")


async def schedule_checker():
    """주기적으로 일정 확인하는 비동기 작업"""
    while True:
        await check_upcoming_schedules()
        # 1분마다 체크
        await asyncio.sleep(60)


def run_discord_bot():
    """디스코드 봇 실행"""
    global bot_instance

    # Get token from environment variable
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logging.error("DISCORD_TOKEN environment variable not set")
        print("Error: Please set the DISCORD_TOKEN environment variable")
        return

    # 인텐트 설정 (모든 권한 활성화)
    intents = discord.Intents.all()

    # 봇 생성 함수 호출
    bot = create_bot(intents)
    
    # 글로벌 변수에 봇 인스턴스 저장
    bot_instance = bot
    logger.info(f"봇 인스턴스 초기화 완료: {bot_instance}")

    # 일정 체크 태스크 추가
    @bot.event
    async def on_ready():
        logger.info(f"봇이 로그인되었습니다: {bot.user} (ID: {bot.user.id})")
        logger.info(f"Discord.py 버전: {discord.__version__}")
        
        # 봇 활동 상태 설정
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="일정 관리 | !help"))
        
        # 일정 체크 태스크 시작
        bot.loop.create_task(schedule_checker())
        
        # 슬래시 명령어 동기화
        try:
            from config import GUILD_ID
            if GUILD_ID:
                guild = discord.Object(id=int(GUILD_ID))
                await bot.tree.sync(guild=guild)
                logger.info(f"길드 {GUILD_ID}에 슬래시 명령어를 동기화했습니다.")
            else:
                await bot.tree.sync()
                logger.info("전역 슬래시 명령어를 동기화했습니다.")
        except Exception as e:
            logger.error(f"슬래시 명령어 동기화 중 오류 발생: {e}")

    # 봇 실행
    try:
        logger.info("봇 실행 중...")
        bot.run(token)
    except discord.errors.LoginFailure:
        logger.error("봇 토큰이 유효하지 않습니다.")
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {e}")


# 디스코드 봇 시작 (웹 서버와 별개로 작동하도록)
start_discord_bot()

if __name__ == "__main__":
    # 봇 실행 준비
    try:
        # 웹 서버 실행
        keep_alive()
        logger.info("웹 서버가 시작되었습니다.")
    except Exception as e:
        logger.error(f"애플리케이션 시작 중 오류 발생: {e}")
