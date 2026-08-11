"""
loader.py -- PDF loader for the Constitution of Pakistan RAG pipeline.

CHANGE LOG / ISSUE RECORD

Originally this used:
    from langchain_community.document_loaders import PyMuPDFLoader

Issue found: PyMuPDFLoader (and PyMuPDF's page.get_text() underneath it returns plain flattened text 
with no font-size information.

This PDF has footnote superscript numbers set in 8pt font sitting immediately before real article numbers 
set in 12pt font, with no space between them. Because get_text() flattens everything into one text stream.

This is not fixable by cleaning the text after extraction.
Interface kept identical to the original PyMuPDFLoader version

"""

from pathlib import Path
import pdfplumber
from langchain_core.documents import Document

PDF_PATH = Path("data/raw/Pakistan_Constitution.pdf")

# Anything below this size is footnote/superscript text 
MIN_FONT_SIZE = 9


def LoadConstitution(PDF_Path):
    documents = []
    with pdfplumber.open(str(PDF_Path)) as pdf:
        doc_meta = {k.lower(): v for k, v in (pdf.metadata or {}).items()}
        base_metadata = {
            "source": str(PDF_Path),
            "file_path": str(PDF_Path),
            "total_pages": len(pdf.pages),
            **doc_meta,
        }

        for page_number, page in enumerate(pdf.pages):
            words = [
                w for w in page.extract_words(extra_attrs=["size"])
                if w["size"] >= MIN_FONT_SIZE
            ]
            if not words:
                documents.append(Document(
                    page_content="",
                    metadata={**base_metadata, "page": page_number},
                ))
                continue            
            rows = {}
            for w in words:
                rows.setdefault(round(w["top"], 1), []).append(w)
            lines = []
            for top in sorted(rows):
                row = sorted(rows[top], key=lambda w: w["x0"])
                lines.append(" ".join(w["text"] for w in row))

            documents.append(Document(
                page_content="\n".join(lines),
                metadata={**base_metadata, "page": page_number},
            ))
    return documents


if __name__ == "__main__":
    documents = LoadConstitution(PDF_PATH)

    print("PDFPLUMBER LOADER (FONT-SIZE FILTERED) - CONSTITUTION OF PAKISTAN")
    print(f"\nTotal documents/pages loaded: {len(documents)}")

    for document in documents[0:2]:
        print("\n" + "-" * 60)
        print(document.metadata)

        print("\nTEXT")
        print(document.page_content[:1500])
        print("\n")