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
WORKDIR /andross-api/

# Update pip and install required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/Andross
ENV FLASK_APP=index.py

RUN mv entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["start"]
