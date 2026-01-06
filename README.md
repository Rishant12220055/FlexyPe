# Smart Inventory Reservation System

## FlexyPe Hackathon - Flash Sale Concurrency Solution

### Problem Statement
Handle 100+ concurrent users racing to buy the same last item without overselling, payment failures, or database deadlocks.

### Key Features
✅ **Atomic Inventory Management** - Lua scripts ensure inventory never goes negative  
✅ **Auto-Expiring Reservations** - 5-minute TTL with background cleanup  
✅ **Idempotent Operations** - Duplicate requests return same result  
✅ **Rate Limiting** - 10 requests/minute per user  
✅ **Audit Logging** - PostgreSQL for order history and compliance  

### Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Cache/Inventory**: Redis 7.x with AOF persistence
- **Database**: PostgreSQL 15
- **Auth**: JWT tokens
- **Frontend**: React 18 with TypeScript
- **Containerization**: Docker Compose

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Start Services
```bash
# Start Redis + PostgreSQL
docker-compose up -d

# Initialize database
cd backend
python scripts/init_db.py

# Start backend
uvicorn main:app --reload

# Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### 2. Test the System
```bash
# Run concurrency tests
cd backend
pytest tests/test_concurrency.py -v

# Load test (requires Apache Bench)
ab -n 100 -c 100 -p tests/reserve.json \
   -H "Authorization: Bearer $(python scripts/get_test_token.py)" \
   http://localhost:8000/api/v1/inventory/reserve
```

---

## API Documentation

### Reserve Inventory
```http
POST /api/v1/inventory/reserve
Authorization: Bearer <jwt_token>
X-Idempotency-Key: <uuid>

{
  "sku": "FLASH-SALE-001",
  "quantity": 2
}
```

**Success Response (201)**
```json
{
  "reservation_id": "rsv_1a2b3c4d5e6f",
  "sku": "FLASH-SALE-001",
  "quantity": 2,
  "expires_at": "2026-01-06T10:45:00Z",
  "ttl_seconds": 300
}
```

**Error Responses**
- `409 Conflict` - Insufficient inventory
- `429 Too Many Requests` - Rate limit exceeded
- `400 Bad Request` - Invalid input

### Confirm Checkout
```http
POST /api/v1/checkout/confirm
Authorization: Bearer <jwt_token>

{
  "reservation_id": "rsv_1a2b3c4d5e6f"
}
```

### Get Inventory Status
```http
GET /api/v1/inventory/{sku}
```

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client    │────▶│  FastAPI     │────▶│    Redis     │
│  (React)    │     │   Backend    │     │ (Inventory)  │
└─────────────┘     └──────────────┘     └──────────────┘
                           │                      │
                           │                      ▼
                           │              ┌──────────────┐
                           │              │  Background  │
                           │              │  Job (Expiry)│
                           ▼              └──────────────┘
                    ┌──────────────┐
                    │ PostgreSQL   │
                    │(Audit Logs)  │
                    └──────────────┘
```

### Concurrency Strategy
1. **Atomic Operations**: Redis Lua scripts for check-and-decrement
2. **Optimistic Locking**: WATCH/MULTI/EXEC for checkout confirmation
3. **TTL-based Expiry**: Automatic reservation cleanup
4. **Idempotency Keys**: Prevent double-reservations on network retries

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit/ -v --cov=app
```

### Concurrency Tests (Critical)
```bash
# Verify 100 users racing for 1 item results in exactly 1 success
pytest tests/test_concurrency.py::test_last_item_race -v
```

### Load Tests
```bash
# Target: 500 req/s with p95 < 200ms
locust -f tests/locustfile.py --host=http://localhost:8000
```

---

## Monitoring

### Key Metrics (Prometheus)
- `reserve_requests_total{status}` - Success/failure rates
- `reserve_duration_seconds` - API latency histogram
- `active_reservations_count` - Current reservations
- `inventory_available{sku}` - Real-time stock levels

### Critical Alerts
- **Inventory Negative**: Immediate alert if count < 0
- **High Failure Rate**: Alert if >50% requests fail
- **Slow API**: Alert if p95 > 500ms

---

## Security Measures
- ✅ JWT authentication with 15-minute expiry
- ✅ Rate limiting (10 req/min per user, 100 req/min per IP)
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (parameterized queries)
- ✅ Reservation ownership validation
- ✅ Audit logging for compliance

---

## Project Structure
```
flexype-hackathon/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── inventory.py
│   │   │   │   ├── checkout.py
│   │   │   │   └── auth.py
│   │   │   └── middleware/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── redis_client.py
│   │   │   └── database.py
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── inventory_service.py
│   │   │   └── reservation_service.py
│   │   └── workers/
│   │       └── expiry_worker.py
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Future Enhancements (Post-Hackathon)
- [ ] Waitlist for sold-out items
- [ ] Multi-region inventory with eventual consistency
- [ ] GraphQL API
- [ ] WebSocket for real-time inventory updates
- [ ] Advanced analytics dashboard

---

## License
MIT License - FlexyPe Hackathon 2026

## Contributors
Built with ❤️ for the FlexyPe Hackathon
