Project: “Bulk-PDF Knowledge-Extraction” System
(Integrating LangGraph, FastAPI, LightRAG, MCP Server, Webhooks, and a Vector Database)

────────────────────────────────────────
Trigger & Orchestration Layer 
──────────────────────────────────────── 
• Storage bucket (e.g., GCS, S3, Azure Blob) is configured to emit an HTTP webhook each
time a batch of PDFs is uploaded (e.g., POST /webhook/new-batch). • FastAPI hosts the
webhook endpoint. Its handler immediately enqueues a “batch-id” message onto LangGraph,
which acts as the multi-agent orchestrator. • LangGraph instantiates the following agents
as graph nodes, passing a shared “context” object that includes the batch metadata and
pointers to common resources (vector DB handles, MCP tool registry, etc.).

────────────────────────────────────────
2. Shared Resources
────────────────────────────────────────
a. LightRAG Graph
• Implemented with LangGraph’s native graph primitives.
• Nodes: Retriever → Reranker → Merger.
• Backed by a scalable vector database (e.g., Weaviate, Qdrant, Milvus, or pgvector).
• Stores tuples: (doc_full_text, human_validated_structured_data, metadata).

b. MCP Server
• Provides a catalog of tools, prompt templates, and guardrails that LangGraph agents call through the MCP SDK (think: function-calling layer).
• Central place to version prompts and to inject retrieval callbacks automatically.

────────────────────────────────────────
3. Ingestion Phase
────────────────────────────────────────
Node: IngestionAgent

Fetch PDFs referenced in batch-id from the bucket.
For each PDF:
• Parse every page to text + page-level metadata (titles, headers, page #,
tables) using a PDF parser (e.g., pdfplumber + layoutLM fallback).
• Store raw text in an object store and emit a pdf_parsed event into the graph.

────────────────────────────────────────
4. Preliminary Retrieval
────────────────────────────────────────
Node: RetrievalAgent
• On pdf_parsed, query LightRAG with the whole document embedding OR chunk-level embeddings (configurable).
• Return top-k “gold-standard” examples as grounding context.
• Persist retrieval IDs into the context for downstream traceability.

────────────────────────────────────────
5. Automated Extraction
────────────────────────────────────────
Node: ExtractionAgent (LLM via MCP-registered tool)
Inputs: (a) parsed PDF text, (b) retrieved examples, (c) optional validator comments.
Outputs (single JSON payload):
• draft_structured_data
• confidence_score (0-1)
• change_log (Δ vs. grounding examples)
• iteration_count

────────────────────────────────────────
6. Human-in-the-Loop Validation Loop
────────────────────────────────────────
Node: ValidationRouter
• Routes the draft to a human UI (we are not interested in the UI).
• FastAPI supplies endpoints:
– GET /draft/{doc_id}  → fetch draft & examples
– POST /feedback/{doc_id} → accept or request re-extraction with inline JSON comments

Loop Logic (executed in LangGraph):

If validator POSTs status=accept, emit accepted edge.
If status=reextract and iteration_count < N, append comments to context and cycle back to ExtractionAgent.
If iteration_count ≥ N, emit max_iter_reached edge.

────────────────────────────────────────
7. Finalization
────────────────────────────────────────
Node: Finalizer
• On accepted: upsert (full_text, validated_structured_data, metadata) into LightRAG’s vector DB; link PDF file URI.
• On max_iter_reached: flag document in a “manual-follow-up” collection and alert ops via webhook/email.

────────────────────────────────────────
8. Observability & Governance
────────────────────────────────────────
• Every LangGraph edge automatically logs: timestamps, agent name, prompts, LLM responses, tool calls (via MCP), and validator actions.
• Logs flow to a central backend (e.g., OpenTelemetry → Grafana/Loki) with dashboards for:
– mean time per iteration
– confidence vs. acceptance rate
– validator edit distance
• Audit trail is immutable and queryable by document ID or agent run ID.

────────────────────────────────────────
9. Deployment Solution
────────────────────────────────────────

