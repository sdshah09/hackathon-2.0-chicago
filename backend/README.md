# Backend Setup Guide - Patient Summary Assistant

## 🎯 End-to-End Pipeline (NEW!)

**Upload files → Get PDF summary link automatically!**

The system now provides a complete end-to-end pipeline:
1. Upload files with `specialist_type` parameter
2. Files processed automatically (S3 upload, Pathway extraction, RAG indexing)
3. Summary PDF generated and uploaded to S3
4. Get download link via `/users/{username}/summary-pdf`

**Quick Example:**
```bash
# Upload files with specialist type
curl -X POST "http://localhost:8000/users/testuser/files/upload" \
  -F "files=@lab_results.pdf" \
  -F "specialist_type=dermatologist"

# Get PDF link (poll until status: "completed")
curl "http://localhost:8000/users/testuser/summary-pdf?specialist_type=dermatologist"
```

📖 **See [END_TO_END_PIPELINE.md](./END_TO_END_PIPELINE.md) for complete guide**

---

## Prerequisites
- PostgreSQL running (locally or remote)
- Python 3.11+ with pip
- AWS S3 bucket and credentials (for file storage)
- Poppler installed (for PDF processing): `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in the `backend/` directory or export them:

```bash
# Database
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/patient_summary"

# AWS S3
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="your-bucket-name"

# OpenAI (optional but recommended for better summaries)
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** Pathway and Docling are large packages. Installation may take a few minutes.

### 3. Initialize Database

```bash
python init_db.py
```

Or manually:
```bash
python -c "from backend.utils.db import init_db; init_db()"
```

### 4. Start the Server

```bash
# Option 1: Using main.py
python main.py

# Option 2: Using uvicorn directly
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Testing

### 1. Test Pathway Integration

Test that Pathway parsers work correctly:

```bash
python test_pathway_integration.py
```

This will test parsing on sample files (if available in the backend directory).

### 2. Test S3 Connection

```bash
python test_s3.py
```

### 3. Test API Endpoints

#### Signup
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123",
    "full_name": "Test User"
  }'
```

#### Signin
```bash
curl -X POST http://localhost:8000/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123"
  }'
```

#### Upload Files
```bash
curl -X POST "http://localhost:8000/users/testuser/files/upload" \
  -F "files=@/path/to/image.jpg" \
  -F "files=@/path/to/document.pdf"
```

#### List User Files
```bash
curl -X GET "http://localhost:8000/users/testuser/files"
```

#### Generate Patient Summary
```bash
# Generate summary for dermatologist
curl -X POST "http://localhost:8000/users/testuser/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "specialist_type": "dermatologist"
  }'

# Get available specialists
curl -X GET "http://localhost:8000/specialists"
```

### 4. Test via Swagger UI

1. Start the server
2. Open `http://localhost:8000/docs` in your browser
3. Use the interactive API documentation to test endpoints

## API Endpoints

### Authentication
- `POST /auth/signup` - Register a new user
- `POST /auth/signin` - Login with username/password

### Files
- `POST /users/{username}/files/upload` - Upload files (JPEG, PNG, PDF)
- `GET /users/{username}/files` - List user's files

### Patient Summary (Main Feature)
- `POST /users/{username}/summary` - Generate specialist-specific health summary
- `GET /specialists` - Get available specialist types
- `GET /users/{username}/documents` - Get indexed documents for patient

### RAG Queries
- `POST /users/{username}/query` - Query patient records using RAG

### Health
- `GET /health` - Health check

## Architecture

### File Upload Flow
```
1. Frontend uploads files → FastAPI
2. FastAPI validates & creates DB records
3. Files uploaded to S3 (async)
4. Pathway parses files (async)
5. Extracted text stored in database
```

### Pathway Integration
- **DoclingParser**: Used for PDFs (fast, no OCR needed for text PDFs)
- **PaddleOCRParser**: Used for images and scanned PDFs (with PPStructureV3)
- Parsing happens automatically after S3 upload completes
- Text extraction is asynchronous and non-blocking

## Troubleshooting

### Pathway Parser Not Available
```bash
pip install pathway[llm] docling unstructured
```

### Poppler Not Found (PDF errors)
```bash
# macOS
brew install poppler

# Linux
apt-get install poppler-utils
```

### Database Connection Errors
- Check `DATABASE_URL` is set correctly
- Ensure PostgreSQL is running
- Verify database exists: `createdb patient_summary`

### S3 Upload Errors
- Verify AWS credentials are set
- Check S3 bucket exists and is accessible
- Verify IAM permissions (PutObject, GetObject)

## Development

### Project Structure
```
backend/
├── main.py              # Server entry point
├── server.py            # FastAPI app & routes
├── models.py            # Pydantic models
├── auth_service.py      # Authentication logic
├── services/
│   ├── file_service.py      # File upload & S3
│   ├── extraction_service.py # Text extraction orchestration
│   └── pathway_service.py   # Pathway parsing
└── utils/
    ├── db.py            # Database utilities
    ├── s3_client.py     # S3 client
    └── schema.sql      # Database schema
```

### Running Tests
```bash
# Test Pathway integration
python test_pathway_integration.py

# Test S3 connection
python test_s3.py
```

## Next Steps

1. **Pathway RAG Pipeline**: Set up Pathway's live indexing for RAG queries
2. **Patient Summary Generation**: Implement LLM-based summary generation
3. **Specialist Filtering**: Add logic to filter content by specialist type
4. **Source Citations**: Enhance metadata for traceability
