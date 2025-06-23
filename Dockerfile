FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Generate Python gRPC stubs
RUN python -m grpc_tools.protoc -I protos --python_out=. --grpc_python_out=. protos/feed_ranker.proto

EXPOSE 50051
CMD ["python", "grpc_server.py"]
