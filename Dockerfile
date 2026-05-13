FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt requirements-lock.txt /app/
RUN pip install --no-cache-dir -r requirements-lock.txt

# Install Playwright browsers (already in base image, but just in case)
RUN playwright install chromium

# Copy project files
COPY . /app/

# Expose Django port
EXPOSE 8000
