# Maekawa Algorithm
## Introduction
Maekawa algorithm is a distributed mutual exclusion algorithm that allows a group of nodes or sites to coordinate access to a shared resource in a distributed system. It is a variation of the Ricart-Agrawala algorithm and is used to ensure that only one process at a time can access the shared resource, while allowing other processes to proceed concurrently as long as they do not require access to the shared resource.
It works by using a token that is passed among the processes in the system. When a process wants to access the shared resource, it sends a request message to all other processes in the system. If a process has the token, it immediately sends the token to the requesting process and the requesting process can access the shared resource. If a process does not have the token, it sends an acknowledgement message back to the requesting process and adds itself to a queue of processes waiting for the token. When the requesting process is finished with the shared resource, it sends the token to the next process in the queue, allowing that process to access the shared resource. This process continues until all processes have had an opportunity to access the shared resource.

## Implementation

![alt text](https://github.com/LuboDimitrov/Maekawa/blob/main/Untitled%20Diagram.png)

In our case each node acts both as client and server.

### Client
In the client side, there is a main method called **update()** that executes indefinetly the following 3 methods
* request critical section()
* enter critical section()
* exit critical section()

```python
update():
  self.node.signal_request_cs.wait()
  self.node.request_cs(datetime.now())
  self.node.signal_enter_cs.wait()
  self.node.enter_cs(datetime.now())
  self.node.signal_exit_cs.wait()
  self.node.exit_cs(datetime.now())
```

### Server
The server side handles the requests in a method called **process_message()** that depending on the type of message, executes the corresponding method.

```python
process_message():
  if msg.msg_type == MSG_TYPE.REQUEST:
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
```

**References**
- https://www.geeksforgeeks.org/maekawas-algorithm-for-mutual-exclusion-in-distributed-system/
- https://en.wikipedia.org/wiki/Maekawa%27s_algorithm
- https://github.com/yvetterowe/Maekawa-Mutex
- https://github.com/Sletheren/Maekawa-JAVA
- https://www.weizmann.ac.il/sci-tea/benari/software-and-learning-materials/daj-distributed-algorithms-java
