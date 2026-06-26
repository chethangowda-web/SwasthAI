FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Copy python dependencies
COPY requirements.txt /app/

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY ./app /app/app

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI application using Uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
