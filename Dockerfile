FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data && \
    if [ ! -f /app/data/custom_assets.json ]; then \
        echo '[]' > /app/data/custom_assets.json; \
    fi

ENV PORT=5001
EXPOSE 5001

CMD ["python", "run.py", "--port", "5001"]
