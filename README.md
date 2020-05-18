# Queue Application
Simple CLI queue application

## Installation

## Usage

## JSON API
### Commands (from client to server)
Command | JSON format | Description
--- | --- | ---
Call | {'command': 'call', 'id': `call_id`} | Creates new call with the ID `call_id`
Answer | {'command': 'answer', 'id': `op_id`} | Answers a ringing call (if exists) on operator with ID `op_id`
Reject | {'command': 'reject', 'id': `op_id`} | Rejects a ringing call (if exists) on operator with ID `op_id`
Hangup | {'command': 'hangup', 'id': `call_id`} | Deletes a call (if exists) with the ID `call_id`

### Info Messages (from server to client)
Message | JSON format | Description
--- | --- | ---
Error | {'type': 'error', 'message': `error_message`} | Signals an error with the message `error_message`
Update | {'type': 'update', 'message': `update_message`} | Signals an update message with the content `update_message`
