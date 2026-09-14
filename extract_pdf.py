#!/usr/bin/env python3
"""Extract text from hermes-kanban-v1-spec.pdf."""
import sys

try:
    import pypdf
except ImportError:
    try:
        import PyPDF2
    except ImportError:
        try:
            from pdfminer.high_level import extract_text
        except ImportError:
            print("No PDF library available. Install pypdf, PyPDF2, or pdfminer.six")
            sys.exit(1)

pdf_path = "C:/Users/mobil/orca/projects/my 1st/docs/hermes-kanban-v1-spec.pdf"

# Try pypdf first
try:
    import pypdf
    r = pypdf.PdfReader(pdf_path)
    print(f"=== PDF EXTRACTION ===")
    print(f"Pages: {len(r.pages)}")
    print(f"Metadata: {r.metadata}")
    print()
    for i, page in enumerate(r.pages):
        text = page.extract_text()
        if text.strip():
            print(f"--- Page {i+1} ---")
            print(text)
            print()
    sys.exit(0)
except ImportError:
    pass

# Try PyPDF2
try:
    import PyPDF2
    with open(pdf_path, 'rb') as f:
        r = PyPDF2.PdfReader(f)
        print(f"=== PDF EXTRACTION ===")
        print(f"Pages: {len(r.pages)}")
        print()
        for i, page in enumerate(r.pages):
            text = page.extract_text()
            if text and text.strip():
                print(f"--- Page {i+1} ---")
                print(text)
                print()
    sys.exit(0)
except ImportError:
    pass

# Try pdfminer
try:
    from pdfminer.high_level import extract_text
    text = extract_text(pdf_path)
    print(f"=== PDF EXTRACTION ===")
    print(text)
except ImportError:
    pass
