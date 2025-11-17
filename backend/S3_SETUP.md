# AWS S3 Setup Guide

## Step-by-Step: Setting Up S3 for File Uploads

### Step 1: Create S3 Bucket

1. Go to AWS Console → S3 → Create bucket
2. **Bucket name**: `patient-summary-files` (or your choice, must be globally unique)
3. **Region**: Choose closest region (e.g., `us-east-1`)
4. **Block Public Access**: **KEEP IT ON** (we don't need public access)
5. **Versioning**: Disable (optional)
6. **Encryption**: Enable with SSE-S3 (AES-256)
7. Click **Create bucket**

### Step 2: Create IAM User for Backend Access

1. Go to AWS Console → IAM → Users → Create user
2. **User name**: `patient-summary-backend` (or your choice)
3. **Access type**: Select **Programmatic access** (we need API keys)
4. Click **Next: Permissions**

### Step 3: Create IAM Policy (Upload Only)

1. Click **Create policy** (opens in new tab)
2. Go to **JSON** tab
3. Paste this policy (replace `patient-summary-files` with your bucket name):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::patient-summary-files/*",
                "arn:aws:s3:::patient-summary-files"
            ]
        }
    ]
}
```

**What each permission does:**
- `s3:PutObject` - Upload files to S3
- `s3:PutObjectAcl` - Set metadata on uploaded files
- `s3:GetObject` - Download files (for later use)
- `s3:DeleteObject` - Delete files (for cleanup)
- `s3:ListBucket` - List files in bucket (for debugging)

4. Click **Next: Tags** (optional)
5. Click **Next: Review**
6. **Policy name**: `S3PatientFilesUploadPolicy`
7. Click **Create policy**

### Step 4: Attach Policy to IAM User

1. Go back to the IAM user creation tab
2. Click **Refresh** button next to "Create policy"
3. Search for `S3PatientFilesUploadPolicy`
4. Check the box next to it
5. Click **Next: Tags** (optional)
6. Click **Next: Review**
7. Click **Create user**

### Step 5: Save Access Keys

**IMPORTANT**: Save these credentials immediately - you won't see the secret key again!

1. Click **Show** next to "Secret access key"
2. Copy both:
   - **Access key ID**: `AKIA...`
   - **Secret access key**: `wJalr...`
3. Save them securely (you'll need them for environment variables)

### Step 6: Set Environment Variables

Add these to your environment or `.env` file:

```bash
export AWS_ACCESS_KEY_ID="your_access_key_id_here"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key_here"
export AWS_REGION="us-east-1"  # Your bucket region
export S3_BUCKET="patient-summary-files"  # Your bucket name
```

### Step 7: Test S3 Connection

Run this Python script to test:

```python
import boto3
import os

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# Test: List buckets (should show your bucket)
buckets = s3.list_buckets()
print("Buckets:", [b['Name'] for b in buckets['Buckets']])

# Test: Upload a small file
s3.put_object(
    Bucket=os.getenv("S3_BUCKET"),
    Key="test/test.txt",
    Body=b"Hello S3!"
)
print("✅ Upload successful!")
```

## Security Best Practices

1. **Never commit credentials to git** - Use environment variables
2. **Rotate keys regularly** - Change access keys every 90 days
3. **Use IAM roles** (if deploying to EC2/ECS) instead of access keys
4. **Enable CloudTrail** - Log all S3 API calls for audit
5. **Enable MFA delete** - Require MFA for bucket deletion (production)

## Troubleshooting

### Error: "Access Denied"
- Check IAM policy is attached to user
- Verify bucket name in policy matches actual bucket
- Ensure access keys are correct

### Error: "Bucket not found"
- Check bucket name in `S3_BUCKET` env variable
- Verify bucket exists in the correct region
- Check AWS_REGION matches bucket region

### Error: "Invalid credentials"
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
- Check for extra spaces or quotes in environment variables
- Regenerate access keys if needed

## File Upload Flow

1. **Frontend** sends files to `/patients/{patient_id}/files/upload`
2. **Backend** validates file type and size
3. **Database** creates file record immediately (status: `pending`)
4. **Background task** uploads to S3 asynchronously
5. **Database** updates with S3 URL when upload completes
6. **Status** can be checked via `/patients/{patient_id}/files`

## Next Steps

After S3 setup is complete:
1. Run database migration: `python init_db.py` (to create `files` table)
2. Install dependencies: `pip install -r requirements.txt`
3. Start server: `python main.py`
4. Test upload endpoint via `/docs` (Swagger UI)

