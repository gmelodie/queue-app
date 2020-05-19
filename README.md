# Queue Application
Call center CLI queue simulation app

## Installation
### Docker container
Download the docker containter for the server
```
docker pull gmelodie/queue-app
```

There is no docker image available for the client at the moment

### Bare installation
You may also run both the server and the client without the pre-compiled docker image,
 for this you would need to download and install the dependencies
 on your machine or using a virtual environment
```
python3 -m pip install -r requirements.txt
```

## Usage
### Running server
You may run the server directly python (this requires you to install the dependencies on `requirements.txt`)
```
python3 src/server.py [number of operators] [listen port]
```
Or using the docker image
```
docker run -p 5678:5678 gmelodie/queue-app [number of operators] [listen port]
```

**Obs:** The server defaults to serve on `localhost` port `5678`. If you decide to change these configurations
 make sure the exposed port on docker matches the one you chose.

### Running client
There is no docker image for the client. To run the client download the dependencies on
 `requirements.txt` and execute it using python

```
python3 src/client.py [remote host] [remote port]
```


## JSON API
### Commands (from client to server)
Command | JSON format | Description
--- | --- | ---
Call | {'command': 'call', 'id': `call_id`} | Creates new call with the ID `call_id`
Answer | {'command': 'answer', 'id': `op_id`} | Answers a ringing call (if exists) on operator with ID `op_id`
Reject | {'command': 'reject', 'id': `op_id`} | Rejects a ringing call (if exists) on operator with ID `op_id`
Hangup | {'command': 'hangup', 'id': `call_id`} | Deletes a call (if exists) with the ID `call_id`
Info | {'command': 'info', 'id': `{ops, calls}`} | Prints informations about operators (if `ops`) or call queues (if `calls`)

### Info Messages (from server to client)
Message | JSON format | Description
--- | --- | ---
Error | {'type': 'error', 'message': `error_message`} | Signals an error with the message `error_message`
Update | {'type': 'update', 'message': `update_message`} | Signals an update message with the content `update_message`
