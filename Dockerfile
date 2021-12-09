# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

ENV PORT 80
EXPOSE $PORT

COPY ./dist /opt

RUN pip install --no-cache-dir --find-links /opt hb_platform_user_management

CMD gunicorn user_management.main:create_app --bind=0.0.0.0:$PORT --config python:user_management.core.config.gunicorn
