from math import ceil, sqrt
from threading import Event, Thread, Timer
from datetime import datetime, timedelta
import time

from past.builtins import xrange

from enums import STATE, MSG_TYPE
from nodeServer import NodeServer
from nodeSend import NodeSend
from message import Message
import config


class Node(object):
    NEXT_REQ = 7
    CS_INT = 5

    def __init__(self, id):
        Thread.__init__(self)
        self.id = id
        self.port = config.port + id
        self.daemon = True
        self.lamport_ts = 0
        self.state = STATE.INIT

        self.has_voted = False
        self.voted_request = None
        self.request_queue = []

        # self.voting_set = self._create_voting_set()
        self.num_votes_received = 0
        self.has_inquired = False

        # start the server
        self.server = NodeServer(self)
        self.server.start()

        if id % 2 == 0:
            self.collegues = list(range(0, config.numNodes, 2))
        else:
            self.collegues = list(range(1, config.numNodes, 2))

        self.client = NodeSend(self)

        # Events
        # 1 request enter cs
        # 2 enter cs
        # 3 leave cs
        self.signal_request_cs = Event()
        # initially we request to enter the cs
        self.signal_request_cs.set()
        self.signal_enter_cs = Event()
        self.signal_exit_cs = Event()

        # Timestamp for next expected request/exit
        self.time_request_cs = None
        self.time_exit_cs = None

    # Method to request entering the cs. Broadcasts the message to the whole set
    def request_cs(self, ts):
        self.state = STATE.REQUEST
        self.lamport_ts += 1
        request_msg = Message(msg_type=MSG_TYPE.REQUEST, src=self.id, data="Let me in!!!!")
        # print("Sending a request to enter the cs")
        self.client.multicast(request_msg, self.collegues)
        # set the flag to false indicating we ve already done that action
        self.signal_request_cs.clear()

    # Method when we are in the cs
    def enter_cs(self, ts):
        self.time_exit_cs = ts + timedelta(milliseconds=Node.CS_INT)
        self.state = STATE.HELD
        self.lamport_ts += 1
        # print("Node %i entering cs" % self.id)
        self.signal_enter_cs.clear()

    def exit_cs(self, ts):
        self.time_request_cs = ts + timedelta(milliseconds=Node.NEXT_REQ)
        self.state = STATE.RELEASE
        self.lamport_ts += 1
        # reset votes counter
        self.num_votes_received = 0
        # send a realease message to all sites in the voting set
        release_msg = Message(msg_type=MSG_TYPE.RELEASE, src=self.id)
        self.client.multicast(release_msg, self.collegues)
        self.signal_exit_cs.clear()

    def do_connections(self):
        self.client.build_connection()

    def _state(self):
        timer = Timer(1, self._state)  # Each 1s the function call itself
        timer.start()
        self.curr_time = datetime.now()
        """
        if we have already exectued the cs and the system is in a time greater than the time 
        in which we requested to enter the cs, then we request to enter the cs again
        """
        if self.state == STATE.RELEASE and self.time_request_cs <= self.curr_time:
            if not self.signal_request_cs.is_set():
                print("Please enter")
                self.signal_request_cs.set()
        # if we have all the votes we need, we enter the cs
        elif self.state == STATE.REQUEST and self.num_votes_received == 1:
            if not self.signal_enter_cs.is_set():
                self.signal_enter_cs.set()
        # if we are holding the token, and we have already exited the cs then we set the flag to false
        elif self.state == STATE.HELD and self.time_exit_cs <= self.curr_time:
            if not self.signal_exit_cs.is_set():
                self.signal_exit_cs.set()

        self.wakeupcounter += 1
        if self.wakeupcounter == 2:
            timer.cancel()
            print("Stopping N%i" % self.id)
            self.daemon = False

        else:
            print("This is Node_%i at TS:%i sending a message to my collegues" % (self.id, self.lamport_ts))

            message = Message(msg_type="greetings",
                              src=self.id,
                              data="Hi!, this is Node_%i _ counter:%i" % (self.id, self.wakeupcounter))

            self.client.multicast(message, self.collegues)

    def run(self):
        print("Run Node%i with the follows %s" % (self.id, self.collegues))
        self.client.start()
        self.wakeupcounter = 0
        self._state()
