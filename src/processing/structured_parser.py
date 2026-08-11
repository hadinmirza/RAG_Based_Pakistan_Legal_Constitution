import re
import json
from pathlib import Path
 
import pdfplumber
from langchain_core.documents import Document
 
PDF_PATH = Path("data/raw/Pakistan_Constitution.pdf")
MIN_FONT_SIZE = 9
 
HEADING_RE = re.compile(r"^[\[\s]*(\d{1,4}[A-Z]{0,3})\.\s+(.*)$")
PART_RE = re.compile(r"^PART\s+([IVXLC]+)$", re.IGNORECASE)
CHAPTER_RE = re.compile(r"^CHAPTER\s+([\dA-Z]+)", re.IGNORECASE)
STOP_RE = re.compile(r"^\[?\s*(ANNEX|FIRST SCHEDULE)", re.IGNORECASE)
PAGE_FOOTER_RE = re.compile(r"^Page \d+ of \d+$", re.IGNORECASE)
BRACKET_MARKER_RE = re.compile(r"\d+\[")

FIRST_CLAUSE_RE = re.compile(r"\(1[A-Z]{0,3}\)\s")
TITLE_DASH_RE = re.compile(r"\.\s*[-\u2013\u2014]\s*")
ABBREVIATION_RE = re.compile(r"\b(etc|i\.e|e\.g)$", re.IGNORECASE)
 
 
def split_title_body(rest):
    """Split the text after 'Num. ' into (title, body) at the real title/body boundary."""
    # Primary signal: the opening numbered clause "(1)" / "(1A)" -- most reliable,
    # doesn't depend on the dash character having survived PDF extraction.
    clause_match = FIRST_CLAUSE_RE.search(rest)
    if clause_match:
        title = rest[:clause_match.start()]
        title = re.sub(r"[\s.\-\u2013\u2014]+$", "", title)
        return title.strip(), rest[clause_match.start():].strip()
 
    # articles with no numbered clauses (plain prose body) -- use the dash marker
    dash_match = TITLE_DASH_RE.search(rest)
    if dash_match:
        return rest[:dash_match.start()].strip(), rest[dash_match.end():].strip()
 
    # last resort: first period that isn't part of a known abbreviation
    # (e.g. "Custody, etc. of ...")
    for period_match in re.finditer(r"\.", rest):
        idx = period_match.start()
        before = rest[:idx].rstrip()
        if ABBREVIATION_RE.search(before):
            continue
        return rest[:idx].strip(), rest[idx + 1:].strip()
 
    # no boundary found at all -- treat the whole thing as title, empty body
    return rest.strip(), ""
 
 
def extract_lines_with_pages(pdf_path):
 
    result = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages):
            words = [w for w in page.extract_words(extra_attrs=["size"])
                     if w["size"] >= MIN_FONT_SIZE]
            if not words:
                continue
            rows = {}
            for w in words:
                rows.setdefault(round(w["top"], 1), []).append(w)
            for top in sorted(rows):
                row = sorted(rows[top], key=lambda w: w["x0"])
                result.append((page_number, " ".join(w["text"] for w in row)))
    return result
 
 
def find_body_start(lines):
    for i, (_, text) in enumerate(lines):
        if text.strip() == "PREAMBLE":
            for j in range(i + 1, len(lines)):
                if lines[j][1].strip().startswith("PART I"):
                    return j
    return 0
 
 
def parse_constitution(pdf_path=PDF_PATH):
 
    lines = extract_lines_with_pages(pdf_path)
    start = find_body_start(lines)
 
    records = []
    current = None
    part, chapter = None, None
 
    for page_number, line in lines[start:]:
        stripped = line.strip()
 
        if STOP_RE.match(stripped):
            break  # reached the Annex/Schedules -- stop parsing articles
 
        if PAGE_FOOTER_RE.match(stripped):
            continue  # "Page N of 176" footer -- not content
 
        if PART_RE.match(stripped):
            part = stripped
            chapter = None  # a new Part resets the chapter
            continue
 
        if CHAPTER_RE.match(stripped):
            chapter = stripped
            continue
 
        head_match = HEADING_RE.match(stripped)
        if head_match:
            if current:
                records.append(current)
            number, rest = head_match.groups()
            title, body_start_text = split_title_body(rest)
            current = {
                "article": number,
                "title": title,
                "part": part,
                "chapter": chapter,
                "page_start": page_number,
                "page_end": page_number,
                "text": body_start_text.strip(),
            }
            continue
 
        if current:
            current["text"] += " " + stripped
            current["page_end"] = page_number
 
    if current:
        records.append(current)
 
    for r in records:
        r["text"] = r["text"].replace("[", "").replace("]", "")
 
    return records
 
 
def create_documents(records):
    """Turn parsed records into LangChain Documents"""
    documents = []
    for r in records:
        content = f"Article {r['article']}: {r['title']}\n\n{r['text']}"
        documents.append(Document(
            page_content=content,
            metadata={
                "article": r["article"],
                "title": r["title"],
                "part": r["part"],
                "chapter": r["chapter"],
                "page_start": r["page_start"],
                "page_end": r["page_end"],
            },
        ))
    return documents
 
# Test
if __name__ == "__main__":
    records = parse_constitution(PDF_PATH)
 
    print("\nCONSTITUTION STRUCTURE PARSER")
    print(f"\nArticles detected: {len(records)}")
 
    print("\nFIRST 10 ARTICLES")
    for record in records[:10]:
        print(
            f"\nArticle {record['article']}"
            f" | Part: {record['part']}"
            f" | Chapter: {record['chapter']}"
        )
        print(f"Title: {record['title']}")
        print(f"Pages: {record['page_start']} - {record['page_end']}")
        print("\nText:")
        print(record["text"][:500])
 
    lengths = [(r["article"], len(r["text"])) for r in records]
    lengths.sort(key=lambda x: -x[1])
    print("\n" + "-" * 70)
    print("5 LONGEST ARTICLES (candidates for further chunking, if any)")
    for article, length in lengths[:5]:
        print(f"  Article {article}: {length} characters")
 
    structured_documents = create_documents(records)
    print(f"\nFinal structured Documents: {len(structured_documents)}")
 
    OUTPUT_PATH = Path("data/processed/constitution_articles.json")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)