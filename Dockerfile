# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster

WORKDIR /user_management
ENV PYTHONPATH="${PYTHONPATH}:user_management"


RUN pip install poetry; poetry config virtualenvs.create false
ADD poetry.lock pyproject.toml /user_management/


RUN mkdir /root/.ssh/
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

RUN poetry install --no-dev

COPY ./ .

ENTRYPOINT ["python", "user_management/main.py"]
