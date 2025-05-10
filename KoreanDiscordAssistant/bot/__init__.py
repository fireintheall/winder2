import os
import logging
import discord
from discord.ext import commands
from bot.cogs.schedules import ScheduleCog
from bot.cogs.help import HelpCog
from config import PREFIX

logger = logging.getLogger(__name__)

def create_bot(intents=None):
    """
    디스코드 봇 인스턴스를 생성하고 반환합니다.
    
    Args:
        intents (discord.Intents, optional): 인텐트 설정
        
    Returns:
        discord.ext.commands.Bot: 구성된 디스코드 봇 인스턴스
    """
    # 인텐트가 제공되지 않은 경우, 기본 인텐트 사용
    if intents is None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        
    # 봇 인스턴스 생성
    bot = commands.Bot(command_prefix=PREFIX, 
                        intents=intents, 
                        help_command=None)
    
    # 봇 코그(Cog) 추가
    async def setup_cogs():
        await bot.add_cog(ScheduleCog(bot))
        await bot.add_cog(HelpCog(bot))
        
    # 봇 준비 시 코그(Cog) 설정
    @bot.event
    async def on_ready():
        await setup_cogs()
        logger.info("코그 설정이 완료되었습니다.")
    
    return bot
