from plugin import plugin
import imp
import os
import inspect
import zmq
import threading
from watchdog.observers import Observer

class messagePump(plugin):
    
    def __init__(self):
        super(messagePump, self).__init__()
        self.pluginPushSockets = {}
        self.pluginPullSockets = []
        self.broadcastName = 'inproc://'+self.instanceName
        self.broadcastSocket = self.zmqContext.socket(zmq.PUB)
        self.broadcastSocket.bind(self.broadcastName)
        self.connectPlugins()
        self.attach(self)
        self.dispatchThread = threading.Thread(target=self.receiving)
        self.dispatchThread.start()

    def connectPlugins(self):
        directory = '.'
        filename = inspect.getfile(self.__class__)
        filenameParts = filename.split('/')
        if len(filenameParts) > 1:
            directory = '/'.join(filenameParts[:-1])
        pluginFiles = [pf for pf in os.listdir(directory) if pf != 'messagePump.py' and pf != 'plugin.py' and pf.endswith('.py') and not pf.startswith('__') and not pf.startswith('.#')]
        for pluginFile in pluginFiles:
            className = pluginFile.split('/')[-1].split('.')[0]
            mod = imp.load_source(className, pluginFile)
            cls = getattr(mod, className)
            plug = cls()
            plug.attach(self)            

    def connect(self, pluginName):
        pullSocket = self.zmqContext.socket(zmq.PULL)
        pullSocket.connect('inproc://'+pluginName+'_push')
        self.pluginPullSockets.append(pullSocket)
        
        pushSocket = self.zmqContext.socket(zmq.PUSH)
        connectionName = 'inproc://'+self.instanceName+'_'+pluginName+'_pull'
        pushSocket.bind(connectionName)
        self.pluginPushSockets[pluginName] = pushSocket

        return connectionName
        
    def killThreads(self):
        super(messagePump, self).killThreads()
        self.dispatchThread.abort()

    def handleMessage(self, message):
        pass

    def handleBroadcast(self, message):
        pass

    def receiving(self):
        while self.running:
            for socket in self.pluginPullSockets:
                msg = None
                
                try:
                    msg = socket.recv_pyobj(flags=zmq.NOBLOCK)
                except zmq.ZMQError,e:
                    if 'Resource temporarily unavailable' in e:
                        pass
                    else:
                        self.killThreads()
                        raise
                    
                if msg is not None:
                    self.pumpMessage(msg)

    def pumpMessage(self):
        pass
