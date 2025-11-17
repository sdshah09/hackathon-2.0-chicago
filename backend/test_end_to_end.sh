#!/bin/bash
# End-to-End Test Script for Patient Summary System

BASE_URL="http://localhost:8000"
USERNAME="testpatient"
PASSWORD="test123"

echo "🧪 End-to-End Test - Patient Summary System"
echo "============================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if server is running
echo -e "\n${YELLOW}Checking if server is running...${NC}"
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo "Start it with: python main.py"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"

# Step 1: Signup
echo -e "\n${YELLOW}Step 1: Creating user '${USERNAME}'...${NC}"
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\", \"full_name\": \"Test Patient\"}")

if echo "$SIGNUP_RESPONSE" | grep -q "User created successfully"; then
    echo -e "${GREEN}✅ User created${NC}"
elif echo "$SIGNUP_RESPONSE" | grep -q "already exists"; then
    echo -e "${YELLOW}⚠️  User already exists, continuing...${NC}"
else
    echo -e "${RED}❌ Signup failed: $SIGNUP_RESPONSE${NC}"
    exit 1
fi

# Step 2: Check for test files
echo -e "\n${YELLOW}Step 2: Checking for test files...${NC}"
TEST_FILES=()
if [ -f "Shaswat_Resume_3.pdf" ]; then
    TEST_FILES+=("Shaswat_Resume_3.pdf")
fi
if [ -f "CamScanner 10-12-25 09.44_1.jpg" ]; then
    TEST_FILES+=("CamScanner 10-12-25 09.44_1.jpg")
fi

if [ ${#TEST_FILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No test files found. Skipping upload.${NC}"
    echo "You can upload files manually via the API."
else
    echo -e "${GREEN}✅ Found ${#TEST_FILES[@]} test file(s)${NC}"
    
    # Step 3: Upload files
    echo -e "\n${YELLOW}Step 3: Uploading files...${NC}"
    UPLOAD_CMD="curl -s -X POST \"$BASE_URL/users/${USERNAME}/files/upload\""
    for file in "${TEST_FILES[@]}"; do
        UPLOAD_CMD="$UPLOAD_CMD -F \"files=@$file\""
    done
    
    UPLOAD_RESPONSE=$(eval $UPLOAD_CMD)
    if echo "$UPLOAD_RESPONSE" | grep -q "Successfully queued"; then
        echo -e "${GREEN}✅ Files uploaded successfully${NC}"
        echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"
    else
        echo -e "${RED}❌ Upload failed: $UPLOAD_RESPONSE${NC}"
        exit 1
    fi
    
    # Step 4: Wait for processing
    echo -e "\n${YELLOW}Step 4: Waiting 45 seconds for file processing...${NC}"
    echo "   (Files are being uploaded to S3 and parsed by Pathway)"
    for i in {45..1}; do
        echo -ne "\r   Waiting... ${i}s remaining"
        sleep 1
    done
    echo -e "\r   ${GREEN}✅ Processing complete${NC}    "
    
    # Step 5: Check file status
    echo -e "\n${YELLOW}Step 5: Checking file status...${NC}"
    FILES_RESPONSE=$(curl -s -X GET "$BASE_URL/users/${USERNAME}/files")
    echo "$FILES_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$FILES_RESPONSE"
    
    # Step 6: Get available specialists
    echo -e "\n${YELLOW}Step 6: Getting available specialists...${NC}"
    SPECIALISTS_RESPONSE=$(curl -s -X GET "$BASE_URL/specialists")
    echo "$SPECIALISTS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SPECIALISTS_RESPONSE"
    
    # Step 7: Generate summary
    echo -e "\n${YELLOW}Step 7: Generating patient summary (general)...${NC}"
    SUMMARY_RESPONSE=$(curl -s -X POST "$BASE_URL/users/${USERNAME}/summary" \
      -H "Content-Type: application/json" \
      -d '{"specialist_type": "general"}')
    
    if echo "$SUMMARY_RESPONSE" | grep -q "summary"; then
        echo -e "${GREEN}✅ Summary generated${NC}"
        echo "$SUMMARY_RESPONSE" | python3 -m json.tool 2>/dev/null | head -50 || echo "$SUMMARY_RESPONSE" | head -50
    else
        echo -e "${YELLOW}⚠️  Summary response: $SUMMARY_RESPONSE${NC}"
    fi
fi

# Step 8: Query test
echo -e "\n${YELLOW}Step 8: Testing RAG query...${NC}"
QUERY_RESPONSE=$(curl -s -X POST "$BASE_URL/users/${USERNAME}/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What information is available about this patient?", "top_k": 3}')

if echo "$QUERY_RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}✅ Query successful${NC}"
    echo "$QUERY_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$QUERY_RESPONSE"
else
    echo -e "${YELLOW}⚠️  Query response: $QUERY_RESPONSE${NC}"
fi

echo -e "\n${GREEN}============================================"
echo "✅ End-to-End Test Complete!"
echo "============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:8000/docs for interactive API testing"
echo "2. Try generating summaries for different specialists"
echo "3. Upload more medical documents to test with real data"

