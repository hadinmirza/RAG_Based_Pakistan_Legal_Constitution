🇵🇰 RAG-Based Pakistan Legal Constitution Assistant

An end-to-end Retrieval-Augmented Generation (RAG) system designed to answer questions about the Constitution of Pakistan using the constitutional text as its knowledge source.

The project focuses on building a legally grounded RAG pipeline rather than relying on an LLM's general knowledge. The system extracts and structures the Constitution, creates semantically searchable embeddings, stores them in a persistent vector database, retrieves relevant constitutional provisions, generates answers using an LLM, verifies citations, detects out-of-scope questions, and exposes the final system through a lightweight web interface.

📌 Project Overview

The goal of this project is to build a Pakistan Legal Constitution RAG Assistant capable of answering questions such as:

What does Article 25 say about equality?

What is the right to fair trial?

Who is eligible to become President?

What does Article 50 say about Parliament?

The system retrieves relevant constitutional articles before generating an answer.

This is important for a legal RAG system because the LLM should not freely invent legal information. Instead, it is given retrieved excerpts from the Constitution and instructed to answer only from those excerpts.

The final architecture follows:

Constitution PDF
       ↓
PDF Ingestion
       ↓
PDF Inspection
       ↓
Text Extraction
       ↓
Structure-Aware Parsing
       ↓
Structure-Aware Chunking
       ↓
Document Embeddings
       ↓
ChromaDB Vector Store
       ↓
Semantic Retrieval
       ↓
Out-of-Scope Detection
       ↓
LLM Answer Generation
       ↓
Citation Extraction & Verification
       ↓
Flask Web UI

🎯 Problem Statement

Legal documents are large, highly structured, and sensitive to context.

A general-purpose LLM may know some information about the Constitution of Pakistan, but relying directly on its internal knowledge can introduce:

hallucinations

outdated information

unsupported claims

incorrect Article references

answers that are not grounded in the actual source document

The objective of this project is therefore to build a system where answers are grounded in the actual Constitution of Pakistan PDF.

The system should:

Understand the structure of the Constitution.

Retrieve relevant constitutional provisions.

Generate answers only from retrieved content.

Provide Article-level citations.

Refuse questions outside the scope of the Constitution.

Handle questions where the retrieved context does not contain enough information.

❓ Business / System Question

Can a RAG system reliably answer questions about the Constitution of Pakistan by retrieving the relevant constitutional provisions and grounding LLM-generated answers in those provisions?

🧠 Why RAG?

Traditional LLM usage:

User Question
     ↓
LLM
     ↓
Answer

This allows the model to rely on its pretrained knowledge.

This project instead uses:

User Question
     ↓
Query Embedding
     ↓
Vector Search
     ↓
Relevant Constitutional Articles
     ↓
LLM + Retrieved Context
     ↓
Grounded Answer + Citation

The retrieved Constitution becomes the source of truth for the answer.

📄 Dataset

The project uses the Constitution of Pakistan as the primary knowledge source.

The source PDF is a structured legal/government document containing:

Parts

Chapters

Articles

Clauses

Sub-clauses

Schedules

Constitutional text and amendments

The PDF contains a selectable text layer, so OCR was not required.

During inspection, the document was found to contain approximately:

176 pages

74,596 words

451,758 characters

~423.84 average words per page

The inspection also identified major structural patterns including Parts, Chapters, Articles, Schedules, and the Preamble.

🛠️ Complete Development Journey

This project was not built as a single-pass pipeline. Several important implementation problems were discovered while processing the actual Constitution PDF.

Understanding those problems was an important part of the project because the quality of every downstream RAG component depends on the quality of the original document extraction.

1. PDF Ingestion

The first stage was loading the Constitution PDF into the system.

Different PDF extraction approaches were investigated and tested.

The initial loader produced text, but deeper inspection showed that the extracted text contained structural problems.

The project therefore did not immediately assume that the first successful PDF load meant that the ingestion stage was correct.

2. PDF Inspection

After loading the PDF, the document was inspected to understand:

page count

word count

character count

page-level text

document structure

Parts

Chapters

Articles

Schedules

formatting patterns

repeated footer content

superscript/footnote behavior

This inspection was essential because the Constitution is not a simple block of prose.

It contains legal hierarchy such as:

PART
 └── CHAPTER
      └── ARTICLE
           ├── Clause
           ├── Sub-clause
           └── Explanation

The inspection stage revealed that naive text extraction could corrupt important legal structure.

⚠️ Major Loader Problem

One of the most difficult problems in the project occurred during parser development.

The initial parser repeatedly produced incorrect Article numbers and structure.

For example, a real Article number could become something similar to:

11. The Republic and its territories

instead of:

1. The Republic and its territories

The reason was not simply a bad regular expression.

The PDF contained:

small-font superscript/footnote markers

footer annotations

amendment markers

text with different font sizes

The initial loader flattened these elements into ordinary text.

As a result, the parser was receiving already-corrupted input.

This led to repeated parser debugging and several iterations before the actual root cause was identified.

🔄 Loader Replacement

The investigation showed that the loader needed to preserve more information about the PDF's text representation.

The project therefore moved away from the initial high-level extraction approach and ultimately selected:

pdfplumber

pdfplumber provided access to PDF character-level information such as font size, which made it possible to distinguish small superscript/footnote text from normal article text.

The final extraction strategy filtered problematic small-font content before structural parsing.

This significantly improved Article detection.

🧩 Structure-Aware Parsing

After resolving the loader problem, a custom Constitution structure parser was implemented.

The parser identifies constitutional hierarchy and associates Articles with their corresponding:

Part

Chapter

Article number

Article title

Page range

Article text

The resulting structured representation allows downstream chunking and retrieval to retain legal context.

Example:

Article 10A
Part: PART II
Chapter: CHAPTER 1
Title: Right to fair trial
Pages: ...

The final parser detected:

Articles detected: 326

The Constitution's source/table-of-contents structure contains a slightly different total because of omitted/edge-case entries, so the parser output was validated against the document rather than blindly trusting a single count.

✂️ Structure-Aware Chunking

Why structure-aware chunking?

Several chunking strategies were studied before selecting the final approach.

Method

Meaning Awareness

Structure Preservation

Speed

Typical Use

Fixed-size

❌

❌

⭐⭐⭐⭐⭐

Simple baseline

Fixed + overlap

❌

❌

⭐⭐⭐⭐⭐

General RAG

Sentence

Somewhat

⭐⭐

⭐⭐⭐⭐

Articles/prose

Paragraph

Somewhat

⭐⭐⭐

⭐⭐⭐⭐

Reports/books

Recursive

Somewhat

⭐⭐⭐⭐

⭐⭐⭐⭐

General RAG

Semantic

✅

⭐⭐⭐⭐

⭐⭐

Complex prose

Structure-aware

Depends

⭐⭐⭐⭐⭐

⭐⭐⭐⭐

Legal documents

Markdown/HTML

Depends

⭐⭐⭐⭐⭐

⭐⭐⭐⭐

Documentation

Hierarchical

✅

⭐⭐⭐⭐⭐

⭐⭐⭐

Large structured documents

Parent-child

✅

⭐⭐⭐⭐⭐

⭐⭐⭐

Precise retrieval + context

Sliding window

❌

⭐⭐⭐

⭐⭐⭐⭐

Context-heavy text

LLM-based

✅✅

⭐⭐⭐⭐⭐

⭐

Complex documents

For this project, structure-aware chunking was selected because the Constitution already has a meaningful legal hierarchy.

Most Articles are small enough to remain a single chunk.

Very large Articles were split into multiple chunks while retaining:

Article number

Article title

Part

Chapter

chunk index

total number of chunks

This means a chunk does not lose its constitutional identity after being separated from the original Article.

Chunking Challenges

Chunking itself required additional debugging.

Some Articles contained:

very large amounts of text

nested clauses

sub-level legal structure

explanations

raw/unprocessed extracted content

The chunking implementation therefore required several iterations to correctly handle large Articles while maintaining useful legal context.

Final result:

Articles: 326
Chunks:   488

Articles split into multiple chunks:

80

Example:

Article 8
    ↓
art-8-1
art-8-2

Each chunk retains contextual information such as:

Article 8: Laws inconsistent with or in derogation of Fundamental Rights to be void
(PART II | CHAPTER 1)
[part 1/2]

🧮 Embeddings

After structured chunking, the 488 chunks were converted into vector representations.

Selected Embedding Model

BAAI/bge-small-en-v1.5

The model was selected after researching and comparing embedding approaches for the project.

Why BGE-small?

The project contains a relatively small number of chunks and the individual chunks are not excessively large.

Therefore, a smaller embedding model provided a practical balance between:

semantic retrieval quality

computational requirements

local execution

model size

simplicity

cost

It was also suitable for running locally without depending on a paid embedding API.

Embedding Configuration

Model:
BAAI/bge-small-en-v1.5

Embedding dimension:
384

Device:
CPU

Normalization:
Enabled

The model was used for document embeddings and the appropriate query instruction was applied during query embedding:

Represent this sentence for searching relevant passages:

Embedding Output

The final embedding generation produced:

Chunks loaded: 488
Embeddings shape: (488, 384)

The embeddings were stored in:

data/embeddings/embeddings.npy

Metadata was stored in:

data/embeddings/metadata.json

The metadata preserves the mapping between embedding rows and their original chunks.

🗄️ Vector Database

ChromaDB

The project uses ChromaDB as the persistent vector database.

The vector store contains:

Collection:
pakistan_constitution

Vectors:
488

Distance:
Cosine

The database is persisted locally at:

data/chroma_db

Why ChromaDB?

ChromaDB was selected because it provides a simple local persistent vector-store workflow suitable for this project.

Important advantages for this implementation include:

persistent local storage

direct vector similarity search

metadata storage

metadata filtering

simple Python integration

easy integration with locally generated embeddings

no external vector database infrastructure required

This was especially useful because the project needs both semantic similarity and constitutional metadata such as:

article
part
chapter
title
page_start
page_end
chunk_id

For example, retrieval can be restricted to:

PART II

while still performing semantic search inside that subset.

🔎 Semantic Retrieval

The retrieval layer converts the user's question into an embedding and searches ChromaDB for the most semantically relevant constitutional chunks.

Default retrieval:

Top K = 5

Each result includes:

chunk ID

Article

title

Part

Chapter

text

vector distance

Example query:

right to fair trial

Retrieved result:

Article 10A: Right to fair trial
distance = 0.1539

Other semantically related results may also be retrieved.

Metadata Filtering

The retrieval system also supports filtering.

Example:

part = PART II

This allows a query to search only within a specific constitutional Part.

Example:

Query:
right to fair trial

Filter:
PART II

The system correctly retrieved:

Article 10A
Article 25
Article 26
Article 36
Article 19A

🤖 LLM Answer Generation

The retrieved constitutional context is passed to an LLM.

LLM Provider

The project uses:

Groq API

with:

Llama 3.3 70B Versatile

Note: the project uses Groq as the API provider. "Grok" and "Groq" are different technologies.

Grounding Prompt

The system uses a legal-assistant system prompt instructing the model to:

answer questions about the Constitution of Pakistan

use only provided Article excerpts

avoid unsupported information

explicitly say when the excerpts do not contain the answer

cite the Article numbers used

Conceptually:

User Question
      +
Retrieved Constitutional Context
      ↓
Llama 3.3 70B
      ↓
Grounded Legal Answer

This prevents the LLM from being treated as the primary knowledge source.

📚 Citation Verification

A dedicated citation layer was implemented.

The system extracts Article references from the generated answer and checks whether those Articles actually existed in the retrieved sources.

For example:

LLM Answer:
According to Article 10A...

The citation layer checks:

Article 10A
      ↓
Was Article 10A retrieved?
      ↓
YES
      ↓
Valid citation

If the LLM cites an Article that was not among the retrieved sources, it is recorded as a potentially hallucinated citation.

The final response can therefore expose:

answer
citations
hallucinated_citations
sources

Example successful output:

According to Article 10A, for the determination of his civil rights
and obligations or in any criminal charge against him, a person shall
be entitled to a fair trial and due process.

Citations:

- Article 10A: Right to fair trial

🛡️ Out-of-Scope Question Detection

A legal assistant should not attempt to answer arbitrary questions.

For example:

What is the best recipe for chicken biryani?

is not a constitutional question.

The project therefore implements a two-level scope-control mechanism.

Level 1 — Pre-LLM Distance Threshold

A similarity-distance threshold of:

0.45

is applied during retrieval.

If a query is sufficiently far from the constitutional knowledge base, it is rejected before the LLM is called.

The user receives:

This question does not appear to be covered by the Constitution of Pakistan.
I can only answer questions based on its content.

This prevents unnecessary LLM calls for obviously unrelated queries.

Level 2 — LLM-Level Scope Handling

Some questions can be close enough to legal/government language to pass the distance threshold even though the retrieved Articles do not actually answer the question.

For example:

What are the visa requirements to travel to Pakistan?

Such a question may retrieve constitutionally related material without actually containing the required answer.

The LLM is therefore instructed to refuse unsupported questions when the retrieved excerpts do not contain the answer.

This creates two separate protection layers:

                    User Query
                         ↓
                Similarity Check
                  /            \
             Too far          Close enough
               ↓                    ↓
         Reject directly       Retrieve context
                                    ↓
                                  LLM
                              /          \
                       Answer exists   Answer absent
                            ↓               ↓
                         Answer          Refuse

🧪 Evaluation

A dedicated evaluation script was implemented to test both normal constitutional questions and out-of-scope questions.

In-Scope Evaluation

The system was tested on:

What does the constitution say about the right to fair trial?
What is the state religion of Pakistan?
Who is eligible to become President?
What does Article 25 say about equality?
What is high treason under the constitution?

Expected Articles:

10A
2
41
25
6

Result:

5/5 passed

This confirms that the tested legal queries retrieved and cited their expected Articles.

Pre-LLM Out-of-Scope Evaluation

The following unrelated queries were tested:

What is the best recipe for chicken biryani?
Who won the last cricket world cup?
What is the weather like in Lahore today?

All three were rejected using the distance threshold before reaching the LLM.

Result:

3/3 rejected

LLM-Level Out-of-Scope Evaluation

Queries that were closer to legal/government language were also tested:

What is Pakistan's current interest rate set by the central bank?
What are the visa requirements to travel to Pakistan?

The first was successfully rejected at the LLM level.

The visa query exposed a remaining limitation in the current system because it was able to produce retrieved constitutional citations even though the question itself was outside the Constitution's scope.

This is an important evaluation finding rather than something hidden from the results.

📊 Current Evaluation Summary

Evaluation Category

Result

In-scope legal queries

5/5 passed

Clearly unrelated queries

3/3 rejected pre-LLM

Ambiguous / legal-adjacent out-of-scope queries

1/2 rejected at LLM level

The evaluation demonstrates that the core retrieval and citation pipeline works correctly for tested constitutional queries, while also identifying an area for further improvement in scope classification.

🖥️ Web Interface

A lightweight web interface was developed using:

Flask

HTML

CSS

JavaScript

The UI is intentionally simple and focuses on interacting with the RAG pipeline rather than adding unnecessary frontend complexity.

The user can enter a constitutional question and receive:

generated answer

Article citation

grounded response

refusal for clearly out-of-scope questions

Example interface introduction:

Assalam-o-Alaikum!
Ask me anything about the Constitution of Pakistan —
e.g. "What does Article 25 say about equality?"

💬 Example Queries and Results

Example 1 — Direct Article Query

Query

article 50

Answer

According to Article 50, the Majlis-e-Shoora (Parliament) of Pakistan
consists of the President and two Houses: the National Assembly and
the Senate. (Article 50)

Citation:

Article 50

Example 2 — Article Summary

Query

Article 40

The system retrieved Article 40 and generated a summary covering the State's objectives regarding:

relations with Muslim countries

common interests of peoples in Asia, Africa and Latin America

international peace and security

goodwill among nations

peaceful settlement of international disputes

Citation:

Article 40

Example 3 — Asking for Multiple Articles

Query

I need a summary from Article 60 to Article 65

The system correctly recognized the limitation of the retrieved context when only Article 60 was available.

It responded that the provided excerpt only contained Article 60 and therefore could not summarize Articles 61–65.

This is an important grounding behavior:

Retrieved context ≠ requested range
        ↓
Do not invent missing Articles
        ↓
State the limitation

Example 4 — Out-of-Scope Question

Query

Can I become a Hokage?

Response

This question does not appear to be covered by the Constitution of Pakistan.
I can only answer questions based on its content.

The query is rejected because it is outside the constitutional knowledge domain.

Example 5 — Constitutionally Relevant Question

Query

Can I become an MPA?

The system retrieved relevant constitutional provisions and used Articles including Article 62 and Article 273 to explain that eligibility depends on constitutional qualifications and disqualifications.

The system also avoided claiming a definitive personal eligibility decision because personal information such as age, citizenship, and voter enrollment was not provided.

This demonstrates the importance of separating:

What the Constitution says

from:

Whether a specific individual satisfies those requirements

⚠️ Known Limitations

The current system is a retrieval-grounded legal assistant, not a full legal reasoning engine.

1. Global document questions

Questions such as:

How many total Articles are there in the Constitution?

can be problematic because the answer may depend on document-level metadata rather than a single retrieved Article.

The current RAG pipeline is primarily optimized for:

Question
→ Relevant constitutional passage
→ Grounded answer

rather than:

Question
→ Global aggregation over the entire document

A future metadata-aware query layer could solve this.

2. Multi-Article range queries

A query such as:

Summarize Articles 40 to 55

may retrieve only a subset of the requested range.

The system correctly avoids fabricating missing Articles, but a future implementation could explicitly detect Article ranges and perform targeted retrieval for every requested Article.

3. Scope classification

The current distance threshold is useful for clearly unrelated questions but cannot perfectly determine whether a question is legally answerable.

A query can be semantically close to constitutional language while still being outside the Constitution.

The current architecture therefore combines:

Vector distance filtering
+
LLM grounding/refusal

A dedicated classifier or stronger retrieval validation layer could further improve this.

4. Citation verification is retrieval-based

The citation system verifies whether an Article cited by the LLM was present in the retrieved results.

This reduces unsupported citations, but citation verification does not independently prove that every statement in the answer is legally correct.

5. Source version dependency

The answers are grounded in the Constitution PDF used during ingestion.

If the source document is replaced with a newer constitutional version, the ingestion, parsing, chunking, embeddings, and vector database should be regenerated.

🏗️ Project Architecture

                         ┌──────────────────────┐
                         │ Constitution of      │
                         │ Pakistan PDF         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ PDF Ingestion        │
                         │ pdfplumber            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ PDF Inspection       │
                         │ Structure Analysis   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Structure Parser     │
                         │ Part / Chapter /     │
                         │ Article / Pages      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Structure-Aware      │
                         │ Chunking             │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ BGE-small-en-v1.5    │
                         │ 384-D Embeddings     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ ChromaDB             │
                         │ Persistent Vector DB │
                         └──────────┬───────────┘
                                    │
                           User Question
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Query Embedding      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Scope / Distance     │
                         │ Detection             │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Top-K Retrieval      │
                         │ + Metadata Filter    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Groq API             │
                         │ Llama 3.3 70B        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Citation Extraction  │
                         │ & Verification       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Flask Web UI         │
                         └──────────────────────┘

📁 Project Structure

RAG/
│
├── data/
│   ├── raw/
│   │   └── Constitution PDF
│   │
│   ├── processed/
│   │   └── constitution_chunks.json
│   │
│   ├── embeddings/
│   │   ├── embeddings.npy
│   │   └── metadata.json
│   │
│   └── chroma_db/
│       └── Persistent ChromaDB storage
│
├── src/
│   │
│   ├── ingestion/
│   │   ├── pdf_loader.py
│   │   ├── inspect_pdf.py
│   │   └── final_loader.py
│   │
│   ├── processing/
│   │   └── structured_parser.py
│   │
│   ├── chunking/
│   │   └── chunk.py
│   │
│   ├── embedding/
│   │   └── embedding.py
│   │
│   ├── Vectors/
│   │   └── vector.py
│   │
│   ├── retrieval/
│   │   └── retrieval.py
│   │
│   ├── LLM/
│   │   └── LLM.py
│   │
│   ├── citations/
│   │   └── citation.py
│   │
│   ├── Scope/
│   │   └── scope.py
│   │
│   └── Evaluation/
│       └── Evaluation.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
├── app.py
├── README.md
└── .gitignore

🧰 Technologies Used

Programming

Python

HTML

CSS

JavaScript

PDF / Document Processing

pdfplumber

PDF text extraction

custom structural parsing

RAG / NLP

LangChain HuggingFace integration

Sentence Transformers

BAAI/bge-small-en-v1.5

semantic vector retrieval

Vector Database

ChromaDB

LLM

Groq API

Llama 3.3 70B Versatile

Backend / UI

Flask

HTML

CSS

JavaScript

Development

VS Code

Git

GitHub

Python virtual environment

🔐 Environment Variables

The Groq API key is loaded through environment variables.

Create a .env file:

GROQ_API_KEY=your_api_key_here

The application loads it using:

from dotenv import load_dotenv

load_dotenv()

The API key should never be committed to GitHub.

🚀 Installation

Clone the repository:

git clone <repository-url>
cd RAG

Create a virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Install the required dependencies:

pip install pdfplumber numpy chromadb langchain-huggingface sentence-transformers groq python-dotenv flask

Set the Groq API key in .env.

▶️ Running the Pipeline

The project is divided into feature-level stages.

1. Inspect the PDF

python src/ingestion/inspect_pdf.py

This helps analyze:

pages

text

structure

formatting

Articles

document characteristics

2. Run the Final Loader

python src/ingestion/final_loader.py

The final loader uses pdfplumber to extract the PDF while handling the formatting issues discovered during development.

3. Parse the Constitution

python src/processing/structured_parser.py

This creates structured constitutional Articles.

4. Create Chunks

python src/chunking/chunk.py

This generates the structure-aware chunks.

Output:

326 Articles
488 Chunks

5. Generate Embeddings

python src/embedding/embedding.py

Output:

Embeddings shape: (488, 384)

6. Build the Vector Database

python src/Vectors/vector.py

This indexes the embeddings in persistent ChromaDB.

7. Test Retrieval

python src/retrieval/retrieval.py

Example:

Query: right to fair trial

Article 10A: Right to fair trial
distance = 0.1539

8. Test LLM Generation

python -m src.LLM.LLM

The LLM receives retrieved constitutional context and generates a grounded answer.

9. Test Citations

python -m src.citations.citation

This extracts and verifies Article citations.

10. Run Evaluation

python -m src.Evaluation.Evaluation

This tests:

in-scope legal queries

clearly unrelated queries

legal-adjacent out-of-scope queries

expected Article citations

scope rejection behavior

11. Run the Web Application

python app.py

Then open the local Flask application in a browser.

📈 Key Project Results

The completed pipeline currently demonstrates:

PDF
 ↓
Structured extraction
 ↓
326 detected Articles
 ↓
488 structure-aware chunks
 ↓
488 × 384 embeddings
 ↓
Persistent ChromaDB index
 ↓
Semantic retrieval
 ↓
Groq + Llama 3.3 70B
 ↓
Citation extraction + verification
 ↓
Scope detection
 ↓
Flask UI

The tested retrieval pipeline successfully identified Article 10A for:

right to fair trial

with a cosine distance of approximately:

0.1539

🧪 Example End-to-End Flow

User asks:

What does the constitution say about the right to fair trial?

Step 1 — Query embedding

The question is converted into a 384-dimensional vector.

Step 2 — Scope check

The query is compared against the constitutional vector space.

Step 3 — Retrieval

ChromaDB retrieves the most relevant chunks.

Top result:

Article 10A
Right to fair trial

Step 4 — Context construction

The retrieved Article excerpts are assembled into an LLM context.

Step 5 — LLM generation

Llama 3.3 70B receives the context and question.

Step 6 — Grounded answer

The model produces:

According to Article 10A, for the determination of his civil rights
and obligations or in any criminal charge against him, a person shall
be entitled to a fair trial and due process.

Step 7 — Citation verification

The system detects:

Article 10A

and confirms that Article 10A was actually retrieved.

Step 8 — UI response

The Flask frontend displays the answer and Article citation.

🧠 Key Engineering Decisions

Why structure-aware chunking?

Because the Constitution already has a meaningful hierarchy.

Breaking an Article at arbitrary character boundaries could separate:

Article
+
Clause
+
Explanation

and make retrieval less meaningful.

Structure-aware chunking preserves legal context.

Why BGE-small?

The dataset contains only 488 final chunks and the chunks are relatively manageable in size.

A compact local embedding model was therefore sufficient and practical.

It avoided unnecessary dependency on a paid embedding service.

Why ChromaDB?

The project required:

persistent local storage

vector similarity search

metadata

metadata filtering

easy Python integration

ChromaDB provided these capabilities without requiring a separate hosted vector infrastructure.

Why an LLM after retrieval?

The vector database is good at finding relevant text, but it does not naturally produce a conversational answer.

Therefore:

Retriever
→ Finds evidence

LLM
→ Explains evidence

The LLM is constrained by the retrieved context instead of being allowed to freely answer from general knowledge.

Why citation verification?

A RAG system can still have an LLM cite an Article that was not actually retrieved.

Citation verification adds another validation layer:

LLM citation
      ↓
Compare with retrieved Articles
      ↓
Valid / potentially hallucinated

⚠️ Major Challenges Faced

This project involved several significant implementation challenges.

1. PDF extraction problems

The initial loader merged superscript/footnote text with normal Article text.

This corrupted Article numbers and headings.

2. Parser development

The custom legal parser was one of the most difficult implementation stages.

The parser repeatedly generated incorrect structure and Article numbers.

Understanding why the parser was failing required substantial debugging and research.

3. Loader root-cause investigation

A major discovery was that the parser was not always the actual source of the problem.

The parser was receiving corrupted text from the PDF extraction stage.

This required changing the loader rather than continuing to add increasingly complex regex rules.

4. Rebuilding the parser

After switching to pdfplumber, the parser had to be rebuilt/adjusted to work with the corrected extraction output.

5. Structure-aware chunking

Large Articles and nested legal structures created additional chunking problems.

The chunking implementation required multiple iterations to preserve context while still producing retrievable chunks.

6. Out-of-scope detection

The initial distance threshold was too permissive.

A value around:

0.60

allowed too many unrelated questions to reach the LLM.

The threshold was reduced to:

0.45

which improved pre-LLM rejection of clearly unrelated queries.

However, legal-adjacent questions still require the second LLM-level protection layer.

7. Grounding limitations

Some simple document-level questions do not map naturally to a single retrieved Article.

For example:

How many total Articles are there?

requires document-level metadata rather than ordinary semantic retrieval.

This remains an area for future improvement.

🔮 Future Improvements

Possible improvements include:

1. Better document-level query handling

Add a metadata/query layer for questions involving:

Article counts

Part counts

Chapter counts

page ranges

Article ranges

2. Better Article-range retrieval

For:

Articles 40–55

detect the requested range and directly retrieve the corresponding Articles instead of relying entirely on semantic similarity.

3. Improved scope classifier

Add a dedicated classifier or legal-domain intent detector before retrieval.

4. Better citation presentation

Return richer citations containing:

Article
Title
Part
Chapter
Page
Chunk

and potentially link the citation to the original source page.

5. Retrieval evaluation

Build a larger benchmark containing:

direct Article questions

paraphrased questions

misspelled questions

multi-Article questions

ambiguous legal questions

out-of-scope questions

6. Retrieval metrics

Future evaluation can include:

Recall@K

Precision@K

MRR

citation accuracy

groundedness

answer relevance

refusal accuracy

7. Improved UI

The current UI is intentionally simple.

Future versions could include:

source cards

Article navigation

page references

expandable retrieved context

conversation history

loading indicators

better error handling

📚 What I Learned

This project provided practical experience across the complete RAG lifecycle.

Document Engineering

PDF ingestion

PDF inspection

text extraction

font-level extraction issues

legal document structure

custom parsing

RAG

chunking strategies

structure-aware chunking

embeddings

query embeddings

vector databases

semantic retrieval

metadata filtering

context construction

LLM Integration

Groq API

Llama 3.3 70B

system prompts

grounded generation

refusal behavior

Reliability

citation extraction

citation verification

hallucination detection

scope detection

evaluation testing

Software Engineering

modular project structure

feature-based development

debugging

Git/GitHub workflow

environment variables

Flask integration

📝 Development Milestones

The project progressed through the following major milestones:

1. Project / dataset selection
        ↓
2. PDF ingestion
        ↓
3. PDF inspection
        ↓
4. Loader experimentation
        ↓
5. Structure-aware chunking research
        ↓
6. Custom Constitution parser
        ↓
7. Parser debugging
        ↓
8. Loader root-cause discovery
        ↓
9. pdfplumber final loader
        ↓
10. Parser adjustment
        ↓
11. Structure-aware chunking
        ↓
12. Embedding model research
        ↓
13. BGE-small selection
        ↓
14. Embedding generation
        ↓
15. ChromaDB vector indexing
        ↓
16. Semantic retrieval
        ↓
17. LLM integration
        ↓
18. Citation extraction & verification
        ↓
19. Scope detection
        ↓
20. Evaluation
        ↓
21. Flask web UI

📌 Current Project Status

The core RAG pipeline has been implemented:

✅ PDF ingestion

✅ PDF inspection

✅ Final PDF loader

✅ Constitution structure parser

✅ Structure-aware chunking

✅ Embedding generation

✅ ChromaDB vector database

✅ Semantic retrieval

✅ Metadata filtering

✅ LLM answer generation

✅ Citation extraction

✅ Citation verification

✅ Out-of-scope detection

✅ Evaluation framework

✅ Flask web UI

Remaining work is mainly refinement, testing, documentation, and improving edge cases rather than building the core RAG pipeline from scratch.

👨‍💻 Author

Muhammad Hadin Mirza

Computer Engineering Student

AI / Machine Learning / RAG Enthusiast

This project was developed as a practical end-to-end RAG project focused on applying modern retrieval and LLM techniques to a structured legal document.