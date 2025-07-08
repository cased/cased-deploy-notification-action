FROM python:3.11-slim

RUN pip install --no-cache-dir requests

COPY entrypoint.py /entrypoint.py

ENTRYPOINT ["python", "/entrypoint.py"]