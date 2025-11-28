FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY mcp/requirements.txt /app/mcp/requirements.txt
RUN pip install --no-cache-dir -r /app/mcp/requirements.txt

COPY mcp /app/mcp
COPY host_wrappers /app/host_wrappers

EXPOSE 8080

CMD ["uvicorn", "mcp.bridge:app", "--host", "0.0.0.0", "--port", "8080"]
