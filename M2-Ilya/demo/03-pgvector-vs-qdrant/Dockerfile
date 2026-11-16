FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Code and data are mounted from the host (see docker-compose.yml), so edits apply without a rebuild.
CMD ["python", "demo.py", "--help"]
