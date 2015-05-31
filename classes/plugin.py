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

        if not callable(getattr(self, 'handleMessage')):
            self.killThreads()
            raise AttributeError('You must declare handleMessage as a method of a plugin class')

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
        self.messageThread.abort()

    def messageLoop(self):
        while self.running:
            
            specificMessage = None
            broadcastMessage = None

            try:
                specificMessage = self.zmqMPPullSocket.recv_pyobj(flags=zmq.NOBLOCK)
            except zmq.ZMQError,e:
                if 'Resource temporarily unavailable' in e:
                    print 'rtu'
                else:
                    print e
                    self.running = False
                    raise

            if specificMessage is not None:
                self.handleMessage(specificMessage)

            try:
                broadcastMessage = self.zmqBroadcast.recv_pyobj(flags=zmq.NOBLOCK)
            except zmq.ZMQError,e:
                if 'Resource temporarily unavailable' in e:
                    pass
                else:
                    self.running = False
                    raise

            if broadcastMessage is not None:
                self.handleBroadcast(broadcastMessage)
                
            time.sleep(0.001)
