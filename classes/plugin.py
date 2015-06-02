import zmq
import threading
import time

class plugin(object):
    
    def __init__(self, instanceName='default'):
        self.instanceName = instanceName + '_' + self.__class__.__name__
        self.running = True
        self.zmqContext = zmq.Context()

    def attach(self, pump):
        if not callable(getattr(self, 'handleBroadcast')):
            self.killThreads()
            raise AttributeError('You must declare handleBroadcast as a method of a plugin class')

        self.zmqMPPushSocket = self.zmqContext.socket(zmq.PUSH)
        self.zmqMPPushSocket.bind('inproc://' + self.instanceName + '_push')
        pumpSocketName = pump.connect(self.instanceName)
        self.zmqMPPullSocket = self.zmqContext.socket(zmq.PULL)
        self.zmqMPPullSocket.connect(pumpSocketName)
        self.zmqBroadcast = self.zmqContext.socket(zmq.SUB)
        self.zmqBroadcast.connect(pump.broadcastName)

        self.messageThread = threading.Thread(target=self.messageLoop)
        self.messageThread.start()

    def killThreads(self):
        self.running = False
        self.messageThread.join()

    def messageLoop(self):
        while self.running:
            
            specificMessage = None
            broadcastMessage = None

            try:
                specificMessage = self.zmqMPPullSocket.recv_pyobj(flags=zmq.NOBLOCK)
            except zmq.ZMQError,e:
                if 'Resource temporarily unavailable' == str(e):
                    pass
                else:                    
                    self.running = False
                    raise

            if specificMessage is not None:
                self.handleMessage(specificMessage)

            try:
                broadcastMessage = self.zmqBroadcast.recv_pyobj(flags=zmq.NOBLOCK)
            except zmq.ZMQError,e:
                if 'Resource temporarily unavailable' == str(e):
                    pass
                else:
                    self.running = False
                    raise

            if broadcastMessage is not None:
                self.handleBroadcast(broadcastMessage)
                
            time.sleep(0.001)

    def handleMessage(self, message):
        method = None
        try:
            method = getattr(self, message['methodName'])
        except AttributeError:
            errmsg = {}
            errmsg['from'] = self.instanceName
            errmsg['to'] = message['from']
            errmsg['methodName'] = 'error'
            errmsg['parameters'] = {'message': self.instanceName + ' does not accept ' + message['methodName'] + ' messages.'}
            errmsg['isBroadcast'] = False
            self.send(errmsg)
            
        if method is not None:
            result = method(**message['parameters'])
            if 'callback' in message:
                callback = {}
                callback['from'] = self.instanceName
                callback['to'] = message['to']
                callback['methodName'] = message['callback']
                callback['parameters'] = result
                callback['isBroadcast'] = False
                
                self.send(callback)

    def send(self, message):
        self.zmqMPPushSocket.send_pyobj(message)
