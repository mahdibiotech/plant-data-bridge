FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY plantbridge ./plantbridge

CMD ["python", "-m", "plantbridge.cli", "--help"]
