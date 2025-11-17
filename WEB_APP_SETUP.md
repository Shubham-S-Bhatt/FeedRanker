# FeedRanker Web Application - Quick Start Guide

## 🚀 Project Structure

```
FeedRanker/
├── backend/                    # FastAPI REST API wrapper
│   ├── main.py                # FastAPI app with ranking endpoints
│   ├── config.py              # Configuration management
│   ├── database.py            # SQLAlchemy ORM models
│   ├── Dockerfile             # Backend container
│   └── requirements.txt
├── frontend/                   # React TypeScript web UI
│   ├── src/
│   │   ├── App.tsx            # Main app with routing
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   ├── store.ts           # Zustand store (state management)
│   │   ├── main.tsx
│   │   └── index.css
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile             # Frontend container
│   └── package.json
├── models/                     # Trained ML models (created during training)
├── protos/                     # Protocol Buffer definitions
├── data_preprocessing.py       # PySpark ETL pipeline
├── train_lambdamart.py        # LambdaMART training
├── train_ctr.py               # Deep CTR training
├── grpc_server.py             # gRPC ranking service
├── evaluate.py                # Model evaluation
├── docker-compose.yml         # Multi-container orchestration
├── Dockerfile                 # Original gRPC server container
└── README.md
```

## 🔧 Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Node.js 18+
- Java 8+ (for Spark preprocessing only)

### Option 1: Docker Compose (Recommended)

```bash
# 1. Build and start all services
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - gRPC Server: localhost:50051
# - PostgreSQL: localhost:5432
# - API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
pip install pydantic-settings

# Run FastAPI server
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
# App will be at http://localhost:5173
```

#### gRPC Server (separate terminal)
```bash
# From root directory
python grpc_server.py
```

#### PostgreSQL (if using locally)
```bash
# Using Docker just for DB
docker run -d \
  --name feedranker-db \
  -e POSTGRES_USER=feedranker \
  -e POSTGRES_PASSWORD=feedranker \
  -e POSTGRES_DB=feedranker \
  -p 5432:5432 \
  postgres:15-alpine
```

## 📊 API Endpoints

### Ranking
- **POST** `/rank` - Rank items using ensemble models
  ```json
  {
    "user_id": "user_123",
    "item_ids": ["item_1", "item_2", "item_3"],
    "context_features": {
      "impressions": 10,
      "hour_of_day": 12
    }
  }
  ```

### Monitoring
- **GET** `/health` - Health check
- **GET** `/status` - Model and service status
- **GET** `/metrics/latency?limit=100` - Recent latency metrics
- **GET** `/metrics/summary` - Summary statistics

### Documentation
- **GET** `/docs` - Swagger API documentation
- **GET** `/redoc` - ReDoc API documentation

## 🎨 Frontend Features

### Home Page
- Project overview
- Feature descriptions
- Quick navigation

### Ranking Interface
- Input user ID and item IDs
- Configure context features (impressions, hour of day)
- View ranked results with scores
- Display inference latency

### Dashboard
- Real-time metrics
- Latency trend chart
- Performance statistics (min, avg, max)
- Auto-refreshing every 10 seconds

## 🗄️ Database Schema

### Tables
- **ranking_metrics** - Track request latency and volume
- **ranking_requests** - Audit trail of all ranking requests
- **model_metadata** - Model versions and performance
- **user_feedback** - User feedback on ranking quality

## 🔄 Data Flow

```
1. Frontend (React UI)
        ↓
2. FastAPI Backend (/rank endpoint)
        ↓
3. gRPC Client (async)
        ↓
4. gRPC Server (port 50051)
        ├─ Load LambdaMART model
        ├─ Load Deep CTR model
        └─ Score & ensemble
        ↓
5. Return ranked items
        ↓
6. Store metrics in PostgreSQL
        ↓
7. Display in Dashboard
```

## 🚢 Production Deployment

### Environment Variables
```bash
# Backend
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
GRPC_HOST=grpc-server:50051
DATABASE_URL=postgresql://user:pass@host:5432/db
CORS_ORIGINS=https://yourdomain.com

# Frontend
VITE_API_URL=https://api.yourdomain.com
```

### Docker Compose Production
```bash
# Build images
docker-compose build

# Run services
docker-compose up -d

# Check logs
docker-compose logs -f backend frontend
```

### Kubernetes Deployment
Models and Helm charts available in `k8s/` directory (create as needed)

## 📈 Monitoring

### Metrics Available
- Total ranking requests
- Average/min/max latency
- Error rates
- Model availability

### Integrate with Prometheus
Backend exposes Prometheus metrics at `/metrics`

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'feedranker'
    static_configs:
      - targets: ['localhost:8000']
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🔐 Security Considerations

1. **Authentication**: Add JWT tokens to `/rank` endpoint
   - Update `main.py` with `Depends(verify_token)`

2. **Rate Limiting**: Protect API from abuse
   - Use `slowapi` library

3. **HTTPS**: Deploy behind reverse proxy (Nginx, Traefik)

4. **Database**: Use strong passwords, enable SSL connections

## 🐛 Troubleshooting

### Backend Won't Connect to gRPC
```bash
# Check if gRPC server is running
docker-compose logs grpc-server

# Verify port 50051 is open
netstat -an | grep 50051
```

### Frontend Can't Reach API
```bash
# Check CORS settings in main.py
# Verify VITE_API_URL in frontend/.env.local
# Check Docker network: docker network inspect feedranker-network
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check credentials in config.py
# Verify DATABASE_URL matches docker-compose settings
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [gRPC Python Guide](https://grpc.io/docs/languages/python/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Zustand State Management](https://github.com/pmndrs/zustand)

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test
3. Submit PR with description

## 📄 License

MIT License - see LICENSE file
