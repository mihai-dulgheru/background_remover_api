FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN python download_model.py

# gunicorn app:app --bind=0.0.0.0:8080 --workers=2 --threads=4 --timeout=300
CMD ["gunicorn", "app:app", "--bind=0.0.0.0:8080", "--workers=2", "--threads=4", "--timeout=300"]
