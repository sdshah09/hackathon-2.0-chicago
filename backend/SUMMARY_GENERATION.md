# Patient Summary Generation Guide

## 🎯 Overview

The system generates **1-2 page patient health summaries** tailored for specific specialists using Pathway RAG + LLM.

## ✅ Features Implemented

### Core Requirements (Prioritize)
- ✅ **Pathway Live Index**: Documents automatically indexed after upload
- ✅ **Specialist-Specific Summaries**: Filtered by specialist type
- ✅ **Standard Clinical Sections**: Medications, Allergies, Diagnoses, Lab Results, etc.
- ✅ **Source Citations**: Every piece of information traceable to source documents
- ✅ **Privacy by Default**: No AI diagnosis, only reports what's in documents

### Stretch Goals (If Time Permits)
- ✅ **Quality Check**: Optional verification that statements are supported by sources
- ⏳ **Patient Review/Edit**: Can be added via frontend
- ⏳ **Interactive Summary**: Can be added via frontend

---

## 🚀 How to Use

### 1. Upload Patient Documents

```bash
curl -X POST "http://localhost:8000/users/testuser/files/upload" \
  -F "files=@lab_results.pdf" \
  -F "files=@medical_history.pdf" \
  -F "files=@prescription.jpg"
```

Documents are automatically:
- Uploaded to S3
- Parsed with Pathway
- Indexed for RAG queries

### 2. Generate Summary for Specialist

```bash
curl -X POST "http://localhost:8000/users/testuser/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "specialist_type": "dermatologist",
    "custom_query": null
  }'
```

**Available Specialist Types:**
- `dermatologist` - Skin conditions, rashes, dermatological issues
- `ophthalmologist` - Eye conditions, vision problems
- `immunologist` - Allergies, immune system conditions
- `neurologist` - Neurological symptoms, brain conditions
- `cardiologist` - Heart conditions, cardiovascular issues
- `general` - General medical information

### 3. Response Format

```json
{
  "summary": "## Active Medications\n• Metformin 500mg twice daily [Source: prescription.pdf]\n...",
  "sections": {
    "Active Medications": "• Metformin 500mg...",
    "Allergies": "• Penicillin [Source: medical_history.pdf]",
    ...
  },
  "sources": [
    {
      "filename": "lab_results.pdf",
      "file_id": 123,
      "s3_url": "https://...",
      "chunk_index": 2
    }
  ],
  "specialist_type": "dermatologist",
  "num_sources": 5
}
```

---

## 📋 Summary Structure

Each summary includes:

1. **Active Medications**
   - Current medications with dosages
   - Source citations

2. **Allergies**
   - Known allergies and reactions
   - Source citations

3. **Recent Diagnoses**
   - Diagnoses relevant to specialist
   - Dates if available
   - Source citations

4. **Lab Results** (if relevant)
   - Recent lab results
   - Dates and values
   - Source citations

5. **Imaging Findings** (if relevant)
   - Recent imaging results
   - Dates
   - Source citations

6. **Current Symptoms**
   - Symptoms relevant to specialist
   - Source citations

7. **Relevant Medical History**
   - Past medical history
   - Source citations

---

## 🔍 How It Works

### Step-by-Step Process

1. **User Requests Summary**
   ```
   POST /users/{username}/summary
   {
     "specialist_type": "dermatologist"
   }
   ```

2. **Pathway RAG Retrieval**
   - Queries Pathway index for patient documents
   - Filters by patient_id
   - Retrieves top 20 relevant chunks
   - Uses specialist-specific extraction prompts

3. **LLM Summary Generation**
   - Combines retrieved chunks
   - Generates structured summary with LLM
   - Ensures all information is cited
   - Organizes into clinical sections

4. **Optional Quality Check**
   - Verifies each statement is supported by sources
   - Marks unverified statements
   - Can be enabled with `ENABLE_QUALITY_CHECK=true`

5. **Response with Citations**
   - Returns formatted summary
   - Includes all source documents
   - Provides traceability

---

## 🧪 Testing

### Test Summary Generation

```bash
# 1. Get available specialists
curl http://localhost:8000/specialists

# 2. Generate summary for dermatologist
curl -X POST "http://localhost:8000/users/testuser/summary" \
  -H "Content-Type: application/json" \
  -d '{"specialist_type": "dermatologist"}'

# 3. Generate summary with custom query
curl -X POST "http://localhost:8000/users/testuser/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "specialist_type": "general",
    "custom_query": "What are the patient's current medications and allergies?"
  }'
```

### Test via Swagger UI

1. Open `http://localhost:8000/docs`
2. Use `/users/{username}/summary` endpoint
3. Select specialist type
4. Generate summary

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required for LLM generation
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Enable quality check
export ENABLE_QUALITY_CHECK="true"
```

### Without OpenAI API Key

If `OPENAI_API_KEY` is not set:
- Summary generation will return raw retrieved text
- Sections will not be parsed
- Still functional but less structured

---

## 📊 Example Output

### For Dermatologist

```
## Active Medications
• Topical corticosteroid cream (applied twice daily) [Source: prescription.pdf]
• Antihistamine 10mg daily [Source: medical_history.pdf]

## Allergies
• Latex allergy - causes skin rash [Source: allergy_report.pdf]
• Nickel allergy - contact dermatitis [Source: medical_history.pdf]

## Recent Diagnoses
• Atopic dermatitis (diagnosed 2024-01-15) [Source: dermatology_visit.pdf]
• Contact dermatitis (diagnosed 2024-02-20) [Source: dermatology_visit.pdf]

## Current Symptoms
• Persistent dry, itchy skin on arms and legs [Source: patient_notes.pdf]
• Occasional flare-ups of red, scaly patches [Source: patient_notes.pdf]

## Relevant Medical History
• History of eczema since childhood [Source: medical_history.pdf]
• Previous treatment with topical steroids [Source: prescription_history.pdf]
```

---

## 🔒 Privacy & Safety

### Built-in Protections

1. **No AI Diagnosis**
   - LLM explicitly instructed not to diagnose
   - Only reports what's in source documents

2. **Source Verification**
   - Every statement must have a source citation
   - Quality check verifies statements against sources

3. **Patient-Specific**
   - All queries filtered by patient_id
   - No cross-patient data leakage

4. **Explicit Instructions**
   - LLM prompt includes "Do NOT make diagnoses"
   - LLM prompt includes "Only include information explicitly stated"

---

## 🚀 Next Steps (If Time Permits)

1. **Add Patient Review/Edit**
   - Endpoint to save edited summaries
   - Store in database

2. **Interactive Summary**
   - Add clickable source links
   - Drill-down to full document sections

3. **Enhanced Quality Check**
   - Automatic verification of all statements
   - Confidence scores for each claim

4. **Specialist Templates**
   - Custom templates for each specialist type
   - Pre-defined section structures

---

## 📝 API Reference

### Generate Summary
```
POST /users/{username}/summary
Body: {
  "specialist_type": "dermatologist",
  "custom_query": "optional custom query"
}
```

### Get Available Specialists
```
GET /specialists
```

### Get Patient Documents
```
GET /users/{username}/documents
```

---

## ✅ Summary

**Your system now:**
- ✅ Extracts ALL text from documents (Pathway parsers)
- ✅ Indexes documents in Pathway (live index)
- ✅ Generates specialist-specific summaries (LLM + RAG)
- ✅ Includes source citations (traceability)
- ✅ Follows privacy guidelines (no AI diagnosis)
- ✅ Uses standard clinical sections (structured output)

**Ready for hackathon demo!** 🎉

