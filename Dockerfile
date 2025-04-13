FROM python:3.11-slim

# ffmpegのインストールを追加
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
