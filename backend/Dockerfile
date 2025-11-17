FROM python:3.9-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add pydantic-settings for config management
RUN pip install --no-cache-dir pydantic-settings

# Copy backend code
COPY . .

# Generate gRPC stubs (copy from root)
COPY protos /app/protos
RUN python -m grpc_tools.protoc -I /app/protos --python_out=. --grpc_python_out=. /app/protos/feed_ranker.proto

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
