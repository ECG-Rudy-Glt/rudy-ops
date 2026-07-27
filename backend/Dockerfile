FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8082
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8082/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8082", "--workers", "2", "app:app"]
