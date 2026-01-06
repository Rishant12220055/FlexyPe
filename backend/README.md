# Smart Inventory Reservation System - Backend

## Setup

### 1. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup environment variables
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Start services (Redis + PostgreSQL)
```bash
# From project root
docker-compose up -d redis postgres
```

### 5. Initialize database
```bash
python scripts/init_db.py
```

### 6. Run backend
```bash
uvicorn main:app --reload
```

### 7. Run expiry worker (in separate terminal)
```bash
python -m app.workers.expiry_worker
```

## Testing

### Run all tests
```bash
pytest tests/ -v
```

### Run concurrency tests
```bash
pytest tests/test_concurrency.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── middleware/    # Rate limiting, etc.
│   │   └── routes/        # API endpoints
│   ├── core/              # Config, database, Redis
│   ├── models/            # Pydantic schemas
│   ├── services/          # Business logic
│   └── workers/           # Background jobs
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── main.py               # FastAPI app
└── requirements.txt      # Dependencies
```
