<!-- ─────────────── BADGE BAR ─────────────── -->
<p align="center">

  <!-- Build & Test -->
  <a href="https://github.com/ORG_NAME/REPO_NAME/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/ORG_NAME/REPO_NAME/actions/workflows/ci.yml/badge.svg">
  </a>

  <!-- Code Coverage -->
  <a href="https://codecov.io/gh/ORG_NAME/REPO_NAME">
    <img alt="Coverage" src="https://img.shields.io/codecov/c/github/ORG_NAME/REPO_NAME?logo=codecov">
  </a>

  <!-- Latest Release -->
  <a href="https://github.com/ORG_NAME/REPO_NAME/releases">
    <img alt="Latest Release" src="https://img.shields.io/github/v/release/ORG_NAME/REPO_NAME?include_prereleases&logo=github">
  </a>

  <!-- Docker Pulls -->
  <a href="https://hub.docker.com/r/DOCKER_USER/IMAGE_NAME">
    <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/DOCKER_USER/IMAGE_NAME?logo=docker">
  </a>

  <!-- Stars -->
  <a href="https://github.com/ORG_NAME/REPO_NAME/stargazers">
    <img alt="GitHub Stars" src="https://img.shields.io/github/stars/ORG_NAME/REPO_NAME?style=social">
  </a>

  <!-- Issues -->
  <a href="https://github.com/ORG_NAME/REPO_NAME/issues">
    <img alt="Open Issues" src="https://img.shields.io/github/issues/ORG_NAME/REPO_NAME">
  </a>

  <!-- License -->
  <a href="LICENSE">
    <img alt="MIT License" src="https://img.shields.io/badge/License-MIT-blue.svg">
  </a>

</p>
<!-- ───────────────────────────────────────── -->





# FeedRanker

Scalable feed-ranking system combining LightGBM LambdaMART and a TensorFlow deep CTR model, built with PySpark for feature engineering and served via gRPC. Designed for sub-60 ms latency at 20K+ QPS on 100M+ log datasets.

---

## 🔍 Features

- **Data Preprocessing**  
  • PySpark transforms raw event logs into feature parquet files  
  • Session- and user-level aggregations, time-based features, CTR labels  

- **LambdaMART Ranker**  
  • LightGBM implementation with ranking objective  
  • NDCG@5/10 evaluation, early stopping, hyperparameter tuning  

- **Deep CTR Model**  
  • TensorFlow MLP with binary-classification proxy for CTR  
  • AUC monitoring, checkpointing, scalable GPU/CPU training  

- **gRPC Serving Layer**  
  • Protocol Buffers definition for requests & responses  
  • Combines both model scores, weighted ensemble  
  • Dockerized, production-ready with auto-generated stubs  

---

## 🏗️ Architecture

```plaintext
┌────────────────────┐
│  Event Logs (JSON) │
└────────┬───────────┘
         │
         ▼
┌───────────────────────┐
│ data_preprocessing.py │
└────────┬──────────────┘
         │ Parquet
         ▼
┌────────┴────────────┐        ┌────────────────┐
│ train_lambdamart.py | ────▶ │ LightGBM Model │
└────────┬────────────┘        └────────────────┘
         │
         │
         │        ┌────────────────┐
         ▼        │ TensorFlow CTR │
┌────────┴─────┐  │     Model      │
│ train_ctr.py |  └────────────────┘
└────────┬─────┘
         │
         ▼
┌──────────────────┐
│   evaluate.py    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  grpc_server.py  │
└──────────────────┘
         │
         ▼
┌───────────────────┐
│  Docker Container │
└───────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**, **Java 8+** (for Spark)  
- **Apache Spark 3.x**  
- **Docker 20.x** (optional)  
- **Git**

---

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/feedranker.git
cd feedranker
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 2. Data Preprocessing

```bash
spark-submit   --master local[*]   data_preprocessing.py   path/to/raw_logs.json   path/to/features.parquet
```

---

### 3. Model Training

#### LambdaMART

```bash
python train_lambdamart.py   path/to/features.parquet   models/lambdamart.txt
```

#### Deep CTR

```bash
python train_ctr.py   path/to/features.parquet   models/deepctr_model
```

---

### 4. Evaluation

```bash
python evaluate.py   models/lambdamart.txt   path/to/features.parquet   models/deepctr_model
```

---

### 5. Serving via gRPC

#### Local

```bash
# Generate Python stubs (only once or after .proto changes)
python -m grpc_tools.protoc   -I protos   --python_out=.   --grpc_python_out=.   protos/feed_ranker.proto

# Start server
python grpc_server.py
```

#### Docker

```bash
docker build -t feedranker:latest .
docker run --rm -p 50051:50051 feedranker:latest
```

---

## ⚙️ Configuration

All hyperparameters and file paths can be customized at the top of each script. Recommended defaults live in:

- `train_lambdamart.py`  
- `train_ctr.py`  
- `grpc_server.py`  

---

## 🤝 Contributing

We welcome your contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Issue reporting  
- Branching & PR guidelines  
- Code style & testing  

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 📬 Contact & Citation

- **Author:** Shubham Bhatt  
- **Email:** shubhamsatyaprakashbhatt@gmail.com  
- **Citation:**  
  ```bibtex
  @misc{feedranker2025,
    title    = {FeedRanker: Scalable Feed Ranking using LambdaMART and Deep CTR Models},
    author   = {Bhatt, Shubham},
    year     = {2025},
    url      = {https://github.com/your-org/feedranker}
  }
  ```
