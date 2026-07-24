"""
app.py
------

Flask API wrapping the RAG + tool-routing agent from
github.com/SantoshpHiremath/rag-tool-agent-demo as an HTTP service.

Endpoints:

  GET  /health        -> liveness check
  POST /ask            -> {"question": "..."} -> {"question": "...", "answer": "..."}

Request/response validation is done with Pydantic (schemas.py), matching
the shape a FastAPI version of this same service would use.

Which agent backend is used is controlled by the AGENT_MODE env var:
  AGENT_MODE=stub  (default) -> StubAgentRunner, no external dependencies,
                                  used for tests and local dev without Ollama.
  AGENT_MODE=real            -> RealAgentRunner, calls the actual LangChain
                                  agent. Requires Ollama running locally with
                                  llama3.2 + nomic-embed-text pulled, and the
                                  rag-tool-agent-demo project on PYTHONPATH.
"""

import os

from flask import Flask, jsonify, request
from pydantic import ValidationError

from agent_runner import RealAgentRunner, StubAgentRunner
from schemas import AskRequest, AskResponse


def create_app(agent_runner=None) -> Flask:
    app = Flask(__name__)

    if agent_runner is None:
        mode = os.environ.get("AGENT_MODE", "stub")
        agent_runner = RealAgentRunner() if mode == "real" else StubAgentRunner()

    app.config["AGENT_RUNNER"] = agent_runner

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/ask")
    def ask():
        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify({"error": "Request body must be valid JSON."}), 400

        try:
            req = AskRequest(**payload)
        except ValidationError as exc:
            return jsonify({"error": exc.errors()[0]["msg"]}), 400

        runner = app.config["AGENT_RUNNER"]
        try:
            answer = runner.run(req.question)
        except Exception as exc:  # agent/runtime failure, not a client error
            return jsonify({"error": f"Agent failed to answer: {exc}"}), 502

        response = AskResponse(question=req.question, answer=answer)
        return jsonify(response.model_dump())

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
