# Backend Setup Guide

## Prerequisites
- PostgreSQL running (locally or remote)
- Python 3.11+ with pip

## Quick Start

### 1. Set Database URL
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/patient_summary"
```

Or create a `.env` file in the `backend/` directory:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/patient_summary
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Initialize Database
Run the init script:
```bash
python init_db.py
```

Or manually:
```bash
python -c "from backend.utils.db import init_db; init_db()"
```

### 4. Start the Server
```bash
uvicorn backend.server:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `POST /auth/signup` - Register a new user
- `POST /auth/signin` - Login with username/password
- `GET /health` - Health check

## Example Usage

### Signup
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123", "full_name": "Test User"}'
```

### Signin
```bash
curl -X POST http://localhost:8000/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}'
```

