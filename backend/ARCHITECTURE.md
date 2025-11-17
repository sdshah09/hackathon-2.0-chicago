# Backend Architecture: File Upload & Text Extraction

## Overview

The system handles file uploads and text extraction in a fully asynchronous, parallel architecture:

1. **Frontend** sends multiple files → **FastAPI Backend**
2. **Backend** validates files → Creates DB records immediately
3. **S3 Upload** happens asynchronously in background
4. **Text Extraction** triggers automatically after upload completes
5. Both operations run in parallel for multiple files

## Architecture Flow

```
Frontend Request
    ↓
POST /patients/{id}/files/upload
    ↓
[FastAPI Server]
    ├─ Validate files (type, size)
    ├─ Create DB records (status: 'pending')
    └─ Return immediately with file IDs
    ↓
[Background Tasks - Parallel Execution]
    │
    ├─→ Task 1: Upload File 1 to S3
    │   ├─ Status: 'pending' → 'uploading' → 'completed'
    │   └─ Trigger Extraction for File 1 (async)
    │
    ├─→ Task 2: Upload File 2 to S3
    │   ├─ Status: 'pending' → 'uploading' → 'completed'
    │   └─ Trigger Extraction for File 2 (async)
    │
    └─→ Task N: Upload File N to S3
        ├─ Status: 'pending' → 'uploading' → 'completed'
        └─ Trigger Extraction for File N (async)
```

## Component Details

### 1. File Upload Service (`services/file_service.py`)

**Responsibilities:**
- Create file records in database
- Upload files to S3 asynchronously
- Update upload status
- Trigger text extraction after upload

**Key Functions:**
- `create_file_record()` - Creates DB record immediately (fast response)
- `upload_file_to_s3_async()` - Async S3 upload using ThreadPoolExecutor
- `update_file_upload_status()` - Updates status in database
- `update_file_s3_info()` - Saves S3 URL after upload

**Thread Pool:** Max 5 concurrent uploads

### 2. Text Extraction Service (`services/extraction_service.py`)

**Responsibilities:**
- Extract text from uploaded files
- Update extraction status
- Save extracted text to database

**Key Functions:**
- `extract_text_from_file()` - Main extraction function (async)
- `_perform_extraction()` - Placeholder for actual extraction logic
- `update_extraction_status()` - Updates status in database
- `save_extracted_text()` - Saves extracted text (to be implemented)

**Thread Pool:** Max 3 concurrent extractions

**Current Status:** Boilerplate - ready for PaddleOCR/PDF extraction implementation

### 3. S3 Client (`utils/s3_client.py`)

**Responsibilities:**
- Upload files to S3
- Download files from S3
- Delete files from S3
- Check file existence

**Key Functions:**
- `upload_file()` - Upload to S3
- `download_file()` - Download from S3
- `delete_file()` - Delete from S3
- `file_exists()` - Check if file exists

### 4. Database Schema

**Tables:**
- `users` - Patient/user information
- `files` - File metadata and status tracking
  - `upload_status`: 'pending', 'uploading', 'completed', 'failed'
  - `extraction_status`: 'pending', 'processing', 'completed', 'failed'

## Parallel Execution Details

### Upload Flow (Per File)

1. **Immediate Response** (< 100ms):
   - Validate file
   - Create DB record
   - Return to frontend

2. **Background Upload** (async):
   - Download file content
   - Upload to S3 (ThreadPoolExecutor)
   - Update DB with S3 URL
   - **Trigger extraction** (fire-and-forget)

3. **Background Extraction** (async):
   - Download file from S3
   - Extract text (PaddleOCR/PDF parser)
   - Save extracted text
   - Update extraction status

### Multiple Files Handling

When frontend sends 5 files:
- All 5 DB records created immediately
- All 5 uploads start in parallel (max 5 concurrent)
- Each upload triggers extraction when complete
- Extractions run in parallel (max 3 concurrent)

**Example Timeline:**
```
T=0ms:   Request received
T=50ms:  All 5 DB records created → Response sent
T=100ms: Upload 1, 2, 3, 4, 5 start (parallel)
T=2s:    Upload 1 completes → Extraction 1 starts
T=2.5s:  Upload 2 completes → Extraction 2 starts
T=3s:    Upload 3 completes → Extraction 3 starts
T=3.5s:  Upload 4 completes → Extraction 4 waits (max 3)
T=4s:    Upload 5 completes → Extraction 5 waits
T=5s:    Extraction 1 completes → Extraction 4 starts
T=6s:    Extraction 2 completes → Extraction 5 starts
```

## API Endpoints

### `POST /patients/{patient_id}/files/upload`

**Request:**
- Multiple files (multipart/form-data)
- File types: JPEG, PNG, PDF
- Max size: 50MB per file

**Response:**
```json
{
  "message": "Successfully queued 3 file(s) for upload",
  "files": [
    {
      "id": 1,
      "patient_id": 1,
      "filename": "test.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "upload_status": "pending",
      "extraction_status": "pending"
    }
  ]
}
```

**Flow:**
1. Validates files
2. Creates DB records
3. Queues async uploads
4. Returns immediately

### `GET /patients/{patient_id}/files`

**Response:**
```json
[
  {
    "id": 1,
    "filename": "test.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "s3_url": "https://bucket.s3.region.amazonaws.com/...",
    "upload_status": "completed",
    "extraction_status": "processing"
  }
]
```

## Status Tracking

### Upload Status
- `pending` - File record created, upload not started
- `uploading` - Currently uploading to S3
- `completed` - Successfully uploaded to S3
- `failed` - Upload failed

### Extraction Status
- `pending` - Waiting for upload to complete
- `processing` - Currently extracting text
- `completed` - Text extraction finished
- `failed` - Extraction failed

## Implementation Status

### ✅ Completed
- [x] S3 upload infrastructure
- [x] Database schema for files
- [x] Async upload service
- [x] Extraction service boilerplate
- [x] Parallel execution architecture
- [x] Status tracking

### 🚧 To Be Implemented
- [ ] PaddleOCR integration for JPEG/PNG
- [ ] PDF text extraction
- [ ] Extracted text storage in database
- [ ] Error handling and retry logic
- [ ] Progress tracking for extraction

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET=patient-summary-hackathon
```

## Next Steps

1. **Implement PaddleOCR:**
   ```python
   # In extraction_service.py
   from paddleocr import PaddleOCR
   ocr = PaddleOCR(use_angle_cls=True, lang='en')
   result = ocr.ocr(file_content, cls=True)
   ```

2. **Implement PDF Extraction:**
   ```python
   # In extraction_service.py
   import pdfplumber
   with pdfplumber.open(file_content) as pdf:
       text = '\n'.join([page.extract_text() for page in pdf.pages])
   ```

3. **Add Extracted Text Table:**
   ```sql
   CREATE TABLE extracted_texts (
       id SERIAL PRIMARY KEY,
       file_id INTEGER REFERENCES files(id),
       extracted_text TEXT,
       metadata JSONB,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

4. **Add Progress Tracking:**
   - WebSocket or polling endpoint for real-time status
   - Percentage completion for large files

