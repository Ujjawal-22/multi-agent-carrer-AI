# LangChain

LangChain is a Python (and JavaScript) framework for building applications
powered by large language models. It provides standardized abstractions
for the common building blocks of LLM applications: prompt templates,
chains (sequences of calls), memory (conversation state), document loaders,
text splitters, and integrations with dozens of LLM providers, vector
stores, and tools.

## What it's actually for

Before frameworks like LangChain existed, every LLM application reinvented
the same plumbing: formatting prompts, parsing outputs, managing
conversation history, and connecting to external data sources. LangChain
standardizes these patterns so developers can compose them rather than
rebuild them.

## Core concepts

- **Prompt templates**: parameterized prompts that can be reused and
  versioned, separating prompt text from application logic.
- **Chains**: sequences of calls (to an LLM, a tool, or another chain)
  composed together. The modern LangChain Expression Language (LCEL) uses
  the `|` operator to pipe components together declaratively.
- **Document loaders and text splitters**: utilities for ingesting
  documents (PDFs, web pages, markdown) and breaking them into chunks
  suitable for embedding and retrieval.
- **Retrievers and vector store integrations**: standardized interfaces
  for connecting to vector databases (Qdrant, Pinecone, Chroma, etc.) for
  retrieval-augmented generation.
- **Memory**: mechanisms for persisting conversation state across turns.

## How it relates to LangGraph

LangChain's chains are primarily useful for linear or simple branching
workflows. For applications requiring more control over execution flow -
conditional branching, parallel execution, cycles, and explicit state
management - LangGraph (built by the same team) is typically preferred.
Many real applications use LangChain's component library (prompts,
loaders, integrations) alongside LangGraph for orchestration.

## Common interview-relevant depth signals

A candidate with genuine LangChain experience should be able to explain:
why they chose a chain structure over calling the LLM API directly, how
they handled output parsing/validation, and the trade-offs between
LangChain's abstractions versus writing the equivalent logic by hand.
