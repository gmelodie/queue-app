import json, sys
from cmd import Cmd
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol


class CommandInterface(Cmd):

    def do_call(self, call_id):
        """call <call id>
        Create a new call with id <id>"""
        if call_id:
            data = build_json('call', call_id)
            client.transport.write(data.encode())
        else:
            print('error: no call id specified')


    def do_answer(self, op_id):
        """answer <operator id>
        Make operator <operator id> answer a call"""
        if op_id:
            data = build_json('answer', op_id)
            client.transport.write(data.encode())
        else:
            print('error: no operator id specified')

    def do_reject(self, op_id):
        """reject <operator id>
        Make operator <operator id> reject a call"""
        if op_id:
            data = build_json('reject', op_id)
            client.transport.write(data.encode())
        else:
            print('error: no operator id specified')

    def do_hangup(self, call_id):
        """hangup <call id>
        Delete a call whose id is <call id>"""
        if call_id:
            data = build_json('hangup', call_id)
            client.transport.write(data.encode())
        else:
            print('error: no call id specified')

    def do_info(self, obj): # TODO: get info
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
        print('Bye bye')
        client.transport.loseConnection()
        reactor.callFromThread(reactor.stop)
        return True

    do_EOF = do_exit # EOF exits

    def print_server_response(self, response):
        print(response)

    def emptyline(self): # fix linebreak issue on client print
        pass


class Client(Protocol):

    def dataReceived(self, data):
        messages = data.decode().strip().split('\n')
        print() # insert \n
        for msg in messages:
            loaded_json = json.loads(msg)
            print('Server:', loaded_json['type'] + ':',\
                  loaded_json['message'])

    def connectionMade(self):
        print('Connected to server')

    def connectionLost(self, connector):
        print('Lost connection.')

    def connectionFailed(self, connector):
        print('Connection failed.')


def build_json(cmd, _id):
    return json.dumps({"command": cmd, "id": _id})


def connection_successful(attempt):
    reactor.callInThread(processor.cmdloop) # call cmd


def connection_timeout(attempt):
    print('Connection timed out. Exiting.')
    attempt.cancel()
    reactor.stop()


if __name__ == '__main__':

    # Set remote host and port
    host = 'localhost'
    port = 5678
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    print('Connecting to', (host, port))

    # Connect
    processor = CommandInterface()
    processor.prompt = '(Client) '
    client = Client()
    server_endpoint = TCP4ClientEndpoint(reactor, host, port)

    attempt = connectProtocol(server_endpoint, client)
    attempt.addCallback(connection_successful) # wait for connection to be made
    # reactor.callLater(10, connection_timeout, attempt) # TODO: connection timeout

    reactor.run()
