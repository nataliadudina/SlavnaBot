FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry==1.7.1 --timeout 120 && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

VOLUME ["/app/data"]

COPY src/ /app/src/

CMD ["python", "-m", "src.main"]
