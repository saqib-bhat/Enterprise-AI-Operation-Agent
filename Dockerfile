FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch first.
# This prevents sentence-transformers from pulling CUDA/NVIDIA packages.
RUN pip install --no-cache-dir \
    torch==2.3.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Install the remaining application dependencies.
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY frontend ./frontend
COPY scripts ./scripts
COPY .env.example ./.env.example
COPY README.md ./README.md

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]