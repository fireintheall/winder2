# Use the official Python 3.11 image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Clone the repository (ensure Git is installed)
RUN apt-get update && apt-get install -y git && \
    git clone https://github.com/fireintheall/winder2.git /tmp/repo && \
    cp -r /tmp/repo/KoreanDiscordAssistant/* /app/ && \
    rm -rf /tmp/repo && \
    apt-get purge -y git && apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirementscloud.txt

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]