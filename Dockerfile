# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

ARG RELEASE_COMMIT
ENV RELEASE=$RELEASE_COMMIT

ENV PORT 80
EXPOSE $PORT

COPY ./dist /opt

RUN pip install --no-cache-dir --find-links /opt hb_platform_user_management

CMD uvicorn --factory user_management.main:create_app --host 0.0.0.0 --port $PORT
