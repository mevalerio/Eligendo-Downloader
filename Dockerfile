FROM python:3.12-slim

WORKDIR /service
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .

ENV ELIGENDO_DATA_DIR=/service/data
VOLUME ["/service/data"]
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
