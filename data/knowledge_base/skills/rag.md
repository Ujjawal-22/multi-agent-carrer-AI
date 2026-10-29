# Retrieval-Augmented Generation (RAG)

RAG is a technique for grounding LLM outputs in external knowledge that
wasn't part of the model's training data (or that the model might get
wrong from memory alone) by retrieving relevant documents at query time
and including them in the prompt before generation.

## Why it matters

LLMs hallucinate - they can produce confident, fluent, and wrong answers,
especially about specific facts, recent events, or niche/proprietary
information. RAG reduces this risk by giving the model actual source
material to ground its answer in, and by making answers attributable to
specific documents rather than opaque model knowledge.

## The standard pipeline

1. **Ingestion**: documents are parsed, cleaned, and split into chunks
   (chunking) small enough to be useful as retrieval units but large
   enough to retain context.
2. **Embedding**: each chunk is converted into a vector using an embedding
   model, capturing its semantic meaning as a point in high-dimensional
   space.
3. **Indexing**: embeddings are stored in a vector database for fast
   similarity search.
4. **Retrieval**: at query time, the query is embedded with the same
   model, and the vector database returns the most similar chunks.
5. **Generation**: the retrieved chunks are inserted into the LLM's
   prompt as context, and the LLM generates an answer grounded in that
   context.

## Hybrid retrieval

Pure vector (dense) search can miss exact keyword matches that a simpler
keyword search (like BM25) would catch easily, and vice versa - dense
search is better at semantic similarity, keyword search is better at
exact terms and rare words. Hybrid retrieval combines both, commonly
fused via reciprocal rank fusion (RRF), which combines rankings by each
result's rank position rather than raw scores (since dense similarity
scores and keyword scores aren't on comparable scales).

## Common pitfalls worth being able to discuss

- Retrieving irrelevant chunks that still "sound" relevant due to
  surface-level word overlap.
- Chunking too small (loses context) or too large (dilutes relevance,
  wastes context window).
- Not handling the case where retrieval returns nothing useful - a good
  RAG system should be able to say "I don't have information on that"
  rather than forcing an answer from irrelevant context.
- Treating queries and documents identically when embedding them, when
  many embedding models perform better with asymmetric
  query-vs-document instructions.
