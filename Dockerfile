FROM python:3.9-slim as builder

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

RUN groupadd -r log-replicator && useradd -g log-replicator log-replicator
RUN pip install --upgrade -r /code/requirements.txt
COPY ./app /code/app

USER log-replicator:log-replicator

FROM python:3.9-slim
WORKDIR /code

COPY --from=builder /code /code
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

