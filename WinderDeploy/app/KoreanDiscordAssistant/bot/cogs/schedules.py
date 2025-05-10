import discord
from discord.ext import commands
from discord import app_commands
import logging
from bot.models import Schedule, get_schedules, save_schedules, get_schedule, delete_schedule
from bot.utils import format_datetime, parse_datetime, get_current_time_kst
from bot.views import ScheduleModal, ScheduleResponseView, ScheduleDeleteView

logger = logging.getLogger(__name__)

class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # 일정 추가 명령어
    @app_commands.command(name="일정추가", description="새 일정을 추가합니다.")
    async def add_schedule(self, interaction: discord.Interaction):
        """새 일정을 추가합니다."""
        await interaction.response.send_modal(ScheduleModal())
        
    # 일정 목록 명령어
    @app_commands.command(name="일정목록", description="모든 일정을 보여줍니다.")
    async def list_schedules(self, interaction: discord.Interaction):
        """모든 일정을 보여줍니다."""
        schedules = get_schedules()
        
        if not schedules:
            await interaction.response.send_message("❌ 등록된 일정이 없습니다.", ephemeral=True)
            return
            
        embed = discord.Embed(title="📅 일정 목록", 
                           description="현재 등록된 모든 일정입니다.",
                           color=0x3498db)  # 파란색
                           
        for schedule_id, schedule in schedules.items():
            # 시간 포맷팅
            formatted_time = format_datetime(schedule.time)
            
            # 응답 상태 표시
            participants = len(schedule.responses.get("참가", []))
            on_hold = len(schedule.responses.get("보류", []))
            not_joining = len(schedule.responses.get("미참가", []))
            
            embed.add_field(
                name=f"#{schedule_id}: {schedule.title}",
                value=f"📝 {schedule.description}\n"
                     f"⏰ {formatted_time}\n"
                     f"🏆 BR: {schedule.br}\n"
                     f"👥 참가: {participants} | 보류: {on_hold} | 미참가: {not_joining}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)
        
    # 일정 삭제 명령어
    @app_commands.command(name="일정삭제", description="기존 일정을 삭제합니다.")
    async def delete_schedule_command(self, interaction: discord.Interaction):
        """기존 일정을 삭제합니다."""
        schedules = get_schedules()
        
        if not schedules:
            await interaction.response.send_message("❌ 삭제할 일정이 없습니다.", ephemeral=True)
            return
            
        # 삭제할 일정 선택 뷰 생성
        view = ScheduleDeleteView(schedules)
        
        embed = discord.Embed(title="📅 일정 삭제", 
                           description="삭제할 일정을 선택하세요.",
                           color=0xe74c3c)  # 빨간색
        
        for schedule_id, schedule in schedules.items():
            formatted_time = format_datetime(schedule.time)
            embed.add_field(
                name=f"#{schedule_id}: {schedule.title}",
                value=f"⏰ {formatted_time}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    # 직접 메시지 명령어 (!일정현황)
    @commands.command(name="일정현황")
    async def check_schedule_status(self, ctx, schedule_id=None):
        """특정 일정의 현재 응답 상태를 보여줍니다."""
        if not schedule_id:
            await ctx.send("❌ 일정 ID를 입력해주세요. 예: `!일정현황 1`")
            return
            
        try:
            schedule_id = str(schedule_id)
            schedule = get_schedule(schedule_id)
            
            if not schedule:
                await ctx.send(f"❌ ID가 {schedule_id}인 일정을 찾을 수 없습니다.")
                return
                
            # 시간 포맷팅
            formatted_time = format_datetime(schedule.time)
            
            # 현재 시간과 비교해서 상태 표시
            now = get_current_time_kst()
            time_diff = schedule.time - now
            
            status = ""
            if time_diff.total_seconds() < 0:
                status = "⏰ 이미 시작되었습니다"
            else:
                hours, remainder = divmod(time_diff.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                status = f"⏰ {hours}시간 {minutes}분 후 시작"
            
            # 응답자 처리
            participants = schedule.responses.get("참가", [])
            on_hold = schedule.responses.get("보류", [])
            not_joining = schedule.responses.get("미참가", [])
            
            # 임베드 생성
            embed = discord.Embed(title=f"📅 일정 #{schedule_id}: {schedule.title}", 
                                color=0x3498db)
            embed.add_field(name="설명", value=schedule.description, inline=False)
            embed.add_field(name="시간", value=f"{formatted_time} ({status})", inline=True)
            embed.add_field(name="BR", value=schedule.br, inline=True)
            
            # 참가자 목록
            participants_text = "없음"
            if participants:
                participants_text = "\n".join([f"- {name.split(':', 1)[1] if ':' in name else name}" for name in participants])
            embed.add_field(name=f"👥 참가자 ({len(participants)}명)", value=participants_text, inline=False)
            
            # 보류 목록
            on_hold_text = "없음"
            if on_hold:
                on_hold_text = "\n".join([f"- {name.split(':', 1)[1] if ':' in name else name}" for name in on_hold])
            embed.add_field(name=f"⏳ 보류 ({len(on_hold)}명)", value=on_hold_text, inline=False)
            
            # 미참가 목록
            not_joining_text = "없음"
            if not_joining:
                not_joining_text = "\n".join([f"- {name.split(':', 1)[1] if ':' in name else name}" for name in not_joining])
            embed.add_field(name=f"❌ 미참가 ({len(not_joining)}명)", value=not_joining_text, inline=False)
            
            # 응답 버튼 추가
            view = ScheduleResponseView(schedule_id)
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"일정 현황 확인 중 오류 발생: {e}")
            await ctx.send(f"❌ 오류가 발생했습니다: {e}")
