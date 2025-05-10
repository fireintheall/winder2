# Use the official Python 3.11 image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY app/KoreanDiscordAssistant/requirementscloud.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirementscloud.txt

# Copy the application
COPY app/KoreanDiscordAssistant/ .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]
