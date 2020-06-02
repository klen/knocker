FROM python:3.8-slim-buster

# Labels
LABEL maintainer="horneds@gmail.com"
LABEL version="0.0.1"

# Dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache -r /app/requirements.txt

# Application
COPY . /app

# Params
HEALTHCHECK --interval=1m --timeout=3s \
  CMD curl -f http://localhost:8000/knocker/status || exit 1
EXPOSE 8000
WORKDIR /app
ENTRYPOINT ["/app/devops/docker-entrypoint.sh"]
CMD ["knocker"]
