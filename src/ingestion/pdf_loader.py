from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader

PDF_PATH = Path("data/raw/Pakistan_Constitution.pdf")

def LoadConstitution(PDF_Path):
    loader = PyMuPDFLoader(str(PDF_Path))
    documents = loader.load()
    return documents

if __name__ == "__main__":
    documents = LoadConstitution(PDF_PATH)

    print("PYMUPDF LOADER - CONSTITUTION OF PAKISTAN")
    print(f"\nTotal documents/pages loaded: {len(documents)}")

    for document in documents[0:2]:
        print("\n" + "-" * 60)
        print(document.metadata)

        print("\nTEXT")
        print(document.page_content[:1500])
        print("\n")