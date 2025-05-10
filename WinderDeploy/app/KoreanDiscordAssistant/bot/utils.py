import pytz
from datetime import datetime, timezone

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_current_time_kst() -> datetime:
    """현재 한국 시간을 반환합니다."""
    return datetime.now(KST)

def format_datetime(dt: datetime) -> str:
    """datetime 객체를 읽기 쉬운 문자열로 변환합니다."""
    # 시간대가 없는 경우 KST 추가
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
        
    # 한국 시간으로 변환
    kst_time = dt.astimezone(KST)
    
    # 요일 한글화
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[kst_time.weekday()]
    
    # 포맷팅된 문자열 반환
    return f"{kst_time.year}년 {kst_time.month}월 {kst_time.day}일 ({weekday}) {kst_time.hour:02d}:{kst_time.minute:02d}"

def parse_datetime(datetime_str: str) -> datetime:
    """문자열을 datetime 객체로 변환합니다."""
    try:
        # ISO 형식 (예: 2023-05-10T16:00:00)
        dt = datetime.fromisoformat(datetime_str)
        
        # 시간대가 없는 경우 KST 추가
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
            
        return dt
        
    except ValueError:
        # ISO 형식이 아닌 경우
        try:
            # 사용자 지정 형식 (예: 2023-05-10 16:00)
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            return dt.replace(tzinfo=KST)
        except ValueError:
            # 그 외 형식은 현재 시간 반환
            return get_current_time_kst()
