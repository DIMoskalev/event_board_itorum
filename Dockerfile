FROM python:3

WORKDIR /app

COPY uv.lock pyproject.toml .

RUN pip install uv
RUN uv sync

COPY . .

# CMD ["uvicorn", "project.asgi:application", "--host", "0.0.0.0", "--port", "8000"]