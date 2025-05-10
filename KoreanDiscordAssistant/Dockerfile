FROM python:3.11-slim

WORKDIR /app

COPY requirementscloud.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# PORT 환경 변수 사용
ENV PORT=8080

# 실행
CMD ["python", "main.py"]