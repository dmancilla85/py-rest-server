FROM python:3.14
LABEL authors="David A. Mancilla"

WORKDIR /server

COPY pyproject.toml uv.lock ./
COPY swagger.yml ./

RUN pip install uv && uv sync --no-dev

COPY . .

ARG PORT=5000
ENV PORT=${PORT}
EXPOSE ${PORT}
CMD ["uv", "run", "main.py"]