import discord
from discord.ext import commands
from config import PREFIX
import logging

logger = logging.getLogger(__name__)

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="help")
    async def help_command(self, ctx):
        """도움말 메시지를 표시합니다."""
        embed = discord.Embed(
            title="📅 일정 관리 봇 도움말",
            description="디스코드에서 일정을 생성하고 관리하는 봇입니다.",
            color=0x3498db  # 파란색
        )
        
        # 슬래시 명령어 섹션
        embed.add_field(
            name="🔹 슬래시 명령어",
            value=(
                "`/일정추가` - 새 일정을 추가합니다\n"
                "`/일정목록` - 모든 일정을 보여줍니다\n"
                "`/일정삭제` - 기존 일정을 삭제합니다"
            ),
            inline=False
        )
        
        # 일반 명령어 섹션
        embed.add_field(
            name="🔹 일반 명령어",
            value=(
                f"`{PREFIX}일정현황 [ID]` - 특정 일정의 현재 응답 상태를 보여줍니다\n"
                f"`{PREFIX}help` - 이 도움말 메시지를 표시합니다"
            ),
            inline=False
        )
        
        # 일정 참여 섹션
        embed.add_field(
            name="🔹 일정 참여 방법",
            value=(
                "1. 일정 메시지 하단의 버튼을 클릭하여 참가/보류/미참가 응답을 선택합니다\n"
                "2. 일정 시작 10분 전에 '참가'로 응답한 멤버에게 DM으로 알림이 발송됩니다"
            ),
            inline=False
        )
        
        embed.set_footer(text="도움이 필요하시면 서버 관리자에게 문의하세요.")
        
        await ctx.send(embed=embed)
