FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (already in base image, but just in case)
RUN playwright install chromium

# Copy project files
COPY . /app/

# Expose Django port
EXPOSE 8000
