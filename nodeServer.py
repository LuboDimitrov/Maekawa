import heapq
import select
from threading import Thread
import utils
from enums import MSG_TYPE, STATE
from message import Message
import json


class NodeServer(Thread):
    def __init__(self, node):
        Thread.__init__(self)
        self.node = node

    def run(self):
        self.update()

    def update(self):
        self.connection_list = []
        self.server_socket = utils.create_server_socket(self.node.port)
        self.connection_list.append(self.server_socket)

        while self.node.daemon:
            (read_sockets, write_sockets, error_sockets) = select.select(
                self.connection_list, [], [], 5)
            if not (read_sockets or write_sockets or error_sockets):
                print('NS%i - Timed out' % self.node.id)  # force to assert the while condition
            else:
                for read_socket in read_sockets:
                    if read_socket == self.server_socket:
                        (conn, addr) = read_socket.accept()
                        self.connection_list.append(conn)
                    else:
                        try:
                            msg_stream = read_socket.recvfrom(4096)
                            for msg in msg_stream:
                                try:
                                    ms = json.loads(str(msg, "utf-8"))
                                    self.process_message(ms)
                                except:
                                    None
                        except:
                            read_socket.close()
                            self.connection_list.remove(read_socket)
                            continue

        self.server_socket.close()

    def process_message(self, msg):
        print("Node_%i receive msg: %s\n" % (self.node.id, msg))
        # Doesn't execute the instructions below :(
        print(msg)
        self.node.lamport_ts = max(self.node.lamport_ts + 1, msg.ts)
        if msg.msg_type == MSG_TYPE.REQUEST:
            print("Request")
            self._on_request(msg)
        elif msg.msg_type == MSG_TYPE.GRANT:
            self._on_grant()
        elif msg.msg_type == MSG_TYPE.RELEASE:
            self._on_release()
        elif msg.msg_type == MSG_TYPE.FAIL:
            self._on_fail(msg)
        elif msg.msg_type == MSG_TYPE.INQUIRE:
            self._on_inquire(msg)
        elif msg.msg_type == MSG_TYPE.YIELD:
            self._on_yield()

    def _on_request(self, request_msg):
        # if the current node is in the cs, it queues up the request
        if self.node.state == STATE.HELD:
            heapq.heappush(self.node.request_queue, request_msg)
        # else we check if we have voted or not
        else:
            if self.node.has_voted:
                heapq.heappush(self.node.request_queue, request_msg)
                response_msg = Message(src=self.node.node_id)
                if request_msg < self.node.voted_request and not self.node.has_inquired:
                    response_msg.set_type(MSG_TYPE.INQUIRE)
                    response_msg.set_dest(self.node.voted_request.src)
                    self.node.has_inquired = True
                else:
                    response_msg.set_type(MSG_TYPE.FAIL)
                    response_msg.set_dest(request_msg.src)
                self.node.client.send_message(response_msg, response_msg.dest)
            # if we havent voted, we send a grant
            else:
                self._grant_request(request_msg)

    def _on_release(self):
        # if the queue is not empty we serve the request, otherwise reset the voting flags
        self.node.has_inquired = False
        if self.node.request_queue:
            next_request = heapq.heappop(self.node.request_queue)
            self._grant_request(next_request)
        else:
            self.node.has_voted = False
            self.node.voted_request = None

    # method to handle the voting process
    def _grant_request(self, request_msg):
        grant_msg = Message(msg_type=MSG_TYPE.GRANT,
                            src=self.node.node_id,
                            dest=request_msg.src,
                            )
        self.node.client.send_message(grant_msg, grant_msg.dest)
        self.node.has_voted = True
        self.node.voted_request = request_msg

    # methdo to increase the recieved votes from the other sites
    def _on_grant(self):
        self.node.num_votes_received += 1

    def _on_fail(self, fail_msg):
        pass

    def _on_inquire(self, inquire_msg):
        if self.node.state != STATE.HELD:
            self.node.num_votes_received -= 1
            yield_msg = Message(msg_type=MSG_TYPE.YIELD,
                                src=self.node.node_id,
                                dest=inquire_msg.src)
            self.node.client.send_message(yield_msg, yield_msg.dest)

    # Place the node into its request queue and sends a grant message to the request on top of the priority queue
    def _on_yield(self):
        heapq.heappush(self.node.request_queue, self.node.voted_request)
        self._on_release()
