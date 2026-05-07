# TODO: Write a production-ready Dockerfile
#
# All of these are tested by the grader:
#
# [ ] Multi-stage build (2+ FROM instructions)
# [ ] Base image: python:3.14-slim (pinned version, no :latest)
# [ ] Copy requirements.txt and pip install BEFORE copying source code (layer caching)
# [ ] Run as a non-root USER
# [ ] EXPOSE 8080
# [ ] HEALTHCHECK instruction
# [ ] No hardcoded secrets (no ENV PASSWORD=..., no ENV SECRET_KEY=...)
# [ ] Final image under 200MB
#
# Start command: uvicorn src.app:app --host 0.0.0.0 --port 8080
FROM python:3.14-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.14-slim

WORKDIR /app

RUN useradd -m appuser
USER appuser

COPY --from=builder /install /usr/local
COPY src ./src

EXPOSE 8080

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080"]