FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NERVE_DATA_DIR=/data
WORKDIR /app
COPY pyproject.toml README.md ./
COPY nerve ./nerve
RUN pip install --no-cache-dir '.[cloud]' && mkdir -p /data && chown -R 10001:10001 /data
USER 10001
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn nerve.cloud_api:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
