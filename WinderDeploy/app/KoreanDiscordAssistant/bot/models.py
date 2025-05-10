import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# 파일 경로 설정
SCHEDULES_FILE = "schedules.json"

@dataclass
class Schedule:
    """일정 데이터 클래스"""
    id: int
    title: str
    description: str
    time: datetime
    br: str
    responses: Dict[str, List[str]] = field(default_factory=lambda: {"참가": [], "보류": [], "미참가": []})
    message_id: Optional[int] = None
    channel_id: Optional[int] = None
    notified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Schedule 객체를 딕셔너리로 변환"""
        result = asdict(self)
        # datetime 객체를 ISO 형식 문자열로 변환
        result['time'] = self.time.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """딕셔너리에서 Schedule 객체 생성"""
        # ISO 형식 문자열을 datetime 객체로 변환
        if isinstance(data['time'], str):
            from bot.utils import parse_datetime
            data['time'] = parse_datetime(data['time'])
        return cls(**data)

def get_schedules() -> Dict[str, Schedule]:
    """모든 일정을 가져옵니다."""
    try:
        if not os.path.exists(SCHEDULES_FILE):
            return {}
            
        with open(SCHEDULES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        schedules = {}
        for schedule_id, schedule_data in data.items():
            try:
                schedules[schedule_id] = Schedule.from_dict(schedule_data)
            except Exception as e:
                logger.error(f"일정 {schedule_id} 로드 중 오류 발생: {e}")
                
        return schedules
        
    except Exception as e:
        logger.error(f"일정 로드 중 오류 발생: {e}")
        return {}

def save_schedules(schedules: Dict[str, Schedule]) -> bool:
    """모든 일정을 저장합니다."""
    try:
        # Schedule 객체를 딕셔너리로 변환
        data = {}
        for schedule_id, schedule in schedules.items():
            data[schedule_id] = schedule.to_dict()
            
        # JSON 파일로 저장
        with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return True
        
    except Exception as e:
        logger.error(f"일정 저장 중 오류 발생: {e}")
        return False

def get_schedule(schedule_id: str) -> Optional[Schedule]:
    """특정 ID의 일정을 가져옵니다."""
    schedules = get_schedules()
    return schedules.get(schedule_id)

def add_schedule(schedule: Schedule) -> bool:
    """새 일정을 추가합니다."""
    try:
        schedules = get_schedules()
        
        # 새 ID 생성 (기존 ID 중 가장 큰 숫자 + 1)
        if not schedules:
            new_id = "1"
        else:
            try:
                max_id = max(int(id) for id in schedules.keys())
                new_id = str(max_id + 1)
            except ValueError:
                # ID가 숫자가 아닌 경우
                new_id = "1"
                
        # ID 설정
        schedule.id = int(new_id)
        
        # 일정 추가
        schedules[new_id] = schedule
        
        # 저장
        return save_schedules(schedules)
        
    except Exception as e:
        logger.error(f"일정 추가 중 오류 발생: {e}")
        return False

def update_schedule(schedule_id: str, schedule: Schedule) -> bool:
    """기존 일정을 업데이트합니다."""
    try:
        schedules = get_schedules()
        
        if schedule_id not in schedules:
            logger.warning(f"ID가 {schedule_id}인 일정이 없어 업데이트할 수 없습니다.")
            return False
            
        # 일정 업데이트
        schedules[schedule_id] = schedule
        
        # 저장
        return save_schedules(schedules)
        
    except Exception as e:
        logger.error(f"일정 업데이트 중 오류 발생: {e}")
        return False

def delete_schedule(schedule_id: str) -> bool:
    """기존 일정을 삭제합니다."""
    try:
        schedules = get_schedules()
        
        if schedule_id not in schedules:
            logger.warning(f"ID가 {schedule_id}인 일정이 없어 삭제할 수 없습니다.")
            return False
            
        # 일정 삭제
        del schedules[schedule_id]
        
        # 저장
        return save_schedules(schedules)
        
    except Exception as e:
        logger.error(f"일정 삭제 중 오류 발생: {e}")
        return False

def update_schedule_response(schedule_id: str, user_id: int, user_name: str, response: str) -> bool:
    """사용자의 일정 응답을 업데이트합니다."""
    try:
        schedules = get_schedules()
        
        if schedule_id not in schedules:
            logger.warning(f"ID가 {schedule_id}인 일정이 없어 응답을 업데이트할 수 없습니다.")
            return False
            
        schedule = schedules[schedule_id]
        
        # 사용자 식별자 생성
        user_identifier = f"{user_id}:{user_name}"
        
        # 기존 응답에서 사용자 제거
        for resp_type in ["참가", "보류", "미참가"]:
            # ID 기반 및 이름 기반 모두 확인하여 제거
            schedule.responses[resp_type] = [
                user for user in schedule.responses[resp_type]
                if not (user == user_identifier or 
                       (isinstance(user, str) and user.startswith(f"{user_id}:")))
            ]
            
        # 새 응답에 사용자 추가
        if response in ["참가", "보류", "미참가"]:
            schedule.responses[response].append(user_identifier)
            
        # 일정 업데이트
        schedules[schedule_id] = schedule
        
        # 저장
        return save_schedules(schedules)
        
    except Exception as e:
        logger.error(f"일정 응답 업데이트 중 오류 발생: {e}")
        return False
