FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==1.7.1

COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

VOLUME ["/app/data"]

COPY src/ /app/src/

CMD ["python", "-m", "src.main"]
