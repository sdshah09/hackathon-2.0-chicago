# End-to-End Running Guide

## 🚀 Complete Setup & Run Instructions

### Step 1: Environment Setup

Create a `.env` file in the `backend/` directory or export variables:

```bash
# Database
export DATABASE_URL="postgresql://user:password@localhost:5432/patient_summary"

# AWS S3
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="your-bucket-name"

# OpenAI (for LLM summary generation)
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Enable quality check
export ENABLE_QUALITY_CHECK="false"
```

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** This may take 5-10 minutes (Pathway, Docling, PaddleOCR are large packages)

### Step 3: Initialize Database

```bash
python init_db.py
```

This creates:
- `users` table
- `files` table

### Step 4: Start the Server

```bash
python main.py
```

Server runs at: **http://localhost:8000**
API Docs: **http://localhost:8000/docs**

---

## 🧪 End-to-End Test Flow

### Test 1: Create a User

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123",
    "full_name": "Test Patient"
  }'
```

**Expected Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "testuser",
    "full_name": "Test Patient"
  }
}
```

### Test 2: Upload Medical Documents

```bash
curl -X POST "http://localhost:8000/users/testuser/files/upload" \
  -F "files=@/path/to/lab_results.pdf" \
  -F "files=@/path/to/prescription.jpg" \
  -F "files=@/path/to/medical_history.pdf"
```

**Expected Response:**
```json
{
  "message": "Successfully queued 3 file(s) for upload",
  "files": [
    {
      "id": 1,
      "patient_id": 1,
      "filename": "lab_results.pdf",
      "file_type": "pdf",
      "file_size": 123456,
      "upload_status": "pending",
      "extraction_status": "pending"
    },
    ...
  ]
}
```

**What Happens in Background:**
1. Files uploaded to S3 (async)
2. Pathway parses files (async)
3. Text extracted and indexed (async)
4. Status updates in database

**Wait 30-60 seconds** for processing to complete.

### Test 3: Check File Status

```bash
curl -X GET "http://localhost:8000/users/testuser/files"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "filename": "lab_results.pdf",
    "upload_status": "completed",
    "extraction_status": "completed",
    "s3_url": "https://..."
  }
]
```

### Test 4: Get Available Specialists

```bash
curl -X GET "http://localhost:8000/specialists"
```

**Expected Response:**
```json
{
  "specialists": [
    "dermatologist",
    "ophthalmologist",
    "immunologist",
    "neurologist",
    "cardiologist",
    "general"
  ]
}
```

### Test 5: Generate Patient Summary

```bash
curl -X POST "http://localhost:8000/users/testuser/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "specialist_type": "dermatologist"
  }'
```

**Expected Response:**
```json
{
  "summary": "## Active Medications\n• Medication name [Source: prescription.pdf]\n...",
  "sections": {
    "Active Medications": "...",
    "Allergies": "...",
    ...
  },
  "sources": [
    {
      "filename": "lab_results.pdf",
      "file_id": 1,
      "s3_url": "https://...",
      "chunk_index": 2
    }
  ],
  "specialist_type": "dermatologist",
  "num_sources": 5
}
```

### Test 6: Query Patient Records (Alternative)

```bash
curl -X POST "http://localhost:8000/users/testuser/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What medications is the patient currently taking?",
    "top_k": 5
  }'
```

---

## 🎯 Quick Test Script

Save this as `test_end_to_end.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "🧪 End-to-End Test"
echo "=================="

# 1. Signup
echo "\n1. Creating user..."
curl -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123", "full_name": "Test Patient"}'

# 2. Upload file (use a test file)
echo "\n2. Uploading file..."
curl -X POST "$BASE_URL/users/testuser/files/upload" \
  -F "files=@test.pdf"

# 3. Wait for processing
echo "\n3. Waiting 30 seconds for processing..."
sleep 30

# 4. Check files
echo "\n4. Checking file status..."
curl -X GET "$BASE_URL/users/testuser/files"

# 5. Generate summary
echo "\n5. Generating summary..."
curl -X POST "$BASE_URL/users/testuser/summary" \
  -H "Content-Type: application/json" \
  -d '{"specialist_type": "general"}'

echo "\n✅ Test complete!"
```

Make it executable:
```bash
chmod +x test_end_to_end.sh
./test_end_to_end.sh
```

---

## 📋 Complete Checklist

Before running, ensure:

- [ ] PostgreSQL is running
- [ ] Database created (`createdb patient_summary`)
- [ ] Environment variables set
- [ ] AWS S3 bucket exists and is accessible
- [ ] Poppler installed (`brew install poppler` on macOS)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized (`python init_db.py`)
- [ ] OpenAI API key set (optional, for LLM summaries)

---

## 🔍 Monitoring the Process

### Check Server Logs

When you start the server, you'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

When files are uploaded:
```
✅ Successfully queued 3 file(s) for upload
```

When processing:
```
✅ Successfully extracted text from file 1 using Pathway
✅ Indexed 11 chunks in Pathway for file 1
```

### Check Database

```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Check users
SELECT * FROM users;

# Check files
SELECT id, filename, upload_status, extraction_status FROM files;
```

### Check S3

```bash
# List files in bucket
aws s3 ls s3://your-bucket-name/patients/
```

---

## 🎬 Demo Flow (For Hackathon)

### 1. Setup (2 minutes)
```bash
# Set environment variables
export DATABASE_URL="..."
export AWS_ACCESS_KEY_ID="..."
export OPENAI_API_KEY="..."

# Install & initialize
pip install -r requirements.txt
python init_db.py
```

### 2. Start Server (30 seconds)
```bash
python main.py
```

### 3. Demo Flow (5 minutes)

**Step 1: Create Patient**
- Open `http://localhost:8000/docs`
- Use `/auth/signup` endpoint
- Create user: `testpatient`

**Step 2: Upload Documents**
- Use `/users/{username}/files/upload` endpoint
- Upload 2-3 sample medical documents
- Show immediate response

**Step 3: Wait for Processing**
- Show file status endpoint
- Explain background processing
- Wait 30-60 seconds

**Step 4: Generate Summary**
- Use `/users/{username}/summary` endpoint
- Select specialist type: `dermatologist`
- Show generated summary with citations

**Step 5: Show Features**
- Highlight source citations
- Show structured sections
- Demonstrate specialist filtering

---

## 🐛 Troubleshooting

### Server Won't Start

**Error:** `ModuleNotFoundError: No module named 'backend'`
- **Fix:** Run from project root: `python -m backend.main`

**Error:** `DATABASE_URL not set`
- **Fix:** Export `DATABASE_URL` environment variable

### File Upload Fails

**Error:** `S3 upload failed`
- **Fix:** Check AWS credentials and bucket permissions

**Error:** `File exceeds maximum size`
- **Fix:** Files must be < 50MB

### Summary Generation Fails

**Error:** `No documents found`
- **Fix:** Wait for file processing to complete (check extraction_status)

**Error:** `LLM not available`
- **Fix:** Set `OPENAI_API_KEY` environment variable
- **Note:** System still works, but returns raw text instead of structured summary

### Pathway Parsing Fails

**Error:** `Poppler not found`
- **Fix:** `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)

**Error:** `Pathway parser not available`
- **Fix:** `pip install pathway[llm] docling`

---

## ✅ Success Indicators

You'll know everything is working when:

1. ✅ Server starts without errors
2. ✅ Files upload successfully (status: `completed`)
3. ✅ Extraction completes (status: `completed`)
4. ✅ Summary generation returns structured output
5. ✅ Summary includes source citations
6. ✅ Summary is filtered by specialist type

---

## 🎯 Quick Start (Copy-Paste)

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/patient_summary"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="your-bucket"
export OPENAI_API_KEY="your-openai-key"

# 2. Install & setup
cd backend
pip install -r requirements.txt
python init_db.py

# 3. Start server
python main.py

# 4. Open browser
# http://localhost:8000/docs
```

---

## 📱 Using Swagger UI (Easiest Way)

1. **Start server:** `python main.py`
2. **Open:** `http://localhost:8000/docs`
3. **Test endpoints:**
   - `/auth/signup` - Create user
   - `/users/{username}/files/upload` - Upload files
   - `/users/{username}/files` - Check status
   - `/users/{username}/summary` - Generate summary
   - `/specialists` - See available specialists

**Swagger UI is the easiest way to test everything!** 🎉

