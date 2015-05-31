from plugin import plugin
import zmq
import threading

class messagePump(plugin):
    
    def __init__(self):
        super(messagePump, self).__init__()
        self.pluginPushSockets = {}
        self.pluginPullSockets = []
        self.broadcastName = 'inproc://'+self.instanceName
        self.dispatchThread = threading.Thread(target=self.receiving)
        self.dispatchThread.start()

    def connect(self, pluginName):
        pullSocket = self.zmqContext.socket(zqm.PULL)
        pullSocket.connect('inproc://'+pluginName+'_push')
        self.pluginPullSockets.append(pullSocket)
        
        pushSocket = self.zmqContext.socket(zmq.PUSH)
        connectionName = 'inproc://'+self.instanceName+'_'+pluginName+'_pull'
        pushSocket.bind(connectionName)
        self.pluginPushSockets[pluginName] = pushSocket

        return connectionName
        
    def receiving(self):
        while self.running:
            for socket in self.pluginPullSockets:
                msg = None
                
                try:
                    msg = socket.recv_pyobj(flag=zmq.NOBLOCK)
            except zmq.core.error.ZMQError,e:
                if 'Resource temporarily unavailable' in e:
                    pass
                else:
                    raise

                if msg is not None:
                    self.pumpMessage(msg)

    def pumpMessage(self):
        pass
