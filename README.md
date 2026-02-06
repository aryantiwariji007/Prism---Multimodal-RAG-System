# Prism RAG Architecture Documentation

**Version:** 2.1.0-Internal  
**Status:** Production (On-Prem)  
**Classification:** INTERNAL AGENTIC ARCHITECTURE  
**Owner:** Enterprise Platform Team

---

# Project Overview

Prism is an enterprise-grade, local-first Retrieval-Augmented Generation (RAG) system designed for high-recall retrieval across complex corporate knowledge bases. Unlike standard RAG implementations that maximize speed at the cost of accuracy, Prism prioritizes **recall sufficiency** and **data determinism**.

The system operates entirely on-premise, utilizing specific embedding hierarchies and agentic loops to handle multimodal documents, with a specialized engine for tabular data preservation.

# High-Level Architecture

The architecture follows a strict **Split-Merge-Route** pattern, ensuring that ingestion and retrieval are decoupled but share a unified vector definition.

```ascii
[Documents] --> [Ingestion Pipeline] --> [Splitter/Router]
                                              |
                        +---------------------+---------------------+
                        |                     |                     |
                  [Text Chunks]        [Table Objects]       [Visual Nodes]
                        |                     |                     |
                  [Qdrant Dense]        [DuckDB SQL]        [Qdrant Sparse]
                  [+ Sparse IX]               |                     |
                        |                     +---------------------+
                        |                                |
                        +-----> [Retrieval Nexus] <------+
                                       |
                              [Hybrid Search + RRF]
                                       |
                              [Re-ranking Layer]
                                       |
                                [Generative Agent] --> [User]
```

### Core Components
1.  **Ingestion Service**: A multi-stage processing reactor that classifies, chunks, and enriches content.
2.  **Vector Store (Qdrant)**: Stores hybrid vectors (Dense `instructor-xl` + Sparse `BM25`).
3.  **Tabular Engine (DuckDB)**: A dedicated SQL-based tabular storage for structured querying.
4.  **Retrieval Agent (QA Service)**: Orchestrates query rewriting, routing, and synthesis.

# Core Design Principles

### 1. Recall-First Engineering
We accept higher ingestion latency to ensure maximum retrieval accuracy. Every document undergoes "deep parsing"—tables are not treated as text but as structural objects.

### 2. Deterministic Execution
The system eschews probabilistic "magic" where possible. Chunk identification, metadata injection, and routing logic are hard-coded rules, ensuring that if a document exists, it is mathematically retrievable.

### 3. Local-First Sovereignty
All components (Embeddings, LLM, Vector Database, OCR) run within the network boundary. No external API calls are made, guaranteeing zero data leakage.

# Ingestion Pipeline

The ingestion process is **synchronous** and **blocking** by design during the critical path, ensuring atomic write consistency.

### Synchronous Ingestion
We utilize an "Ultra-fast Synchronous" architecture rather than a background job queue for user-facing uploads.
- **Rationale**: Background queues introduce state uncertainty ("Is my file ready?"). By keeping the primary ingestion path synchronous but parallelized via thread pools, we provide immediate "Read-to-Query" confirmation to the user.
- **Parallelization**: Parsing occurs on CPU threads while embedding generation is batched on the GPU, maximizing hardware saturation without blocking the HTTP response indefinitely.

### Chunking Strategy
Standard fixed-window chunking fails on enterprise documents.
- **Recursive Character Chunking**: Used for unstructured text to preserve semantic boundaries.
- **Context Injection**: Every chunk is prepended with `Filename: [Name] \n File ID: [ID]`. This "Metadata rescue" technique enables the model to associate disparate chunks with their parent document during retrieval.

### OCR Alignment & Enrichment
Ingestion uses a two-stage pass:
1.  **Pass 1 (Fast)**: Extracts raw text.
2.  **Pass 2 (Enrichment)**: If text density is <1000 characters (indicating a scan), we trigger the **OCR Enrichment Layer**. 
    - Uses **PaddleOCR** for high-fidelity text.
    - Falls back to **LLaVA (Vision LLM)** for complex layout analysis.

### Metadata Enrichment
Metadata is not secondary; it is a primary retrieval vector. Every chunk carries strict schema tags (`doc_id`, `source_file`, `ingestion_method`). This allows the vector engine to perform pre-filtering before semantic search, drastically reducing part-of-speech confusion.

# Retrieval Pipeline

Retrieval is handled by an agentic orchestrator that creates a "Retrieval Plan" before executing searches.

### Hybrid Retrieval
We do not rely solely on dense vector similarity.
- **Dense**: `hkunlp/instructor-xl` captures semantic intent.
- **Sparse**: `BM25` captures exact keyword matches (vital for part numbers, IDs, and acronyms).
- **Fusion**: Results are merged using **Reciprocal Rank Fusion (RRF)** to normalize scores across the two spaces.

### Conditional Query Rewriting
The **Query Rewriter Agent** analyzes the user's prompt before searching.
- **Trigger**: If the query is vague (e.g., "what does it say about the cost?"), the agent rewrites it to be semantically complete (e.g., "financial cost details in Project Alpha documentation").
- **Bypass**: If the query contains specific IDs or filenames, rewriting is bypassed to prevent "hallucinated expansion."

### Global vs. Scoped Retrieval
- **Scoped**: When a folder/file is selected, strict metadata filters are applied at the database level (`filter: { must: [ { key: "folder_id", match: ... } ] }`).
- **Global**: Searches the entire manifold. Scores are penalized slightly to prefer exact matches over broad semantic similarities.

### Reranking
Retrieval fetches a wide candidate pool (k=40+). These candidates are passed to a Cross-Encoder Reranker which scores pairs of `(Query, Chunk)`. This step eliminates "nearest neighbor" vector artifacts that are semantically close but factually irrelevant.

# Tabular Data Strategy

Standard RAG fails at retrieval functionality on tables because vector embeddings destroy row-column relationships.

### The Problem
When a table is chunked as text:
```
| Year | Revenue |
| 2020 | 10M     |
```
Becomes `Year 2020 Revenue 10M`. The query "Revenue in 2020" matches, but "What was the growth?" fails because the structural logic is gone.

### Schema-Aware Indexing
We use a **Split-Routing** mechanism:
1.  **Detection**: The ingestion pipeline detects tabular structures during parsing.
2.  **Extraction**: Tables are converted into DataFrames.
3.  **Storage**: These DataFrames are stored as **SQL Tables** in DuckDB, not just vector chunks.
4.  **Metadata**: The columns are sanitized and stored as JSON metadata.

### OCR + Table Realignment
For scanned PDFs, we do not rely on raw OCR text blocks. The Vision LLM assists in reconstructing the table topology, ensuring that cell alignment is preserved before it reaches the embedding model.

# Agentic Components

The "Agent" in Prism is not a single entity but a collection of specialized functional loops:

1.  **Ingestion Controller**: Decides if a document requires OCR or standard parsing.
2.  **Router Agent**: Classifies queries as `TABULAR`, `SEMANTIC`, or `METADATA` oriented.
    - If `TABULAR`, it constructs a SQL query for DuckDB.
    - If `SEMANTIC`, it executes the Vector Search pipeline.
3.  **Sufficiency Agent**: Evaluates if the retrieved chunks actually answer the question. If not, it triggers a "step-back" prompting strategy to re-query with broader terms.

# Performance Characteristics

- **Ingestion Speed**: ~2-3 seconds per page (OCR enabled).
- **Retrieval Latency**: <1.5s (P95) for Hybrid Search + Reranking.
- **Recall**: >92% on internal benchmarks (vs ~75% for vanilla RAG).
- **Concurrency**: Thread-safe ingestion allows simultaneous uploads without blocking reads.

# Why This Architecture Works

1.  **Hybrid Search handles the "Vocabulary Gap"**: Users often query with keywords that don't semantically match embeddings. Sparse vectors capture these lexical anchors.
2.  **Dual-Store for Tables**: SQL for structure + Vectors for semantics means we don't force a "one size fits all" solution on highly structured data.
3.  **Strict Metadata**: By enforcing `folder_id` and `file_id` at the lowest database level, we prevent cross-contamination of contexts, which is critical for multi-tenant enterprise deployment.

# Future Improvements

-   **Graph RAG**: Implementation of Knowledge Graph extraction for inter-document entity relationships.
-   **Fine-tuned Embeddings**: Training `instructor-xl` adapters on specific corporate taxonomies.
-   **Streaming Ingestion**: Moving to a full streaming response architecture for massive (1000+ page) PDF ingestion.

# Internal Notes

-   **Do not modify `qdrant_service.py` collection config** without running the `reindex_all.py` script. Changing HNSW parameters requires a full rebuild.
-   **OCR**: The `prism_ocr` module depends on PaddlePaddle. Ensure CUDA drivers are verified if GPU offloading is inconsistent.
-   **DuckDB**: The tabular store is currently single-file. For high-write concurrency in the future, migrate to a server-based OLAP database.
