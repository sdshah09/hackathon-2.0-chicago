#!/usr/bin/env python3
"""Quick test script to verify S3 connection and permissions."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.s3_client import get_s3_client, S3_BUCKET

def test_s3_connection():
    """Test S3 connection and upload permissions."""
    print("Testing S3 connection...")
    print(f"Bucket: {S3_BUCKET}")
    print(f"Region: {os.getenv('AWS_REGION', 'not set')}")
    print()
    
    try:
        # Test 1: Create S3 client
        s3_client = get_s3_client()
        print("✅ S3 client created successfully")
        
        # Test 1a: Try to list buckets (optional - not critical)
        try:
            buckets = s3_client.list_buckets()
            bucket_names = [b['Name'] for b in buckets['Buckets']]
            print(f"✅ Can list buckets: {len(bucket_names)} bucket(s) found")
            if S3_BUCKET not in bucket_names:
                print(f"⚠️  Warning: Bucket '{S3_BUCKET}' not found in list")
                print(f"   Available buckets: {bucket_names}")
            else:
                print(f"✅ Bucket '{S3_BUCKET}' exists")
        except Exception as e:
            print(f"⚠️  Cannot list buckets (not critical): {e}")
            print(f"   Proceeding with direct bucket operations...")
        
        # Test 2: Try to upload a test file (CRITICAL)
        test_key = "test/connection_test.txt"
        test_content = b"Hello from backend! S3 connection works."
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=test_key,
            Body=test_content,
            ContentType="text/plain"
        )
        print(f"✅ Successfully uploaded test file to s3://{S3_BUCKET}/{test_key}")
        
        # Test 3: Try to read it back
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=test_key)
        content = response['Body'].read()
        if content == test_content:
            print(f"✅ Successfully downloaded and verified test file")
        
        # Test 4: Clean up - delete test file
        # s3_client.delete_object(Bucket=S3_BUCKET, Key=test_key)
        # print(f"✅ Successfully deleted test file")
        
        print()
        print("🎉 All S3 tests passed! Your setup is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set")
        print("2. Verify S3_BUCKET name matches your actual bucket")
        print("3. Ensure AWS_REGION matches your bucket region")
        print("4. Confirm IAM policy allows s3:PutObject, s3:GetObject, s3:DeleteObject")
        return False

if __name__ == "__main__":
    success = test_s3_connection()
    sys.exit(0 if success else 1)

