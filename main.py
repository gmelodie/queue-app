import sys, math, string, secrets, enum, cmd
from collections import OrderedDict


MAX_NUM_OPS = 26


class OperatorStates(enum.Enum):
    AVAILABLE = 'available'
    RINGING = 'ringing'
    BUSY = 'busy'


class Operator():
    def __init__(self, op_id):
        self.op_id = op_id
        self.state = OperatorStates.AVAILABLE
        self.call_id = None


class CallCenter(cmd.Cmd):
    def do_call(self, call_id):
        """call <call id>
        Create a new call with id <id>"""
        if call_id:
            if call_id in wait_calls or call_id in handle_calls:
                print('error: call', call_id, 'already exists')
                return
            print('Call', call_id, 'received')
            new_call(call_id)
        else:
            print('error: no call id specified')

    def do_answer(self, op_id):
        """answer <operator id>
        Make operator <operator id> answer a call"""
        if op_id:
            op_answer_call(op_id)
        else:
            print('error: no operator id specified')

    def do_reject(self, op_id):
        """reject <operator id>
        Make operator <operator id> reject a call"""
        if op_id:
            op_reject_call(op_id)
        else:
            print('error: no operator id specified')

    def do_hangup(self, call_id):
        """hangup <call id>
        Delete a call whose id is <call id>"""
        if call_id:
            hangup_call(call_id)
        else:
            print('error: no call id specified')

    def do_info(self, obj):
        """info {calls | ops}
        Shows information about operators (ops) or calls"""
        if not obj:
            print("error: no info object specified, \
                    expected 'calls' or 'obs'")
        elif obj == 'calls':
            pass
        elif obj == 'ops':
            pass

    def do_exit(self, s):
        return True

    do_EOF = do_exit


def new_call(call_id):
    """ Creates a new call with ID <call_id>
    Assigns call to available operator
    Inserts assigned call into handle_calls
    Changes operator state from AVAILABLE to RINGING
    Puts in wait_calls if no operators are available
    """
    if len(available_operators) <= 0:
        wait_calls.append(call_id)
        print('Call', call_id, 'waiting in queue')
        return

    op_id, op = available_operators.popitem(last=False)

    handle_calls[call_id] = op_id
    op.call_id = call_id
    op.state = OperatorStates.RINGING
    ringing_operators[op.op_id] = op

    print('Call', call_id, 'ringing for operator', op.op_id)


def op_answer_call(op_id):
    """ Accepts a ringing call in the operator with ID <op_id>
    Moves operator to BUSY state
    """
    op = _op_respond_call(op_id)
    if op:
        op.state = OperatorStates.BUSY
        busy_operators[op_id] = op
        print('Call', op.call_id, 'answered by operator', op.op_id)


def op_reject_call(op_id):
    """ Rejects a ringing call in the operator with ID <op_id>
    Frees operator and move call to wait_calls
    """
    op = _op_respond_call(op_id)
    if op:
        print('Call', op.call_id, 'rejected by operator', op.op_id)
        wait_calls.append(op.call_id)
        _op_free(op)


def hangup_call(call_id):
    """ Deletes or ends a call with ID <call_id>
    Remove call if it is in the wait_calls (Call missed)
    Prints an error if the call is not in wait_calls or hadle_calls
    Terminates and frees operator if call is ringing or has been answered
    """
    if call_id in wait_calls:
        op_id = wait_calls.remove(call_id)
        print('Call', call_id, 'missed')
        return

    if call_id not in handle_calls:
        print('error: no such call being handled')
        return

    op_id = handle_calls[call_id]
    if op_id in ringing_operators:
        print('Call', call_id, 'missed')
        return

    op = busy_operators[op_id]
    print('Call', call_id, 'finished and operator', op_id, 'available')
    _op_free(op)


def _op_free(op):
    """Frees operator <op>
    Assigns new call if there is one at wait queue
    """

    handle_calls.pop(op.call_id)
    op.call_id = None
    op.state = OperatorStates.AVAILABLE
    available_operators[op.op_id] = op

    if len(wait_calls) > 0:
        new_call(wait_calls.pop(0))


def _op_respond_call(op_id):
    """
    Prints an error if operator is not in ringing state
    Prints an error if operator is ringing but call doesn't exist
    """
    if op_id not in ringing_operators:
        print('error: operator not in ringing state')
        return None

    op = ringing_operators.pop(op_id)

    if op.call_id is None:
        print('error: operator in ringing state but call_id is None')
        _op_free(op)
        print('Operator', op_id, 'moved back to', \
              OperatorStates.AVAILABLE, 'state')
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


if __name__ == '__main__':
    num_ops = 10
    if len(sys.argv) > 1:
        num_ops = int(sys.argv[1])

    available_operators = generate_operators(num_ops)
    ringing_operators = OrderedDict()
    busy_operators = OrderedDict()

    wait_calls = []
    handle_calls = OrderedDict()

    CallCenter().cmdloop()
