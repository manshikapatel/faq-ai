FROM python:3.11-slim

WORKDIR /app

# System deps (fitz/Unstructured often need these)
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ../requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]