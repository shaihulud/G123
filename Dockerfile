FROM python:3.9-slim AS app

WORKDIR /code

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY requirements.dev.txt .
RUN pip3 install --no-cache-dir -r requirements.dev.txt

COPY . .
COPY dev.env .env

EXPOSE 8000

ENTRYPOINT [ "/code/docker-entrypoint.sh" ]
