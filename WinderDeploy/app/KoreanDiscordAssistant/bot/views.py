import discord
from discord import ui
import logging
from datetime import datetime
from bot.models import Schedule, add_schedule, update_schedule_response, delete_schedule, get_schedules, get_schedule
from bot.utils import parse_datetime, format_datetime

logger = logging.getLogger(__name__)

class ScheduleModal(ui.Modal, title="새 일정 추가"):
    """일정 추가를 위한 모달"""
    
    # 입력 필드 정의
    title = ui.TextInput(
        label="제목",
        placeholder="일정 제목을 입력하세요",
        required=True,
        max_length=100
    )
    
    description = ui.TextInput(
        label="설명",
        placeholder="일정에 대한 설명을 입력하세요",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    time = ui.TextInput(
        label="시간 (YYYY-MM-DD HH:MM)",
        placeholder="예: 2023-12-31 23:00",
        required=True
    )
    
    br = ui.TextInput(
        label="BR",
        placeholder="예: 실버, 골드, 플래티넘 등",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """모달이 제출되었을 때 처리"""
        try:
            # 입력값 가져오기
            title = self.title.value
            description = self.description.value
            time_str = self.time.value
            br = self.br.value
            
            # 시간 파싱
            try:
                time = parse_datetime(time_str)
            except ValueError:
                await interaction.response.send_message(
                    "❌ 시간 형식이 잘못되었습니다. 'YYYY-MM-DD HH:MM' 형식으로 입력해주세요.",
                    ephemeral=True
                )
                return
                
            # 일정 객체 생성
            schedule = Schedule(
                id=0,  # ID는 add_schedule에서 자동 할당
                title=title,
                description=description,
                time=time,
                br=br,
                channel_id=interaction.channel_id
            )
            
            # 일정 추가
            success = add_schedule(schedule)
            
            if not success:
                await interaction.response.send_message("❌ 일정 추가 중 오류가 발생했습니다.", ephemeral=True)
                return
                
            # 성공 메시지
            schedules = get_schedules()
            new_id = max(schedules.keys(), key=int)
            schedule = schedules[new_id]
            
            # 임베드 생성
            embed = discord.Embed(
                title=f"📅 새 일정: {title}",
                description=description,
                color=0x2ecc71  # 초록색
            )
            
            # 시간 포맷팅
            formatted_time = format_datetime(time)
            
            embed.add_field(name="⏰ 시간", value=formatted_time, inline=True)
            embed.add_field(name="🏆 BR", value=br, inline=True)
            embed.add_field(
                name="👥 참가자", 
                value="아래 버튼을 눌러 참가 여부를 선택해주세요.", 
                inline=False
            )
            
            # 응답 버튼 생성
            view = ScheduleResponseView(new_id)
            
            # 모달 응답 완료
            await interaction.response.send_message("✅ 새 일정이 추가되었습니다!", ephemeral=True)
            
            # 채널에 일정 메시지 전송
            message = await interaction.channel.send(embed=embed, view=view)
            
            # 메시지 ID 저장
            schedule.message_id = message.id
            schedules[new_id] = schedule
            from bot.models import save_schedules
            save_schedules(schedules)
            
            logger.info(f"새 일정이 추가되었습니다: ID {new_id}, 제목: {title}")
            
        except Exception as e:
            logger.error(f"일정 추가 중 오류 발생: {e}")
            await interaction.response.send_message(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)


class ScheduleResponseView(ui.View):
    """일정 응답을 위한 버튼 뷰"""
    
    def __init__(self, schedule_id):
        super().__init__(timeout=None)  # 시간 제한 없음
        self.schedule_id = schedule_id
        
    @ui.button(label="참가", style=discord.ButtonStyle.success, emoji="✅")
    async def attend(self, interaction: discord.Interaction, button: ui.Button):
        """참가 버튼 클릭"""
        await self._handle_response(interaction, "참가")
        
    @ui.button(label="보류", style=discord.ButtonStyle.secondary, emoji="⏳")
    async def hold(self, interaction: discord.Interaction, button: ui.Button):
        """보류 버튼 클릭"""
        await self._handle_response(interaction, "보류")
        
    @ui.button(label="미참가", style=discord.ButtonStyle.danger, emoji="❌")
    async def not_attend(self, interaction: discord.Interaction, button: ui.Button):
        """미참가 버튼 클릭"""
        await self._handle_response(interaction, "미참가")
        
    async def _handle_response(self, interaction: discord.Interaction, response: str):
        """응답 처리 로직"""
        try:
            # 사용자 정보 가져오기
            user = interaction.user
            
            # 응답 업데이트
            success = update_schedule_response(
                str(self.schedule_id),
                user.id,
                user.display_name,
                response
            )
            
            if not success:
                await interaction.response.send_message(
                    f"❌ 응답 업데이트 중 오류가 발생했습니다.", 
                    ephemeral=True
                )
                return
                
            # 성공 메시지
            await interaction.response.send_message(
                f"✅ 일정 #{self.schedule_id}에 '{response}' 응답이 등록되었습니다.", 
                ephemeral=True
            )
            
            # 원본 메시지 업데이트 (선택 사항)
            schedule = get_schedule(str(self.schedule_id))
            if schedule and hasattr(interaction, 'message'):
                try:
                    # 임베드 업데이트
                    embed = interaction.message.embeds[0]
                    
                    # 참가자 필드 찾기
                    for i, field in enumerate(embed.fields):
                        if field.name.startswith("👥 참가자"):
                            # 참가자 카운트
                            participants = len(schedule.responses.get("참가", []))
                            on_hold = len(schedule.responses.get("보류", []))
                            not_joining = len(schedule.responses.get("미참가", []))
                            
                            # 필드 업데이트
                            embed.set_field_at(
                                i,
                                name=f"👥 참가자 (참가: {participants} | 보류: {on_hold} | 미참가: {not_joining})",
                                value="아래 버튼을 눌러 참가 여부를 선택해주세요."
                            )
                            break
                            
                    await interaction.message.edit(embed=embed)
                except Exception as e:
                    logger.error(f"메시지 업데이트 중 오류 발생: {e}")
                
        except Exception as e:
            logger.error(f"응답 처리 중 오류 발생: {e}")
            await interaction.response.send_message(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)


class ScheduleDeleteView(ui.View):
    """일정 삭제를 위한 드롭다운 뷰"""
    
    def __init__(self, schedules):
        super().__init__(timeout=300)  # 5분 제한
        self.add_item(ScheduleSelectMenu(schedules))


class ScheduleSelectMenu(ui.Select):
    """일정 선택 드롭다운"""
    
    def __init__(self, schedules):
        options = []
        
        # 각 일정에 대한 옵션 추가
        for schedule_id, schedule in schedules.items():
            # 시간 포맷팅
            formatted_time = format_datetime(schedule.time)
            
            options.append(
                discord.SelectOption(
                    label=f"#{schedule_id}: {schedule.title}",
                    description=f"{formatted_time}",
                    value=schedule_id
                )
            )
            
        super().__init__(
            placeholder="삭제할 일정을 선택하세요...",
            min_values=1,
            max_values=1,
            options=options
        )
        
    async def callback(self, interaction: discord.Interaction):
        """드롭다운에서 일정 선택 시 호출"""
        try:
            schedule_id = self.values[0]
            
            # 일정 정보 가져오기
            schedule = get_schedule(schedule_id)
            if not schedule:
                await interaction.response.send_message(
                    f"❌ ID가 {schedule_id}인 일정을 찾을 수 없습니다.", 
                    ephemeral=True
                )
                return
                
            # 삭제 확인 뷰 생성
            view = ConfirmDeleteView(schedule_id, schedule.title)
            
            await interaction.response.send_message(
                f"⚠️ 정말로 일정 #{schedule_id}: '{schedule.title}'을(를) 삭제하시겠습니까?",
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"일정 선택 중 오류 발생: {e}")
            await interaction.response.send_message(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)


class ConfirmDeleteView(ui.View):
    """일정 삭제 확인 버튼"""
    
    def __init__(self, schedule_id, schedule_title):
        super().__init__(timeout=60)  # 1분 제한
        self.schedule_id = schedule_id
        self.schedule_title = schedule_title
        
    @ui.button(label="삭제", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        """삭제 확인 버튼"""
        try:
            # 일정 삭제
            success = delete_schedule(self.schedule_id)
            
            if not success:
                await interaction.response.send_message(
                    f"❌ 일정 삭제 중 오류가 발생했습니다.", 
                    ephemeral=True
                )
                return
                
            # 성공 메시지
            await interaction.response.send_message(
                f"✅ 일정 #{self.schedule_id}: '{self.schedule_title}'이(가) 삭제되었습니다.", 
                ephemeral=True
            )
            
            # 기존 메시지 비활성화 시도
            schedule = get_schedule(self.schedule_id)
            if not schedule:  # 이미 삭제됨
                try:
                    # 모든 채널 검색
                    for guild in interaction.client.guilds:
                        for channel in guild.text_channels:
                            try:
                                message = await channel.fetch_message(int(schedule.message_id))
                                
                                # 메시지 업데이트 (비활성화)
                                embed = message.embeds[0]
                                embed.title = f"[삭제됨] {embed.title}"
                                embed.color = discord.Color.light_gray()
                                
                                await message.edit(embed=embed, view=None)
                                break
                            except:
                                continue
                except Exception as e:
                    logger.error(f"삭제된 일정 메시지 업데이트 중 오류 발생: {e}")
                    
        except Exception as e:
            logger.error(f"일정 삭제 중 오류 발생: {e}")
            await interaction.response.send_message(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)
            
    @ui.button(label="취소", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        """삭제 취소 버튼"""
        await interaction.response.send_message("❌ 일정 삭제가 취소되었습니다.", ephemeral=True)
