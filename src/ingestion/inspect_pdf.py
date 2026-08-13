from pathlib import Path
from pypdf import PdfReader

pdf_Path =  Path("data/raw/Pakistan_Constitution.pdf")

# function to inspect the data pdf
def inspect_pdf(pdf_Path):
    print("PAKISTAN CONSTITUTION - PDF INSPECTION")

    # if file does not exit return otherwise read pdf file 
    if not pdf_Path.exists():  
        print("\n Error File Not Found")   
        return

    read = PdfReader(pdf_Path) 
    totalPages = len(read.pages)
    print(f"\nPDF: {pdf_Path.name}")
    print(f"Total pages: {totalPages}")

    page_data = [] # create empty array for each page 

    for pageNum , page in enumerate(read.pages,start=1): # start loop with page numbering starting from page 1         
        text = page.extract_text() or "" # either get text or store " " in case of empty
        text = text.strip() # only for data cleaning 

        words = text.split() # based on spaces words extracted from text
        characters = len(text) 

        page_data.append({
            "page": pageNum,
            "text": text,
            "words": len(words),
            "characters": characters
        })

    non_empty_pages = [
        page for page in page_data
        if page["text"]
    ]

    empty_pages = [
        page for page in page_data
        if not page["text"]
    ]

    totalWords = sum(page["words"] for page in page_data)
    totalCharacters = sum(page["characters"] for page in page_data)

    AvgWords = (
        totalWords / totalPages
        if totalPages > 0
        else 0
    )

    print("BASIC STATISTICS")
    print("\n")

    print(f"Total pages:          {totalPages}")
    print(f"Pages with text:      {len(non_empty_pages)}")
    print(f"Empty pages:          {len(empty_pages)}")
    print(f"Total words:          {totalWords:,}")
    print(f"Total characters:     {totalCharacters:,}")
    print(f"Average words/page:   {AvgWords:,.2f}")

    longest_page = max(  # finding longest page by counting max words in a page
        page_data,
        key=lambda page: page["words"]
    )

    shortest_non_empty_page = min( # findingshortest page by counting min words in a page
        non_empty_pages,
        key=lambda page: page["words"]
    ) if non_empty_pages else None   # in case of non empty pages only 

    if shortest_non_empty_page: # print details of shortest non empty page 
        print(
            f"Shortest non-empty page: "
            f"{shortest_non_empty_page['page']} "
            f"({shortest_non_empty_page['words']:,} words)"
        )

    if empty_pages:
        print(f"\nEmpty page numbers: {empty_pages}") # print empty page

    sample_pages = [5,10,28,39,56,100,150,176]

    print("\n SAMPLE PAGE EXTRACTION")
    print("\n")

    for page_number in sample_pages:

        if page_number > totalPages:
            continue

        page = page_data[page_number - 1]

        print(f"PAGE {page_number}")
        text = page["text"]

        if not text:
            print("[NO TEXT EXTRACTED]")
            continue

        # Print only first 1500 characters
        print(text[:1500])

        if len(text) > 1500:
            print("\n...[TRUNCATED]...")


    # STRUCTURE DETECTION
    print("\n")
    print("LEGAL STRUCTURE DETECTION")
    print("\n")

    keywords = {
        "PART": 0,
        "CHAPTER": 0,
        "ARTICLE": 0,
        "SCHEDULE": 0,
        "PREAMBLE": 0
    }

    full_text = "\n".join(
        page["text"]
        for page in page_data
    )

    upper_text = full_text.upper()
    for keyword in keywords:
        keywords[keyword] = upper_text.count(keyword)

    for keyword, count in keywords.items():
        print(f"{keyword:<12}: {count}")

    print("\n")
    print("ARTICLE DETECTION")

    article_lines = []

    for page in page_data:
        for line in page["text"].splitlines():
            line = line.strip()

            if line.startswith("Article "):
                article_lines.append(
                    (page["page"], line)
                )

    print(f"Possible article headings found: {len(article_lines)}")
    print("\nFirst 20 detected article headings:")

    for page_number, article in article_lines[:20]:
        print(f"Page {page_number}: {article}")

    # SAVE EXTRACTED TEXT
    output_dir = Path("data/processed")
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_File = output_dir / "ExtractedData.txt"

    with open(
        output_File,
        "w",
        encoding="utf-8"
    ) as file:

        for page in page_data:

            file.write(
                f"\n\n=PAGE {page['page']} =\n\n"
            )

            file.write(page["text"])

    print("\n")
    print("EXTRACTION COMPLETE")

    print(f"\nExtracted text saved to:")
    print(output_File)


if __name__ == "__main__":
    inspect_pdf(pdf_Path)

##