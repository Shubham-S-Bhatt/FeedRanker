# FeedRanker: AI Coding Agent Guide

## Project Overview

**FeedRanker** is a scalable feed ranking system with a **full-stack web application**:

### Core ML System
- **LambdaMART** (LightGBM): Learns-to-rank model optimizing NDCG@5/10
- **Deep CTR** (TensorFlow): Binary classification for CTR prediction
- Both models scored independently, then 50/50 weighted ensemble for final ranking
- Target: **<60ms latency at 20K+ QPS**

### Web Application
- **FastAPI Backend**: REST API wrapper around gRPC service with PostgreSQL database
- **React Frontend**: Modern TypeScript UI with Tailwind CSS, Zustand state management, Recharts visualization
- **gRPC Service**: Async ranking engine on port 50051
- **PostgreSQL**: Metrics tracking, audit logs, model versioning
- **Docker Compose**: Multi-container orchestration for all services

## Critical Architecture

### Full-Stack Data Flow
```
Frontend (React)
     ↓
FastAPI Backend (/rank endpoint, async)
     ↓
gRPC Client (async channel to :50051)
     ↓
gRPC Ensemble Server
  ├─ LambdaMART (.txt model)
  └─ Deep CTR (SavedModel)
     ↓
Scored items + metadata → PostgreSQL (metrics, audit)
     ↓
Dashboard Visualization
```

### ML Training Pipeline
```
Raw Event Logs → PySpark Preprocessing → Feature Parquet
                                             ↓
                                    ┌────────┴────────┐
                                    ↓                 ↓
                           LambdaMART Training    CTR Training
                                    ↓                 ↓
                                    └────────┬────────┘
                                             ↓
                                      gRPC Ensemble Server
```

### Service Boundaries

#### ML Pipeline Components
- **`data_preprocessing.py`**: PySpark ETL—converts MIND-format (behaviors TSV + news TSV) into unified parquet features. Handles time parsing, impression explosion, per-user/news aggregation, metadata enrichment. **Tunable spark shuffle partitions** based on core count to prevent OOM.
- **`train_lambdamart.py`**: LightGBM ranker training. Input: parquet features. Objective: `lambdarank`. Groups by `(user_id + session_id)`. Output: `.txt` model file.
- **`train_ctr.py`**: TensorFlow MLP training. Binary classification on CTR > 0 proxy. Output: Keras SavedModel directory.
- **`evaluate.py`**: Offline metrics. Computes NDCG@10 for both models independently using test parquet.

#### Web Application Components
- **`backend/main.py`**: FastAPI application with REST endpoints:
  - `POST /rank` - Main ranking endpoint (async gRPC call)
  - `GET /health` - Health check
  - `GET /status` - Model status and metrics
  - `GET /metrics/*` - Latency and performance metrics
  - Auto-generated `/docs` (Swagger UI) and `/redoc`
  
- **`backend/database.py`**: SQLAlchemy ORM models (PostgreSQL):
  - `RankingMetric` - Performance metrics per request
  - `RankingRequest` - Audit trail of ranking requests
  - `ModelMetadata` - Model versions and performance
  - `UserFeedback` - Quality feedback loop
  
- **`grpc_server.py`**: gRPC ranking service (unchanged). Listens on port 50051. Both `/rank` (REST) and `grpc_server.py` can coexist.

- **`frontend/src/App.tsx`**: React main component with navigation (Home, Ranking, Dashboard)
- **`frontend/src/components/RankingInterface.tsx`**: Form for submitting ranking requests
- **`frontend/src/components/Dashboard.tsx`**: Real-time metrics and performance charts
- **`frontend/src/services/api.ts`**: Axios client for backend API
- **`frontend/src/store.ts`**: Zustand store for state management

### Model Integration Pattern
Both `grpc_server.py` and evaluation use identical feature extraction: `["impressions", "avg_hour"]` from context. This minimal feature set ensures fast inference. **Verify new features are added to all three locations**: data_preprocessing.py aggregation → train scripts → server/eval extraction.

## Developer Workflows

### Setup & First Run
```bash
# Windows
setup-dev.bat

# macOS/Linux
bash setup-dev.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pydantic-settings

cd backend && python -m grpc_tools.protoc -I ../protos --python_out=. --grpc_python_out=. ../protos/feed_ranker.proto
cd ../frontend && npm install
```

### Quick Start with Docker Compose
```bash
docker-compose up --build

# Services available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# gRPC: localhost:50051
# Database: localhost:5432
```

### Local Development (3 Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Opens http://localhost:5173
```

**Terminal 3 - gRPC Server:**
```bash
python grpc_server.py
# Listens on :50051
```

**Terminal 4 - PostgreSQL (optional, can use Docker):**
```bash
docker run -d \
  --name feedranker-db \
  -e POSTGRES_USER=feedranker \
  -e POSTGRES_PASSWORD=feedranker \
  -p 5432:5432 \
  postgres:15-alpine
```

### Training Workflow (Original, unchanged)
```bash
# 1. Preprocess with PySpark (requires Java 8+, $SPARK_HOME set)
spark-submit --master local[*] data_preprocessing.py path/to/behaviors.tsv path/to/news.tsv output/features.parquet

# 2. Train both models in parallel (optional, can be sequential)
python train_lambdamart.py output/features.parquet models/lambdamart.txt &
python train_ctr.py output/features.parquet models/deepctr_model &
wait

# 3. Evaluate
python evaluate.py models/lambdamart.txt output/features.parquet models/deepctr_model

# 4. Start gRPC server with models
python grpc_server.py
```

## Project-Specific Conventions

### Feature Engineering
- **Always extract features as numpy arrays in order**: `[impressions, avg_hour]`. Positional indexing—order matters for model alignment.
- **PySpark feature names in preprocessing**: `impressions`, `clicks`, `ctr`, `avg_hour`, `category_idx`, `title_len`, `abstract_len`. When adding features, update both aggregation logic in preprocessing and the subset selection in train/serve scripts.
- **Fill NaN values consistently**: Missing hours → 0.0, missing metadata → -1.0 or 0 per context.

### Model Configuration
- **LambdaMART** hyperparams in `train_lambdamart.py`: `num_leaves=31`, `min_data_in_leaf=20`, `ndcg_eval_at=[5, 10]`, early stopping at 50 rounds. These are tuned for 100M+ logs—adjust `num_leaves` if overfitting.
- **Deep CTR** architecture: 256→128→64→1 (sigmoid). Binary classification. If modifying layer sizes, re-run with same data to ensure ensemble calibration.
- **Ensemble weights**: Currently 50/50 (`0.5*score_lm + 0.5*score_ctr`). Adjust in `grpc_server.py` Rank method.

### gRPC Protocol
- `feed_ranker.proto` defines:
  - `RankRequest`: user_id (string), item_ids (repeated string), user_features & context_features (map<string, float>)
  - `RankResponse`: ranked_items (repeated RankedItem with item_id + score)
- Server listens on `[::]:50051` (IPv6 dual-stack). Items sorted by score descending before returning.

### PySpark Memory Tuning
`data_preprocessing.py` sets `spark.memory.fraction=0.6` and dynamically calculates shuffle partitions:
```python
shuffle_parts = max(spark.sparkContext.defaultParallelism * 4, 50)
```
**Critical**: All spark config values must be **strings** (`spark.conf.set("key", str(value))`). If OOM occurs, increase shuffle partitions or reduce memory.fraction.

## Common Patterns & Anti-Patterns

### ✅ DO:
- Keep train scripts CLI-driven with argparse (path inputs, model outputs). Enables easy automation.
- Use LightGBM `.txt` format for portability; TensorFlow SavedModel for versioning.
- Aggregate features at the impression level in preprocessing; never compute features on-the-fly during serving.
- Test model loading & inference latency locally before Docker build.

### ❌ DON'T:
- Hardcode file paths. Always use CLI args or config.
- Change feature order without updating ALL extraction locations (preprocessing, train, serve, eval).
- Train CTR model with raw CTR values; use binary proxy (CTR > 0) for stable gradients.
- Serve models without loading them at server init—loading during request = latency spike.

## Key Files Reference

| File | Purpose | Entry Point |
|------|---------|-------------|
| `data_preprocessing.py` | Feature extraction pipeline | CLI: behaviors TSV + news TSV → parquet |
| `train_lambdamart.py` | LambdaMART training | CLI: parquet → `.txt` model |
| `train_ctr.py` | Deep CTR training | CLI: parquet → SavedModel dir |
| `evaluate.py` | Offline NDCG evaluation | CLI: loads models + parquet → metrics |
| `grpc_server.py` | gRPC serving ensemble | Main: listens on :50051 |
| `protos/feed_ranker.proto` | Service contract | Compile with grpc_tools.protoc |
| `backend/main.py` | FastAPI REST wrapper | REST API wraps gRPC service |
| `backend/config.py` | Configuration management | Environment variables |
| `backend/database.py` | SQLAlchemy ORM models | PostgreSQL tables & queries |
| `frontend/src/App.tsx` | React main component | Navigation & routing |
| `frontend/src/components/RankingInterface.tsx` | Ranking form UI | User input & results |
| `frontend/src/components/Dashboard.tsx` | Metrics & charts | Real-time monitoring |
| `frontend/src/services/api.ts` | Axios HTTP client | API calls to backend |
| `frontend/src/store.ts` | Zustand state store | Global state management |
| `docker-compose.yml` | Multi-container config | `docker-compose up` |
| `Dockerfile` (root) | gRPC server container | Original model server |
| `backend/Dockerfile` | FastAPI container | REST API service |
| `frontend/Dockerfile` | React prod build | Web UI service |

## Testing & Debugging

- **Unit test patterns**: Not yet established; consider pytest with fixtures for feature extraction validation.
- **Debugging preprocessing**: Add `log.info()` statements (already in use). Monitor Spark UI on localhost:4040 during spark-submit.
- **Model inference checks**: Before serving, manually call `model.predict(X)` with known inputs to verify shapes and output ranges.
- **gRPC server issues**: Check proto compilation (`python -m grpc_tools.protoc`); verify ports not in use; enable gRPC debug logging with `export GRPC_VERBOSITY=debug`.

## Extensions & Future Work

- **Feature store integration**: Replace hardcoded feature names with a centralized registry.
- **A/B testing**: Serve multiple model versions; parameterize ensemble weights per experiment.
- **Model monitoring**: Add latency histograms, ensemble score distributions to gRPC responses.
- **Batch inference**: Extend gRPC service with batch ranking (multiple users in one RPC).
- **Authentication**: Add JWT/OAuth2 to `/rank` endpoint for multi-tenant deployments.
- **Rate limiting**: Protect API with slowapi for fair usage.
- **Model retraining**: Background jobs for periodic model updates with MLflow tracking.
- **Advanced visualization**: Add more charts (P99 latency, score distributions, A/B comparison).
- **Feedback loop**: Integrate user feedback into model improvement pipeline.
- **Kubernetes**: Helm charts for cloud-native deployments with auto-scaling.
