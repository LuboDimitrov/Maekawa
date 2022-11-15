from threading import Event, Thread, Timer
from datetime import datetime, timedelta
import time
from nodeServer import NodeServer
from nodeSend import NodeSend
from message import Message
import config
class Node():
    def __init__(self,id):
        Thread.__init__(self)
        self.id = id
        self.port = config.port+id
        self.daemon = True
        self.lamport_ts = 0

        self.server = NodeServer(self)
        self.server.start()

        if id % 2 == 0:
            self.collegues = list(range(0,config.numNodes,2))
        else:
            self.collegues = list(range(1,config.numNodes,2))

        self.client = NodeSend(self)    

    def do_connections(self):
        self.client.build_connection()

    def state(self):
        timer = Timer(1, self.state) #Each 1s the function call itself
        timer.start()
        self.curr_time = datetime.now()
        #wakeup
        #DO shomething

        
        self.wakeupcounter += 1
        if self.wakeupcounter == 2:
            timer.cancel()
            print("Stopping N%i"%self.id)
            self.daemon = False

        else:
            print("This is Node_%i at TS:%i sending a message to my collegues"%(self.id,self.lamport_ts))

            message = Message(msg_type="greetings",
                            src=self.id,
                            data="Hola, this is Node_%i _ counter:%i"%(self.id,self.wakeupcounter))

            self.client.multicast(message, self.collegues)

    def run(self):
        print("Run Node%i with the follows %s"%(self.id,self.collegues))
        self.client.start()
        self.wakeupcounter = 0
        self.state()

