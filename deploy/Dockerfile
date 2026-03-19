FROM python:3.11-slim

USER root

## System packages
RUN apt-get update && apt-get install -y \
    libexpat1 

## Working directory
WORKDIR /app

## Source code
COPY . .

## Packages

RUN pip3 install --no-cache-dir -r requirements.txt 

## Dashboard user
RUN useradd -m ldsfsoil_africa

USER ldsfsoil_africa

## Run command
CMD ["shiny", "run", "--port", "8080", "--host", "0.0.0.0", "app.py"]