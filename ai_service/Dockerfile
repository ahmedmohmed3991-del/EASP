FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
COPY app.py boundary.py ./
COPY dlp ./dlp
COPY audio ./audio
COPY voice_deepfake ./voice_deepfake
COPY social_engineering ./social_engineering
COPY risk_engine ./risk_engine
COPY models ./models
# Fetch the transcription checkpoint at build time; runtime startup never downloads models.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8', download_root='/app/models/whisper')"
ENV HF_HOME=/app/models/whisper
ENV HOST=0.0.0.0
# The model download path is a snapshot cache; use its model name and matching cache root.
ENV WHISPER_DOWNLOAD_ROOT=/app/models/whisper
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
