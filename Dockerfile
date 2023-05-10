# Use an official Python 3.10 runtime as a parent image
FROM python:3.10-slim-buster

# Set timezone to discord servers timezone
ENV TZ=America/New_York

# Install prerequisites
RUN apt-get update
RUN apt-get install -y git cron vim

# Clone the git repository
RUN git clone https://github.com/ConstObject/andross-api.git

# Set working directory to the cloned directory
WORKDIR /andross-api

# Update pip and install required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/Andross
ENV DB_HOST=<YOUR_DB_HOST>
ENV DB_PORT=<YOUR_DB_PORT>
ENV DB_NAME=<YOUR_DB_NAME>
ENV DB_USER=<YOUR_DB_USER>
ENV DB_PASSWORD=<YOUR_DB_PASSWORD>
ENV API-KEY=<YOUR_API_KEY>
ENV FLASK_APP=index.py

# Copy to /etc/environment
RUN env >> /etc/environment

ENTRYPOINT ["/entrypoint.sh"]
CMD ["start"]
