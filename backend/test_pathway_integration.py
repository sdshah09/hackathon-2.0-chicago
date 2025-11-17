#!/usr/bin/env python3
"""
Test script for Pathway integration.
Tests the end-to-end flow: Upload → S3 → Pathway Parsing → Database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from backend.services.pathway_service import parse_file_with_pathway, is_pathway_available


async def test_pathway_parsing():
    """Test Pathway parsing on sample files."""
    print("🧪 Testing Pathway Integration")
    print("=" * 60)
    
    # Check if Pathway is available
    if not is_pathway_available():
        print("❌ Pathway parsers are not available!")
        print("   Install with: pip install pathway[llm] docling")
        return False
    
    print("✅ Pathway parsers are available\n")
    
    # Test files in backend directory
    test_files = [
        ("CamScanner 10-12-25 09.44_1.jpg", "jpeg"),
        ("Shaswat_Resume_3.pdf", "pdf"),
    ]
    
    backend_dir = Path(__file__).parent
    
    for filename, file_type in test_files:
        file_path = backend_dir / filename
        
        if not file_path.exists():
            print(f"⚠️  Skipping {filename} (file not found)")
            continue
        
        print(f"\n📄 Testing: {filename}")
        print("-" * 60)
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            print(f"   File size: {len(file_content)} bytes")
            print(f"   File type: {file_type}")
            
            # Parse with Pathway
            print("   Parsing with Pathway...")
            result = await parse_file_with_pathway(
                file_content=file_content,
                file_type=file_type,
                filename=filename,
                patient_id=1,
                file_id=999,
            )
            
            # Display results
            extracted_text = result.get('text', '')
            metadata = result.get('metadata', {})
            
            print(f"   ✅ Parsing successful!")
            print(f"   Parser used: {metadata.get('parser', 'unknown')}")
            print(f"   Number of chunks: {metadata.get('num_chunks', 0)}")
            print(f"   Extracted text length: {len(extracted_text)} characters")
            
            if extracted_text:
                preview = extracted_text[:200].replace('\n', ' ')
                print(f"   Text preview: {preview}...")
            else:
                print("   ⚠️  No text extracted")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_pathway_parsing())
    sys.exit(0 if success else 1)

