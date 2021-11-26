# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

WORKDIR /user_management
ENV PYTHONPATH="${PYTHONPATH}:/user_management"
ENV PORT 80
EXPOSE $PORT

RUN pip install poetry; poetry config virtualenvs.create false
ADD poetry.lock pyproject.toml /user_management/

RUN poetry install --no-dev

COPY ./ .

CMD gunicorn user_management.main:create_app --bind=0.0.0.0:$PORT --config user_management/core/config/gunicorn.py
