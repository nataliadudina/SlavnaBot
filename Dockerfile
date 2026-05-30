FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

VOLUME ["/app/data"]

COPY src/ /app/src/

CMD ["python", "-m", "src.main"]
