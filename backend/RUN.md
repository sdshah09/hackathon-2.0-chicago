# Quick Start - Running the Backend

## 🚀 Fast Setup (5 minutes)

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="your-bucket"
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Start Server
```bash
python main.py
```

Server runs at: **http://localhost:8000**
API Docs: **http://localhost:8000/docs**

---

## 🧪 Testing

### Test Pathway Integration
```bash
python test_pathway_integration.py
```

### Test S3 Connection
```bash
python test_s3.py
```

### Test API (using curl)
```bash
# 1. Signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123", "full_name": "Test User"}'

# 2. Upload file
curl -X POST "http://localhost:8000/users/test/files/upload" \
  -F "files=@test.pdf"

# 3. List files
curl -X GET "http://localhost:8000/users/test/files"
```

### Test via Browser
1. Open http://localhost:8000/docs
2. Use the interactive Swagger UI to test endpoints

---

## ✅ Checklist Before Running

- [ ] PostgreSQL is running
- [ ] Database created
- [ ] Environment variables set
- [ ] AWS S3 bucket exists
- [ ] Poppler installed (`brew install poppler` on macOS)
- [ ] Dependencies installed (`pip install -r requirements.txt`)

---

## 🔍 Verify Everything Works

1. **Health Check**: http://localhost:8000/health
2. **API Docs**: http://localhost:8000/docs
3. **Test Pathway**: `python test_pathway_integration.py`
4. **Test Upload**: Upload a file via `/docs` interface

---

## 📝 Common Issues

**"Pathway parser not available"**
→ `pip install pathway[llm] docling`

**"Poppler not found"**
→ `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)

**"Database connection failed"**
→ Check `DATABASE_URL` and ensure PostgreSQL is running

**"S3 upload failed"**
→ Verify AWS credentials and bucket permissions

