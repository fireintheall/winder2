FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirementscloud.txt

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app