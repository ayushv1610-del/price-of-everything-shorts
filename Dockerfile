FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core fonts-noto-core libraqm0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements-voice.txt ./
RUN pip install --no-cache-dir -r requirements-voice.txt
ENV SHORTS_VOICE_MODEL_DIR=/opt/voice-models
COPY download_voice_models.py ./
RUN python download_voice_models.py
ENV SHORTS_ASR_MODEL_DIR=/opt/asr-model
COPY download_asr_model.py ./
RUN python download_asr_model.py
COPY *.py ./
COPY story_feed.json ./
COPY dashboard.html ./
ENV PORT=8080 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
CMD ["sh","-c","python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
