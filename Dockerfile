# Python base image
FROM python:3.6.3

WORKDIR /usr/src/app
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt

# ENTRYPOINT /bin/bash
EXPOSE 5000

# Launch server app
ENTRYPOINT python ./app.py
