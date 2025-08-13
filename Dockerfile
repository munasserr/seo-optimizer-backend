FROM python:3.12.5-alpine

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
COPY ./requirements.txt /app

# Install required package
RUN apk update && \
    apk add --no-cache --virtual .build-deps \
    ca-certificates gcc mariadb-dev linux-headers musl-dev \
    libffi-dev zlib-dev gmp-dev bash gettext

# Install requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./ /app
WORKDIR /app

EXPOSE 8000
