# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import socket
import threading
import re
import time
import random

pattern = re.compile(r"(?P<ip>(\d+\.){3}\d+):(?P<port>\d+)")


def connect_server(host, port):
    sa = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sa.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sa.connect((host, port))
    priv_addr = sa.getsockname()

    with sa:
        while True:
            priv_addr_str = "{}:{}".format(priv_addr[0], priv_addr[1])
            sa.sendall(priv_addr_str.encode())
            data = sa.recv(1024)
            return priv_addr, data


def receive_data(peer_socket: socket.socket, addr):
    while True:
        try:
            data = peer_socket.recv(1024)
        except socket.error as e:
            print("receive error", e)
            continue
        if not data:
            return
        print("receive data:{} from {}".format(data.decode(), addr))


def send_message(peer_socket: socket.socket, local_addr):
    while True:
        message = "send message from {} at {}".format(local_addr, time.time())
        peer_socket.sendall(message.encode())
        time.sleep(random.randint(1, 5))


def connect_peer(local_addr, addr):
    print("connect info", local_addr, addr)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(local_addr)
    s.settimeout(30)
    while True:
        try:
            s.connect(addr)
            tasks = []
            t1 = threading.Thread(target=receive_data, args=(s, addr))
            t1.setDaemon(True)
            t1.start()
            tasks.append(t1)
            t2 = threading.Thread(target=send_message, args=(s, local_addr))
            t2.setDaemon(True)
            t2.start()
            tasks.append(t2)
            for t in tasks:
                t.join()

        except socket.error:
            continue
        # except Exception as exc:
        #     logger.exception("unexpected exception encountered")
        #     break
        else:
            print("connected from %s to %s success!" % (local_addr, addr))


def accept_from_peer(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen(1)
    s.settimeout(5)
    while True:
        try:
            conn, addr = s.accept()
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print("recevie data :%s from %s"% (data, addr))
        except socket.timeout:
            continue
        else:
            print("Accept %s connected!" % port)
            # STOP.set()


def main():
    local_addr, receive_data = connect_server('', 50005)
    tasks = []
    try:
        public_addr, private_addr = receive_data.decode().split("|")
        public_match = pattern.search(public_addr)
        private_match = pattern.search(private_addr)
        if not public_match:
            return
        if not private_match:
            return
    except:
        return

    t1 = threading.Thread(target=accept_from_peer, args=(int(local_addr[1]), ))
    t1.start()
    tasks.append(t1)
    t11 = threading.Thread(target=accept_from_peer, args=(int(private_match.groupdict()["port"]),))
    t11.start()
    tasks.append(t11)

    t2 = threading.Thread(target=connect_peer, args=(local_addr, (public_match.groupdict()["ip"], int(public_match.groupdict()["port"]))))
    t2.start()
    tasks.append(t2)
    t21 = threading.Thread(target=connect_peer,
                          args=(local_addr, (private_match.groupdict()["ip"], int(private_match.groupdict()["port"]))))
    t21.start()
    tasks.append(t21)

    for t in tasks:
        t.join()
    print("should not get here")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
