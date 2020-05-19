FROM python:3.8-buster
EXPOSE 5678

# Install dependencies
COPY requirements.txt /queue-app/requirements.txt
WORKDIR /queue-app
RUN pip3 install -r requirements.txt

COPY src/ /queue-app/src

ENTRYPOINT ["python3", "src/server.py"]
