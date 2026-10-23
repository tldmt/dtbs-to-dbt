FROM python:3.14-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    python3-dev \
    git \
    curl 

RUN python -m pip install --upgrade pip
RUN python -m pip install uv

ENV PATH="/root/.local/bin:${PATH}"