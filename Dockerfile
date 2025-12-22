FROM --platform=linux/amd64 selenium/standalone-chrome:latest

USER root

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

ENV PYTHONUNBUFFERED=1
ENV HEADLESS=True

ENTRYPOINT ["python", "main.py"]
