FROM docker as docker

FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /config
COPY requirements /config/requirements
RUN pip install -r /config/requirements/dev.txt
RUN mkdir /src

COPY --from=docker . .

WORKDIR /src
