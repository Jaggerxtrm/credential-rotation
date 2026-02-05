
FROM python:3.11-slim

WORKDIR /app
RUN pip install requests

COPY examples/docker-service-poc/client/client_script.py .

CMD ["python", "client_script.py"]
