# Use an official Python 3.10 runtime as a parent image
FROM python:3.10-slim-buster

# Set timezone to discord servers timezone
ENV TZ=America/New_York

# Install prerequisites
RUN apt-get update
RUN apt-get install -y git cron vim

# Set working directory
WORKDIR /andross-api

COPY . .

# Update pip and install required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/Andross
ENV FLASK_APP=index.py

# Create cron job to run update.py, every 20 minutes and then every once a day at midnight, then run cron
RUN crontab crontab
RUN touch /var/log/cron.log

RUN mv entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["start"]
