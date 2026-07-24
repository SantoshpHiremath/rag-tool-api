"""
agent_runner.py
----------------

Thin adapter between the API layer and the actual RAG + tool-routing agent
(github.com/SantoshpHiremath/rag-tool-agent-demo).

The real agent (agent.py / rag_tool.py / calculator_tool.py in that repo)
depends on a locally-running Ollama instance to serve the LLM and the
embedding model. That's the correct way to run it for real use, but it
makes the API impossible to unit-test in an environment without Ollama
installed (like a CI runner, or this sandbox).

So this module defines a small AgentRunner protocol with two
implementations:

- RealAgentRunner: imports and calls the actual agent.run_agent() from the
  rag-tool-agent-demo project. Use this in production, with Ollama running.
- StubAgentRunner: a deterministic, dependency-free stand-in used by the
  test suite (see tests/test_api.py) so routing and error-handling logic
  can be verified without needing a live LLM.

Which implementation the Flask app uses is controlled by the AGENT_MODE
environment variable ("real" or "stub"), read in app.py.
"""

from __future__ import annotations

from typing import Protocol


class AgentRunner(Protocol):
    def run(self, question: str) -> str:
        ...


class RealAgentRunner:
    """Wraps the actual agent from rag-tool-agent-demo. Requires Ollama
    running locally with llama3.2 and nomic-embed-text pulled, and that
    project's directory on PYTHONPATH."""

    def __init__(self):
        from agent import run_agent  # from the rag-tool-agent-demo project
        self._run_agent = run_agent

    def run(self, question: str) -> str:
        return self._run_agent(question)


class StubAgentRunner:
    """Deterministic stand-in with the same routing contract as the real
    agent (retrieval vs. calculator vs. direct answer), used for tests and
    for local development without Ollama installed."""

    def run(self, question: str) -> str:
        lowered = question.lower()
        if any(op in question for op in ("+", "-", "*", "/")) and any(c.isdigit() for c in question):
            return f"[calculator] Evaluated expression in: {question}"
        if any(kw in lowered for kw in ("forda", "dataset", "preprocess", "chunk", "embedding")):
            return (
                f"[search_notes] Answer grounded in retrieved chunks for: {question}"
                "\n\n[Grounded in 3 retrieved chunk(s) from forda_dataset_notes.md]"
            )
        return f"[direct] {question}"
