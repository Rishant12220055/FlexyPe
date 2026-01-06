# 🚀 Quick Start Guide

## Prerequisites

- **Docker Desktop** installed and running
- **Python 3.11+**
- **Node.js 18+**
- **Git** (optional)

---

## 🎯 Option 1: Docker Compose (Recommended)

### 1. Start All Services

```bash
# From project root
docker-compose up --build
```

This will start:
- ✅ Redis (port 6379)
- ✅ PostgreSQL (port 5432)
- ✅ Backend API (port 8000)
- ✅ Expiry Worker
- ✅ Frontend (port 3000)

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

### 3. Test the System

1. Login with any user ID (e.g., `user_1`)
2. Click "Initialize Inventory" to set up 100 units
3. Reserve items with the form
4. Watch the countdown timer
5. Confirm purchase before expiry

---

## 🛠️ Option 2: Manual Setup (Development)

### Step 1: Start Infrastructure

```bash
# Start Redis and PostgreSQL
docker-compose up -d redis postgres

# Wait for services to be healthy (about 10 seconds)
```

### Step 2: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Initialize database
python scripts/init_db.py

# Start backend server
uvicorn main:app --reload
```

Backend will run on http://localhost:8000

### Step 3: Start Expiry Worker

```bash
# In a NEW terminal
cd backend
venv\Scripts\activate  # Activate venv
python -m app.workers.expiry_worker
```

### Step 4: Setup Frontend

```bash
# In a NEW terminal
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env

# Start development server
npm run dev
```

Frontend will run on http://localhost:3000

---

## 🧪 Running Tests

### Concurrency Tests (Critical)

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run only concurrency tests
pytest tests/test_concurrency.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Load Testing

```bash
# Using Apache Bench (requires installation)
cd backend

# Get test token
set TEST_TOKEN=$(python scripts/get_test_token.py test_user)

# Run load test
ab -n 100 -c 100 -p tests/reserve.json ^
   -H "Authorization: Bearer %TEST_TOKEN%" ^
   http://localhost:8000/api/v1/inventory/reserve
```

---

## 📋 Quick Demo Script

### 1. Initialize Inventory

```bash
curl -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\": \"demo_user\"}"

# Save the token from response

curl -X POST "http://localhost:8000/api/v1/inventory/FLASH-SALE-001/initialize?quantity=100" ^
  -H "Authorization: Bearer <your_token>"
```

### 2. Reserve Inventory

```bash
curl -X POST http://localhost:8000/api/v1/inventory/reserve ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer <your_token>" ^
  -d "{\"sku\": \"FLASH-SALE-001\", \"quantity\": 2}"

# Save the reservation_id from response
```

### 3. Confirm Checkout

```bash
curl -X POST http://localhost:8000/api/v1/checkout/confirm ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer <your_token>" ^
  -d "{\"reservation_id\": \"<your_reservation_id>\"}"
```

---

## 🎮 Testing Scenarios

### Scenario 1: Race Condition Test

1. Login with multiple users in different browsers (use Incognito)
2. Initialize inventory with only 1 unit
3. Click "Reserve" on all browsers simultaneously
4. ✅ **Expected**: Only ONE succeeds, others get "Insufficient inventory"

### Scenario 2: Expiry Test

1. Reserve an item
2. Wait for countdown to reach 0 (5 minutes)
3. Try to confirm checkout
4. ✅ **Expected**: "Reservation expired" error
5. ✅ **Expected**: Inventory is restored

### Scenario 3: Idempotency Test

1. Reserve an item
2. Open Network tab in browser DevTools
3. Right-click the reserve API call → "Replay XHR"
4. ✅ **Expected**: Same reservation_id returned, inventory only decremented once

---

## 🐛 Troubleshooting

### Redis Connection Failed

```bash
# Check if Redis is running
docker ps | findstr redis

# Restart Redis
docker-compose restart redis
```

### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is running
docker ps | findstr postgres

# View logs
docker-compose logs postgres
```

### Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Frontend Can't Connect to Backend

1. Check VITE_API_BASE_URL in `frontend/.env`
2. Ensure backend is running on port 8000
3. Check browser console for CORS errors

---

## 📊 Monitoring

### View Redis Data

```bash
# Connect to Redis CLI
docker exec -it flexype-redis redis-cli

# View all keys
KEYS *

# Get inventory for SKU
GET inventory:FLASH-SALE-001

# View expiring reservations
ZRANGE expiring_reservations 0 -1 WITHSCORES

# Exit
exit
```

### View PostgreSQL Data

```bash
# Connect to PostgreSQL
docker exec -it flexype-postgres psql -U flexype -d inventory_system

# View orders
SELECT * FROM orders;

# View audit log
SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;

# Exit
\q
```

---

## 🎯 Success Criteria Checklist

After setup, verify:

- [ ] Backend API docs accessible at http://localhost:8000/api/docs
- [ ] Frontend loads at http://localhost:3000
- [ ] Can login with any user ID
- [ ] Can initialize inventory
- [ ] Can reserve items
- [ ] Countdown timer displays and counts down
- [ ] Can confirm checkout
- [ ] Expired reservations restore inventory
- [ ] Concurrency tests pass (`pytest tests/test_concurrency.py`)
- [ ] Multiple users can't reserve same last item

---

## 🚦 Next Steps

1. ✅ **Test Locally**: Follow Quick Demo Script
2. ✅ **Run Tests**: Verify concurrency behavior
3. ✅ **Load Test**: Validate performance under load
4. 📝 **Document Findings**: Note any issues for presentation
5. 🎤 **Prepare Demo**: Practice the demo flow

---

## 📞 Support

If you encounter issues:

1. Check the backend logs: `docker-compose logs backend`
2. Check the worker logs: `docker-compose logs expiry-worker`
3. View Redis data: `docker exec -it flexype-redis redis-cli`
4. Restart services: `docker-compose restart`

---

**Built with ❤️ for FlexyPe Hackathon 2026**
