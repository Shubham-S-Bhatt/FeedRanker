<!-- ─────────────── BADGE BAR ─────────────── -->
<p align="center">

  <!-- Build & Test -->
  <a href="https://github.com/Shubham-S-Bhatt/FeedRanker/actions">
    <img alt="Build" src="https://img.shields.io/github/actions/workflow/status/Shubham-S-Bhatt/FeedRanker/ci.yml?logo=github">
  </a>

  <!-- Latest Release -->
  <a href="https://github.com/Shubham-S-Bhatt/FeedRanker/releases">
    <img alt="Latest Release" src="https://img.shields.io/github/v/release/Shubham-S-Bhatt/FeedRanker?include_prereleases&logo=github">
  </a>

  <!-- License -->
  <a href="LICENSE">
    <img alt="MIT License" src="https://img.shields.io/badge/License-MIT-blue.svg">
  </a>

  <!-- Stars -->
  <a href="https://github.com/Shubham-S-Bhatt/FeedRanker/stargazers">
    <img alt="GitHub Stars" src="https://img.shields.io/github/stars/Shubham-S-Bhatt/FeedRanker?style=social">
  </a>

</p>
<!-- ───────────────────────────────────────── -->

# 🎯 FeedRanker

**Scalable feed-ranking system** combining **LambdaMART** and **Deep CTR** models with a modern full-stack web application. Designed for **<60ms latency at 20K+ QPS** on 100M+ log datasets.

> **Now with a production-ready web UI!** Deploy instantly with Docker Compose. Real-time dashboards, REST API, PostgreSQL analytics.

---

## ✨ Features

### 🤖 ML System
- **LambdaMART** (LightGBM): Learning-to-rank optimizing NDCG@5/10
- **Deep CTR** (TensorFlow): Binary classification for CTR prediction
- **Ensemble**: 50/50 weighted combination for superior ranking
- **PySpark ETL**: Scalable feature engineering on 100M+ logs

### 🌐 Web Application
- **React Frontend**: Modern TypeScript UI with Tailwind CSS
- **FastAPI Backend**: REST API with async gRPC integration
- **PostgreSQL**: Metrics tracking, audit logs, performance analytics
- **Dashboard**: Real-time monitoring, latency trends, model status
- **Docker Compose**: One-command deployment for all services

### 📊 Production Ready
- Swagger API documentation (`/docs`)
- Health checks and service monitoring
- Request metrics and performance analytics
- CORS support for multi-origin deployments
- Environment-based configuration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  React Frontend (TypeScript + Tailwind)             │
│  • Ranking Interface • Dashboard • Monitoring       │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────────────────┐
│  FastAPI Backend (Python)                           │
│  • /rank endpoint • /health • /metrics/*            │
│  • CORS • Validation • Background tasks            │
└─────────────────┬───────────────────────────────────┘
                  │ gRPC (async)
┌─────────────────▼───────────────────────────────────┐
│  gRPC Ranking Server                                │
│  ├─ LambdaMART Model (.txt)                        │
│  ├─ Deep CTR Model (TensorFlow SavedModel)         │
│  └─ Ensemble Scoring (50/50)                       │
└─────────────────┬───────────────────────────────────┘
                  │ Metrics
┌─────────────────▼───────────────────────────────────┐
│  PostgreSQL Database                                │
│  • ranking_metrics • ranking_requests              │
│  • model_metadata • user_feedback                  │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (easiest)
- Python 3.9+, Node.js 18+, Java 8+ (for local development)

### Option 1: Docker Compose (Recommended)
```bash
# Clone and start all services
git clone https://github.com/Shubham-S-Bhatt/FeedRanker
cd FeedRanker
docker-compose up --build

# Services ready at:
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
# gRPC: localhost:50051
# Database: localhost:5432
```

### Option 2: Local Development
```bash
# Setup (Windows or macOS/Linux)
./setup-dev.bat    # Windows
bash setup-dev.sh  # macOS/Linux

# Terminal 1 - Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend && npm run dev

# Terminal 3 - gRPC Server
python grpc_server.py

# Terminal 4 - Database
docker run -d -e POSTGRES_USER=feedranker -e POSTGRES_PASSWORD=feedranker -p 5432:5432 postgres:15-alpine
```

---

## 📚 API Endpoints

### Ranking
```bash
POST /rank
{
  "user_id": "user_123",
  "item_ids": ["item_1", "item_2", "item_3"],
  "context_features": {
    "impressions": 10,
    "hour_of_day": 14
  }
}
```

### Monitoring
- `GET /health` - Service health
- `GET /status` - Model and service status
- `GET /metrics/latency` - Request latencies
- `GET /metrics/summary` - Statistics
- `GET /docs` - Interactive Swagger UI

---

## 🎨 Web Interface

### Home Page
- Project overview
- Feature descriptions
- Quick navigation

### Ranking Interface
- Input user ID and items
- Configure context features
- View ranked results with scores
- Display inference latency

### Dashboard
- Total requests counter
- Average/min/max latency
- Latency trend chart
- Auto-refreshing metrics

---

## 🔄 ML Training Pipeline

```bash
# 1. Preprocess features (PySpark)
spark-submit --master local[*] \
  data_preprocessing.py \
  path/to/behaviors.tsv path/to/news.tsv \
  output/features.parquet

# 2. Train models
python train_lambdamart.py output/features.parquet models/lambdamart.txt
python train_ctr.py output/features.parquet models/deepctr_model

# 3. Evaluate
python evaluate.py models/lambdamart.txt output/features.parquet models/deepctr_model

# 4. Deploy with Docker
docker-compose up --build
```

---

## 📊 Database Schema

| Table | Purpose |
|-------|---------|
| `ranking_metrics` | Request latency and throughput |
| `ranking_requests` | Audit trail of all requests |
| `model_metadata` | Model versions and performance |
| `user_feedback` | User feedback on ranking quality |

---

## 🔐 Environment Configuration

Create `backend/.env`:
```bash
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
GRPC_HOST=grpc-server:50051
DATABASE_URL=postgresql://feedranker:feedranker@postgres:5432/feedranker
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## 🚢 Production Deployment

### Using Docker Compose (Recommended)
```bash
docker-compose -f docker-compose.yml up -d
```

All services will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000/docs
- gRPC: localhost:50051
- Database: localhost:5432

---

## 📖 Documentation

- **[Web App Setup Guide](WEB_APP_SETUP.md)** - Detailed deployment instructions

---

## 🔍 Key Files

```
FeedRanker/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── database.py          # ORM models
│   ├── config.py            # Configuration
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main app
│   │   ├── components/      # React components
│   │   ├── services/api.ts  # HTTP client
│   │   └── store.ts         # State management
│   └── Dockerfile
├── data_preprocessing.py    # PySpark ETL
├── train_lambdamart.py     # LambdaMART training
├── train_ctr.py            # CTR training
├── grpc_server.py          # gRPC service
├── evaluate.py             # Evaluation script
├── docker-compose.yml      # Multi-container setup
└── setup-dev.sh/.bat       # Development setup
```

---

## 🐛 Troubleshooting

### Frontend can't reach API
```bash
# Check CORS in backend/main.py
# Verify VITE_API_URL in frontend/.env.local
# Check container network: docker network inspect feedranker-network
```

### gRPC connection failed
```bash
# Check if gRPC server is running
docker-compose logs grpc-server
# Verify port 50051: netstat -an | grep 50051
```

### Database connection error
```bash
# Check PostgreSQL is running
docker-compose ps postgres
# Verify DATABASE_URL in config.py
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and test
4. Submit PR with description

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 👤 Author

**Shubham Bhatt**
- Email: shubhamsatyaprakashbhatt@gmail.com
- GitHub: [@Shubham-S-Bhatt](https://github.com/Shubham-S-Bhatt)

---

## 📬 Citation

```bibtex
@software{feedranker2025,
  title    = {FeedRanker: Scalable Feed Ranking with ML},
  author   = {Bhatt, Shubham},
  year     = {2025},
  url      = {https://github.com/Shubham-S-Bhatt/FeedRanker}
}
```

---

<p align="center">
  <strong>⭐ Star this repo if you found it helpful!</strong>
</p>
