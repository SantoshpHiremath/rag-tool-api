# RAG Tool Agent — API Wrapper

A small Flask API that exposes the RAG + tool-routing agent from
[rag-tool-agent-demo](https://github.com/SantoshpHiremath/rag-tool-agent-demo)
as an HTTP service, so it can be called by any client (a chatbot UI, another
service, curl) instead of only running as a CLI script.

Built to close a specific gap: hands-on experience with a backend/API
framework (Flask, FastAPI, Express, Spring, Django, ...), on top of an
LLM/agent project I had already built and tested.

## Why it's structured this way

- **`agent_runner.py`** defines an `AgentRunner` interface with two
  implementations: `RealAgentRunner` (calls the actual LangChain agent,
  which needs Ollama running locally with `llama3.2` and
  `nomic-embed-text` pulled) and `StubAgentRunner` (a deterministic,
  dependency-free stand-in with the same routing contract). This is
  dependency injection for testability — the API's routing, validation,
  and error-handling logic can be fully unit-tested without a live LLM,
  the same way you'd mock an external service in any real backend.
- **`schemas.py`** defines the request/response shape with Pydantic. This
  is the same validation layer FastAPI is built on, so the schema module
  ports over unchanged if this is later moved from Flask to FastAPI.
- **`app.py`** is the Flask app itself: two routes, JSON in/out, explicit
  400 (bad input) vs. 502 (agent/backend failure) status codes.
- **`tests/test_api.py`** hits the API through Flask's test client (i.e.
  through the actual HTTP interface, not by calling internal functions
  directly), covering the happy path, all three routing branches
  (retrieval / calculator / direct answer), input validation, and
  agent-failure handling. 16 tests, all passing.

## Endpoints

```
GET  /health
     -> 200 {"status": "ok"}

POST /ask
     body: {"question": "What is the FordA dataset used for?"}
     -> 200 {"question": "...", "answer": "..."}
     -> 400 {"error": "..."}   if the question is missing/blank/too long
     -> 502 {"error": "..."}   if the underlying agent fails (e.g. Ollama down)
```

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the tests

```bash
pytest tests/ -v
```

Runs fully offline with `AGENT_MODE=stub` (the default) — no Ollama
required. 16 tests, all passing.

## Running the real API

Requires [Ollama](https://ollama.com) running locally, with the two models
the underlying agent uses pulled:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Then, with the `rag-tool-agent-demo` project cloned alongside this one (or
its path added to `PYTHONPATH`):

```bash
AGENT_MODE=real python app.py
```

The server starts on `http://localhost:8000`.

## Example requests

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the FordA dataset used for, and who created it?"}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Compute 1320 / (3601 + 1320)"}'

# validation error
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'
```

## Relationship to the original project

This repo does not duplicate the agent logic — it imports and calls
`run_agent()` from
[rag-tool-agent-demo](https://github.com/SantoshpHiremath/rag-tool-agent-demo)
when `AGENT_MODE=real`. That project remains the source of truth for the
actual RAG pipeline (FAISS vector index, Ollama embeddings, LCEL retrieval
chain, calculator tool, and the LLM's tool-routing decision logic). This
repo is purely the API/service layer on top of it.
