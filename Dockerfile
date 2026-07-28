# rag-tool-api — containerized Flask service wrapping the RAG/tool-routing agent.
#
# Multi-stage build: a builder stage installs dependencies into a venv,
# the runtime stage copies only the venv + app code, keeping the final
# image slim and free of build tooling. Runs as a non-root user.

FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

# Non-root runtime user — never run application code as root in a container.
RUN useradd --create-home --uid 1000 appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    AGENT_MODE=stub

WORKDIR /app
COPY app.py schemas.py agent_runner.py ./

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0", "--port=8000"]
