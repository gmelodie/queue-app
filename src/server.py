import sys, math, string, secrets, enum, json
from collections import OrderedDict

from twisted.internet.protocol import ServerFactory, Protocol
from twisted.internet import reactor


class OperatorStates(enum.Enum):

    AVAILABLE = 'available'
    RINGING = 'ringing'
    BUSY = 'busy'


class Operator():

    def __init__(self, op_id):
        self.op_id = op_id
        self.state = OperatorStates.AVAILABLE
        self.call_id = None


class ClientHandler(Protocol):

    def dataReceived(self, data):
        json_data = json.loads(data.decode())
        self.parse_command(json_data)

    def parse_command(self, json_data):
        if 'command' not in json_data or 'id' not in json_data:
            self.send_msg('error', "'command' or 'id' not found")
            return
        cmd = json_data['command']
        _id = json_data['id']
        if cmd not in COMMANDS:
            self.send_msg('error', 'invalid command ' + cmd)
            return
        COMMANDS[cmd](_id, self) # call command

    def send_msg(self, msg_type, content):
        msg = {'type': msg_type, 'message': content}
        self.transport.write((json.dumps(msg)+'\n').encode())


def new_call(call_id, client, fromQueue=False):
    """ Creates a new call with ID <call_id>
    Assigns call to available operator
    Inserts assigned call into handle_calls
    Changes operator state from AVAILABLE to RINGING
    Puts in wait_calls if no operators are available
    """
    if call_id in wait_calls or call_id in handle_calls:
        client.send_msg('error', 'Call ' + call_id + \
                        ' already exists')
        return

    # only print "call received" if call doesnt come from queue
    if not fromQueue:
        client.send_msg('update', 'Call '+ call_id +' received')

    if len(available_operators) <= 0:
        wait_calls.append(call_id)
        client.send_msg('update', 'Call ' + call_id + \
                        ' waiting in queue')
        return

    # Move operator from available to ringing
    op_id, op = available_operators.popitem(last=False)
    handle_calls[call_id] = op_id
    op.call_id = call_id
    op.state = OperatorStates.RINGING
    ringing_operators[op.op_id] = op

    client.send_msg('update', 'Call ' + call_id + \
                    ' ringing for operator ' + op.op_id)


def op_answer_call(op_id, client):
    """ Accepts a ringing call in the operator with ID <op_id>
    Moves operator to BUSY state
    """
    op = _op_respond_call(op_id, client)
    if op:
        op.state = OperatorStates.BUSY
        busy_operators[op_id] = op
        client.send_msg('update', 'Call ' + op.call_id + \
                        ' answered by operator ' + op.op_id)


def op_reject_call(op_id, client):
    """ Rejects a ringing call in the operator with ID <op_id>
    Frees operator and move call to wait_calls
    """
    op = _op_respond_call(op_id, client)
    if op:
        client.send_msg('update', 'Call ' + op.call_id + \
                        ' rejected by operator ' + op.op_id)
        _op_free(op, client)


def hangup_call(call_id, client):
    """ Deletes or ends a call with ID <call_id>
    Remove call if it is in the wait_calls (Call missed)
    Returns an error if the call is not in wait_calls or hadle_calls
    Terminates and frees operator if call is ringing or has been answered
    """
    if call_id in wait_calls:
        op_id = wait_calls.remove(call_id)
        client.send_msg('update', 'Call '+call_id+' missed')
        return

    if call_id not in handle_calls:
        client.send_msg('error', 'no such call being handled')
        return

    op_id = handle_calls[call_id]

    if op_id in ringing_operators: # hangup a ringing call
        op = ringing_operators[op_id]
        client.send_msg('update', 'Call '+call_id+' missed')
    else:                           # hangup an ongoing call
        op = busy_operators[op_id]
        client.send_msg('update', 'Call '+call_id+' finished' + \
                        ' and operator ' + op_id + ' available')

    _op_free(op, client)


def info(obj, client):
    """Returns information about operators and calls
    Returns lists of available, ringing and busy operators if <obj> == 'ops'
    Returns handled and waiting calls if <obj> == 'calls'
    """
    if obj == 'ops':
        available_ops = 'Available operators: ' + \
            str([op_id for op_id in available_operators.keys()])
        client.send_msg('update', available_ops)

        ringing_ops = 'Ringing operators: ' + \
            str([op_id for op_id in ringing_operators.keys()])
        client.send_msg('update', ringing_ops)

        busy_ops = 'Busy operators: ' + \
            str([op_id for op_id in busy_operators.keys()])
        client.send_msg('update', busy_ops)

    elif obj == 'calls':
        waiting = 'Waiting calls: ' + str(wait_calls)
        client.send_msg('update', waiting)

        handled = 'Calls being handled: ' + \
            str([call_id for call_id in handle_calls.keys()])
        client.send_msg('update', handled)

    else:
        client.send_msg('error', 'invalid info obj ' + obj)


def _op_free(op, client):
    """Frees operator <op>
    Removes operator from busy or ringing group
    Puts operator in available_operators
    Assigns new call if there is one at wait queue
    """

    handle_calls.pop(op.call_id)
    op.call_id = None
    op.state = OperatorStates.AVAILABLE

    # Remove operator from wherever he is
    if op.op_id in busy_operators:
        busy_operators.pop(op.op_id)
    elif op.op_id in ringing_operators:
        ringing_operators.pop(op.op_id)
    else:
        print('error: trying to free available operator')

    available_operators[op.op_id] = op

    if len(wait_calls) > 0:
        new_call(wait_calls.pop(0), client, fromQueue=True)


def _op_respond_call(op_id, client):
    """
    Returns an error if operator is not in ringing state
    Returns an error if call doesn't exist
    """
    if op_id not in ringing_operators:
        client.send_msg('error', 'operator ' + op_id + \
                        ' not in ringing state')
        return None

    op = ringing_operators.pop(op_id)

    if op.call_id is None:
        client.send_msg('error', 'operator ' + op_id + ' in \
                        ringing state but call_id is none')
        _op_free(op, client)
        client.send_msg('update', 'operator '+ op_id+' moved \
            back to ' + OperatorStates.AVAILABLE + ' state')
        return None

    return op


def generate_operators(num_ops):
    """ Generates <num_ops> operator objects
    Chooses length of operator ID according to <num_ops>
    Returns operators in a set
    """
    if num_ops > MAX_NUM_OPS:
        print('error: maximum number of operators is', num_ops)
        num_ops = 10

    operators = OrderedDict()
    alphabet = string.ascii_uppercase # characters to use in operator IDs

    # How many letters to use in ID
    # idlen = int(math.ceil(math.log(num_ops, len(alphabet))))

    for j in range(num_ops):
        # op_id = ''.join(secrets.choice(alphabet) for i in range(idlen))
        op_id = alphabet[j]
        operators[op_id] = Operator(op_id)

    print('Setting number of operators to', num_ops)
    return operators


MAX_NUM_OPS = 26

COMMANDS = {
    'call': new_call,
    'answer': op_answer_call,
    'reject': op_reject_call,
    'hangup': hangup_call,
    'info': info,
}


if __name__ == '__main__':
    # Setup number of operators and generate
    num_ops = 10
    if len(sys.argv) > 1:
        num_ops = int(sys.argv[1])

    # Initialize queue structures
    available_operators = generate_operators(num_ops)   # op_id: op
    ringing_operators = OrderedDict()                   # op_id: op
    busy_operators = OrderedDict()                      # op_id: op

    wait_calls = []                     # call_id
    handle_calls = OrderedDict()        # call_id: op_id

    port = 5678
    if len(sys.argv) > 3:
        port = int(sys.argv[3])
    print('Listening on port', port)

    # Initialize Twisted server
    factory = ServerFactory()
    factory.protocol = ClientHandler
    reactor.listenTCP(port, factory)
    reactor.run()
