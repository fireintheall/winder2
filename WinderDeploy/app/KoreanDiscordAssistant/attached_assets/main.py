import os
import logging
import threading
import time
import asyncio
from datetime import datetime, timedelta
from flask import Flask
import discord
import discord.ext.commands
from bot import create_bot
from bot.models import get_schedules, save_schedules
from keep_alive import keep_alive

keep_alive()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)


@app.route('/')
def index():
    return '디스코드 일정 관리 봇이 실행 중입니다!'


@app.route('/ping')
def ping():
    """Route to keep the app awake"""
    return 'Pong! 봇이 활성화 상태입니다.'


# 전역 봇 인스턴스 (중요: 모든 함수에서 이 변수를 참조해야 함)
bot_instance = None


async def check_upcoming_schedules():
    """일정 시간 10분 전에 참가자들에게 알림 발송"""
    global bot_instance

    # 봇 인스턴스 확인 (주의: 매우 중요!)
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

    # 봇 직접 생성
    bot = discord.ext.commands.Bot(command_prefix="!", intents=intents)

    # 글로벌 변수에 봇 인스턴스 저장 (중요!)
    global bot_instance
    bot_instance = bot
    logger.info(f"봇 인스턴스 초기화 완료: {bot_instance}")

    # 명령어 등록 함수
    def register_commands():
        # 일정 추가 명령어
        @bot.tree.command(name="일정추가", description="새 일정을 추가합니다.")
        async def add_schedule(interaction: discord.Interaction):
            """Add a new schedule"""
            from bot.views import ScheduleModal
            await interaction.response.send_modal(ScheduleModal())

        # 일정 목록 명령어
        @bot.tree.command(name="일정목록", description="모든 일정을 보여줍니다.")
        async def list_schedules(interaction: discord.Interaction):
            """List all schedules"""
            from bot.models import get_schedules

            schedules = get_schedules()

            if not schedules:
                await interaction.response.send_message("❌ 등록된 일정이 없습니다.",
                                                        ephemeral=True)
                return

            embed = discord.Embed(title="📅 일정 목록",
                                  description="현재 등록된 모든 일정입니다.")

            for schedule_id, schedule in schedules.items():
                # KST 시간대 적용 및 포맷팅
                from bot.utils import format_datetime, KST
                if schedule.time.tzinfo is None:
                    schedule.time = schedule.time.replace(tzinfo=KST)
                formatted_time = format_datetime(schedule.time)

                embed.add_field(
                    name=f"#{schedule_id}: {schedule.title}",
                    value=f"시간: {formatted_time}\nBR: {schedule.br}",
                    inline=False)

            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)

        # 일정 삭제 명령어
        @bot.tree.command(name="일정삭제", description="기존 일정을 삭제합니다.")
        @discord.app_commands.describe(일정id="삭제할 일정의 ID")
        async def delete_schedule(interaction: discord.Interaction, 일정id: int):
            """Delete a schedule by ID"""
            from bot.models import get_schedules, save_schedules

            schedules = get_schedules()

            if 일정id not in schedules:
                await interaction.response.send_message(
                    "❌ 해당 일정ID가 존재하지 않습니다.", ephemeral=True)
                return

            schedule = schedules[일정id]

            # Delete the original message if possible
            if schedule.message_id and schedule.channel_id:
                try:
                    channel = bot.get_channel(schedule.channel_id)
                    if channel:
                        try:
                            message = await channel.fetch_message(
                                schedule.message_id)
                            await message.delete()
                        except discord.NotFound:
                            pass  # Message already deleted
                except Exception as e:
                    logger.error(f"일정 메시지 삭제 실패: {e}")

            # Remove from schedules dict
            del schedules[일정id]
            save_schedules(schedules)

            await interaction.response.send_message(f"✅ 일정 #{일정id}가 삭제되었습니다.",
                                                    ephemeral=True)

        # 일정 현황 명령어 (전통적 명령어)
        @bot.command(name="일정현황")
        async def schedule_status(ctx, 일정id: int):
            """Show the current status of a schedule"""
            from bot.models import get_schedules

            schedules = get_schedules()

            if 일정id not in schedules:
                await ctx.send("❌ 해당 일정ID가 존재하지 않습니다.")
                return

            schedule = schedules[일정id]

            # KST 시간대 적용
            from bot.utils import KST, format_datetime
            if schedule.time.tzinfo is None:
                schedule.time = schedule.time.replace(tzinfo=KST)

            # 일정 정보와 함께 시간 표시
            formatted_time = format_datetime(schedule.time)
            embed = discord.Embed(
                title=f"📊 응답 현황 - 일정 #{일정id}: {schedule.title}")
            embed.add_field(name="시간", value=formatted_time, inline=True)
            embed.add_field(name="BR", value=schedule.br, inline=True)

            responses = schedule.responses if hasattr(schedule,
                                                      'responses') else {
                                                          "참가": set(),
                                                          "보류": set(),
                                                          "미참가": set()
                                                      }

            for rtype, users in responses.items():
                # 태그 형식으로 사용자 표시
                mentions = []
                for user_data in users:
                    if ":" in user_data:
                        # ID:닉네임 형식인 경우
                        user_id, _ = user_data.split(":", 1)
                        mentions.append(f"<@{user_id}>")
                    else:
                        # 기존 데이터 형식(호환성 유지)
                        mentions.append(user_data)

                # 태그 텍스트 생성
                if mentions:
                    tag_text = " ".join(mentions)
                    embed.add_field(name=f"{rtype} ({len(users)})",
                                    value=tag_text,
                                    inline=False)
                else:
                    embed.add_field(name=f"{rtype} ({len(users)})",
                                    value="없음",
                                    inline=False)

            await ctx.send(embed=embed)

    # 봇 명령어 등록
    register_commands()

    # 봇 실행
    bot.run(token)


def start_flask():
    """Flask 서버를 별도 스레드에서 실행"""

    app.run(host="0.0.0.0", port=5000, use_reloader=False)


def main():
    """메인 함수: 봇과 웹 서버 실행"""
    # Flask 서버는 별도 스레드에서 실행
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # 디스코드 봇을 실행
    run_discord_bot()


# 메인 함수 호출 (Flask 서버와 디스코드 봇을 동시에 실행)
if __name__ == '__main__':
    main()
