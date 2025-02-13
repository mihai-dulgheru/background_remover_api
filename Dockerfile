FROM python:3.10-slim
RUN apt-get update && apt-get install -y nginx && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN python download_model.py
COPY nginx.conf /etc/nginx/nginx.conf
RUN chmod +x /app/start.sh
EXPOSE 80
CMD ["/app/start.sh"]
