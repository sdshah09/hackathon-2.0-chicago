# End-to-End Pipeline Guide

## 🎯 Complete Flow

The system now provides a **complete end-to-end pipeline** that:

1. ✅ Accepts file uploads with specialist type
2. ✅ Uploads files to S3 asynchronously
3. ✅ Extracts text using Pathway parsers
4. ✅ Indexes content in Pathway RAG
5. ✅ Generates specialist-specific summary
6. ✅ Creates PDF from summary
7. ✅ Uploads PDF to S3
8. ✅ Returns S3 download link

## 📋 Quick Start

### 1. Setup Environment

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/patient_summary"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="your-bucket"
export OPENAI_API_KEY="your-openai-key"  # Optional but recommended
```

### 2. Initialize Database

```bash
cd backend
python init_db.py
```

This creates:
- `users` table
- `files` table
- `summary_pdfs` table (NEW!)

### 3. Start Server

```bash
python main.py
```

Server runs at: **http://localhost:8000**

---

## 🚀 End-to-End Usage

### Step 1: Create User

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testpatient",
    "password": "test123",
    "full_name": "Test Patient"
  }'
```

### Step 2: Upload Files with Specialist Type

**Important:** The upload endpoint now accepts `specialist_type` as a form parameter!

```bash
curl -X POST "http://localhost:8000/users/testpatient/files/upload" \
  -F "files=@lab_results.pdf" \
  -F "files=@prescription.jpg" \
  -F "files=@medical_history.pdf" \
  -F "specialist_type=dermatologist"
```

**Response:**
```json
{
  "message": "Successfully queued 3 file(s) for upload. Summary PDF processing started (ID: 1)",
  "files": [
    {
      "id": 1,
      "filename": "lab_results.pdf",
      "upload_status": "pending",
      "extraction_status": "pending"
    },
    ...
  ]
}
```

**What Happens in Background:**
1. Files uploaded to S3 ✅
2. Pathway extracts text ✅
3. Content indexed in Pathway RAG ✅
4. Summary generated for dermatologist ✅
5. PDF created from summary ✅
6. PDF uploaded to S3 ✅

**Processing Time:** 1-3 minutes (depending on file size and number)

### Step 3: Get Summary PDF Link

```bash
curl -X GET "http://localhost:8000/users/testpatient/summary-pdf?specialist_type=dermatologist"
```

**Response (Processing):**
```json
{
  "summary_id": 1,
  "status": "processing",
  "s3_url": null,
  "specialist_type": "dermatologist",
  "message": "Summary PDF is being generated. Please check again in a few moments."
}
```

**Response (Completed):**
```json
{
  "summary_id": 1,
  "status": "completed",
  "s3_url": "https://your-bucket.s3.amazonaws.com/summaries/1/dermatologist_1_abc123.pdf",
  "specialist_type": "dermatologist",
  "message": "Summary PDF is ready for download."
}
```

**Download the PDF:**
```bash
curl -O "https://your-bucket.s3.amazonaws.com/summaries/1/dermatologist_1_abc123.pdf"
```

---

## 📱 Using Swagger UI (Easiest)

1. **Start server:** `python main.py`
2. **Open:** `http://localhost:8000/docs`
3. **Test flow:**
   - `/auth/signup` - Create user
   - `/users/{username}/files/upload` - Upload files
     - **Important:** In Swagger UI, add `specialist_type` as a form field!
   - `/users/{username}/summary-pdf` - Get PDF link
   - Poll this endpoint until `status: "completed"`

---

## 🔄 Complete Example Script

Save as `test_e2e_pipeline.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
USERNAME="testpatient"
SPECIALIST="dermatologist"

echo "🧪 End-to-End Pipeline Test"
echo "============================"

# 1. Signup
echo "\n1. Creating user..."
curl -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"test123\", \"full_name\": \"Test Patient\"}"

# 2. Upload files with specialist type
echo "\n2. Uploading files with specialist_type=$SPECIALIST..."
curl -X POST "$BASE_URL/users/$USERNAME/files/upload" \
  -F "files=@test.pdf" \
  -F "specialist_type=$SPECIALIST"

# 3. Wait for processing
echo "\n3. Waiting 90 seconds for processing..."
sleep 90

# 4. Get summary PDF
echo "\n4. Getting summary PDF..."
curl -X GET "$BASE_URL/users/$USERNAME/summary-pdf?specialist_type=$SPECIALIST" | python3 -m json.tool

echo "\n✅ Test complete!"
echo "Download the PDF from the s3_url in the response above."
```

---

## 🎯 API Endpoints

### Upload Files (NEW: Accepts specialist_type)

**POST** `/users/{username}/files/upload`

**Form Data:**
- `files`: List of files (multipart/form-data)
- `specialist_type`: Type of specialist (form field)

**Available Specialists:**
- `general`
- `dermatologist`
- `ophthalmologist`
- `immunologist`
- `neurologist`
- `cardiologist`

**Response:**
- Returns immediately with file metadata
- Summary PDF processing starts in background

### Get Summary PDF

**GET** `/users/{username}/summary-pdf?specialist_type={type}`

**Query Parameters:**
- `specialist_type`: Type of specialist (default: "general")

**Response:**
- `status`: "processing" | "completed" | "failed"
- `s3_url`: Download link (when completed)
- `summary_id`: ID of the summary PDF record

**Polling:**
- Check every 10-15 seconds until `status: "completed"`
- Then download from `s3_url`

---

## 📊 Database Schema

### New Table: `summary_pdfs`

```sql
CREATE TABLE summary_pdfs (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id),
    specialist_type VARCHAR(50) NOT NULL,
    s3_bucket VARCHAR(255),
    s3_key VARCHAR(512),
    s3_url TEXT,
    status VARCHAR(20) DEFAULT 'processing',
    file_ids INTEGER[],  -- Array of file IDs used
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔍 Monitoring

### Check Processing Status

```sql
-- Check file processing
SELECT id, filename, upload_status, extraction_status 
FROM files 
WHERE patient_id = 1;

-- Check summary PDF status
SELECT id, specialist_type, status, s3_url, created_at
FROM summary_pdfs
WHERE patient_id = 1;
```

### Server Logs

Watch for:
```
✅ Successfully queued 3 file(s) for upload. Summary PDF processing started (ID: 1)
Waiting for files [1, 2, 3] to complete processing...
All files [1, 2, 3] completed processing
Generating summary for patient 1, specialist dermatologist...
Generating PDF for summary 1...
Uploading PDF to S3 for summary 1...
✅ Summary PDF 1 completed: https://...
```

---

## ⚠️ Troubleshooting

### PDF Status Stuck on "processing"

**Check:**
1. Are all files completed? (`upload_status` and `extraction_status` = "completed")
2. Check server logs for errors
3. Verify Pathway RAG is initialized
4. Check OpenAI API key (if using LLM)

### PDF Status is "failed"

**Check:**
1. Server logs for error messages
2. Database for error details
3. Verify all files were processed successfully
4. Check S3 permissions

### Files Not Processing

**Check:**
1. S3 bucket permissions
2. Pathway dependencies installed
3. Database connection
4. File sizes (max 50MB)

---

## ✅ Success Checklist

- [ ] User created successfully
- [ ] Files uploaded (status: "completed")
- [ ] Files extracted (status: "completed")
- [ ] Summary PDF record created
- [ ] Summary PDF status: "completed"
- [ ] S3 URL returned and accessible
- [ ] PDF downloads successfully

---

## 🎉 You're Done!

Once you get the `s3_url` with `status: "completed"`, you can:
1. Download the PDF directly from the S3 URL
2. Share the link with doctors/patients
3. Use it in your frontend application

The PDF contains:
- Patient name (if provided)
- Specialist-specific summary
- All sections (medications, allergies, diagnoses, etc.)
- Source citations
- Professional formatting

**Perfect for hackathon demo!** 🚀

