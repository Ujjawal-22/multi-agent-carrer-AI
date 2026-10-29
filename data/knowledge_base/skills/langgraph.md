# LangGraph

LangGraph is a library (built by the LangChain team) for building stateful,
multi-agent applications as explicit graphs. Unlike a simple linear chain,
a LangGraph graph is composed of nodes (units of work - often an LLM call,
a tool call, or deterministic logic) and edges (the control flow between
them), with a shared state object that flows through the graph and
accumulates results.

## Why it exists

Real multi-agent systems need things a simple chain can't easily express:
conditional branching based on intermediate results, genuine parallel
execution of independent steps, cycles (an agent retrying or looping until
a condition is met), and clear visibility into what each step in a complex
pipeline actually did. LangGraph models all of this explicitly as a graph
rather than implicitly through nested function calls.

## Core concepts

- **State**: typically a Pydantic model or TypedDict representing
  everything that flows through the graph. Each node reads the fields it
  needs and returns a partial update; LangGraph merges updates into the
  running state.
- **Nodes**: individual units of work - a node is just a function that
  takes the current state and returns an update.
- **Edges**: define execution order. A node with multiple outgoing edges
  to different targets creates a fan-out (parallel execution, if neither
  target depends on the other). A node with multiple incoming edges is a
  fan-in point - LangGraph won't run it until all its predecessors have
  completed.
- **Reducers**: for state fields that should accumulate rather than be
  overwritten (e.g. a list of errors from multiple parallel nodes),
  LangGraph supports custom reducer functions (e.g. `operator.add`) so
  concurrent updates don't silently overwrite each other.

## Common interview-relevant depth signals

A candidate with genuine LangGraph experience should be able to explain:
which parts of their graph actually run in parallel and why (not just
"it's multi-agent"), how they handle a node failing without crashing the
whole graph, and why they chose explicit graph orchestration over a
simpler sequential script for their specific use case. A common mistake
is claiming "multi-agent" architecture when the actual execution is
entirely sequential with no real concurrency - a good interview question
can distinguish genuine parallel fan-out from a chain dressed up as a
graph.
