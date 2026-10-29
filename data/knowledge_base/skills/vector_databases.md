# Vector Databases

A vector database stores high-dimensional embedding vectors and provides
fast approximate nearest-neighbor (ANN) search over them - given a query
vector, it returns the stored vectors most similar to it, typically by
cosine similarity or dot product.

## Why a specialized database

A standard relational database isn't built for this - finding the "most
similar" vectors among millions of high-dimensional points requires
specialized indexing structures (like HNSW - Hierarchical Navigable Small
World graphs) that trade a small amount of accuracy for enormous speed
gains over a brute-force comparison against every stored vector.

## Common vector databases

- **Qdrant**: open-source, written in Rust, supports filtering on
  metadata alongside vector search, runs well self-hosted via Docker.
- **Pinecone**: managed/cloud-only vector database, popular for
  production RAG applications that don't want to self-host.
- **Chroma**: lightweight, often used for local development and
  prototyping.
- **pgvector**: a PostgreSQL extension that adds vector similarity search
  to an existing relational database, useful when you don't want a
  separate database system just for vectors.

## Key concepts

- **Collections**: a named group of vectors (analogous to a table),
  typically all of the same dimensionality.
- **Payload/metadata**: most vector databases let you attach arbitrary
  metadata (source, category, timestamps) to each vector and filter
  search results by it, combining semantic search with structured
  filtering.
- **Distance metric**: cosine similarity, dot product, or Euclidean
  distance - the choice depends on how the embedding model was trained;
  most modern embedding models are designed for cosine similarity.

## Common interview-relevant depth signals

A candidate with genuine vector database experience should be able to
explain why they chose a specific distance metric (or that they just used
the embedding model's recommended default), how they structured metadata
for filtering, and what happens to retrieval quality as the collection
grows - these are the kinds of questions that separate "I called an
API" from "I understand what's actually happening."
