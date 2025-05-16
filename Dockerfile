FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8050
EXPOSE $PORT

CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:$PORT", "--workers", "2"]