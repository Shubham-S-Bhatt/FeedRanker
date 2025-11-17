# 🚀 Quick Reference Guide

## Commands

### Docker Compose
```bash
# Start all services
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service]

# Services: postgres, grpc-server, backend, frontend

# Rebuild specific service
docker-compose build [service]
```

### Local Development
```bash
# Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev

# gRPC Server
python grpc_server.py

# Training Pipeline
spark-submit --master local[*] data_preprocessing.py input output
python train_lambdamart.py output/features.parquet models/lambdamart.txt
python train_ctr.py output/features.parquet models/deepctr_model
```

### Environment Setup
```bash
# Windows
setup-dev.bat

# macOS/Linux
bash setup-dev.sh
```

---

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Database | localhost:5432 |
| gRPC | localhost:50051 |

---

## Environment Variables

### Backend (.env)
```bash
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
GRPC_HOST=localhost:50051
DATABASE_URL=postgresql://feedranker:feedranker@localhost:5432/feedranker
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend (.env.local)
```bash
VITE_API_URL=http://localhost:8000
```

---

## Key Directories

```
backend/          → FastAPI application
frontend/         → React web UI
models/           → Trained ML models
protos/           → Protocol Buffer definitions
```

---

## Database

### Connection
```
Host: localhost
Port: 5432
Username: feedranker
Password: feedranker
Database: feedranker
```

### Tables
- `ranking_metrics` - Request metrics
- `ranking_requests` - Audit logs
- `model_metadata` - Model info
- `user_feedback` - Feedback data

---

## API Endpoints

### POST /rank
```json
Request:
{
  "user_id": "user_123",
  "item_ids": ["item_1", "item_2"],
  "context_features": {
    "impressions": 10,
    "hour_of_day": 14
  }
}

Response:
{
  "ranked_items": [
    {"item_id": "item_1", "score": 0.85},
    {"item_id": "item_2", "score": 0.72}
  ],
  "latency_ms": 45.2,
  "timestamp": "2025-11-16T10:30:00Z"
}
```

### GET /status
```json
{
  "lambdamart_loaded": true,
  "ctr_loaded": true,
  "gRPC_connected": true,
  "last_request_at": "2025-11-16T10:30:00Z",
  "total_requests": 1234,
  "avg_latency_ms": 48.5
}
```

### GET /metrics/summary
```json
{
  "total_requests": 1234,
  "avg_latency_ms": 48.5,
  "min_latency_ms": 35.2,
  "max_latency_ms": 125.8,
  "timestamp": "2025-11-16T10:30:00Z"
}
```

---

## Troubleshooting

### Issue: Frontend can't reach API
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check CORS in backend/main.py
# Verify VITE_API_URL in frontend/.env.local
```

### Issue: gRPC connection failed
```bash
# Check if gRPC server is running
docker-compose logs grpc-server

# Verify GRPC_HOST in backend/.env
```

### Issue: Database connection error
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Verify DATABASE_URL
psql $DATABASE_URL -c "SELECT 1"
```

### Issue: Docker build fails
```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up
```

---

## Files to Modify

### Adding a New API Endpoint
```python
# backend/main.py
@app.get("/my-endpoint")
async def my_endpoint(db: Session = Depends(get_db)):
    """New endpoint."""
    return {"result": "data"}
```

### Adding a React Component
```typescript
// frontend/src/components/MyComponent.tsx
import React from 'react';

export const MyComponent: React.FC = () => {
  return <div>Hello!</div>;
};

// frontend/src/App.tsx - Add to navigation
import { MyComponent } from './components/MyComponent';
```

### Changing Ensemble Weights
```python
# grpc_server.py - Line ~70
scores = 0.6*score_lm + 0.4*score_ctr  # Changed from 0.5/0.5

# backend/config.py - Or use env vars
ENSEMBLE_WEIGHT_LM=0.6
ENSEMBLE_WEIGHT_CTR=0.4
```

---

## Performance Tips

### Optimize Latency
1. Ensure models are pre-loaded in gRPC
2. Use async/await for non-blocking calls
3. Enable database connection pooling
4. Add Redis cache for frequent queries

### Improve Throughput
1. Increase gRPC thread pool size
2. Scale FastAPI replicas
3. Add load balancer (Nginx)
4. Batch ranking requests

### Monitor Performance
1. Use dashboard metrics
2. Check API Swagger /docs
3. View Docker logs
4. Monitor database queries

---

## Security Tips

### For Production
1. ✅ Enable HTTPS/TLS
2. ✅ Add authentication (JWT)
3. ✅ Set up rate limiting
4. ✅ Use secrets manager
5. ✅ Enable database encryption
6. ✅ Add WAF (Web Application Firewall)
7. ✅ Set strong CORS origins
8. ✅ Enable audit logging

---

## Deployment Checklist

- [ ] Set DEBUG=false
- [ ] Configure CORS_ORIGINS
- [ ] Set strong database password
- [ ] Enable HTTPS
- [ ] Add authentication
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Add rate limiting
- [ ] Document API
- [ ] Test all endpoints
- [ ] Load test
- [ ] Security audit

---

## Useful Commands

```bash
# Backend
python -m pytest                          # Run tests
python -m pylint backend/main.py          # Lint code
uvicorn main:app --reload --port 8000     # Dev server

# Frontend
npm run lint                  # Lint code
npm run type-check           # Type check
npm run build                # Production build
npm test                     # Run tests

# Docker
docker-compose ps            # Check services
docker-compose restart       # Restart all
docker exec -it feedranker-db psql -U feedranker -d feedranker  # DB shell
docker logs -f [container]   # Follow logs

# Database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM ranking_metrics"
psql $DATABASE_URL -c "\dt"  # List tables
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Port already in use | Change port in docker-compose.yml or kill process |
| Module not found | Run pip install -r requirements.txt |
| Database won't start | Check password, reset with docker volume rm |
| gRPC connection refused | Ensure gRPC server is running, check port 50051 |
| CORS error | Update CORS_ORIGINS in backend/.env |
| Frontend blank page | Check browser console, verify VITE_API_URL |

---

## Next Reading

- 📖 [WEB_APP_SETUP.md](WEB_APP_SETUP.md) - Detailed setup
- 📖 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What was built
- 📖 [.github/copilot-instructions.md](.github/copilot-instructions.md) - Architecture guide
- 📖 [README.md](README.md) - Project overview

---

**Happy ranking! 🎯**
