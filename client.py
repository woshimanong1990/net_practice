# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

import threading
import re
import time
import random
import traceback
import logging

pattern = re.compile(r"(?P<ip>(\d+\.){3}\d+):(?P<port>\d+)")
lock = threading.Lock()
logging.basicConfig(filename='app.log', filemode='w', format= '%(asctime)s: %(name)s - %(levelname)s -[%(threadName)s]- %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
global_count = 0
connect_stop = {}


def connect_server(host, port):
    sa = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sa.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sa.connect((host, int(port)))
    priv_addr = sa.getsockname()

    with sa:
        while True:
            priv_addr_str = "{}:{}".format(priv_addr[0], priv_addr[1])
            sa.sendall(priv_addr_str.encode())
            data = sa.recv(1024)
            sa.close()
            return priv_addr, data, sa


def connect_peer(local_addr, addr, stop_event):
    global global_count
    print("connect info", local_addr, addr)

    while True:
        try:
            print("try connect ",  addr)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(local_addr)
            # s.settimeout(3)
            with lock:
                if stop_event.is_set():
                    return
                s.connect(addr)
                stop_event.set()
                logger.info("*********************, connect success:{}:{}".format(local_addr, addr))
                return
        except:
            logger.error("connect peer error", exc_info=True)
            connect_stop[local_addr[1]] = True
            connect_stop[addr[1]] = True
            return


def data_communication(receiver_connect, send_connect):
    while True:
        try:
            data = receiver_connect.recv(1024)
        except:
            logger.error("receive data error", exc_info=True)
            send_connect.close()
            return
        if not data:
            logger.error("receive data empty", exc_info=True)
            send_connect.close()
            return
        try:
            send_connect.sendall(data)
        except:
            logger.error("send data error", exc_info=True)
            receiver_connect.close()
            return


def create_local_bind_connect(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, int(port)))
        return s
    except:
        logger.error("create local bind error", exc_info=True)
        return None


def accept_from_peer(port, local_host, local_port):
    print("accept_from_peer at :%s port" % port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen()
    s.settimeout(5)
    global global_count
    while True:
        try:
            if port in connect_stop:
                return
            local_conn, addr = s.accept()
            logger.info("get new connect from peer:%s", addr)
        except socket.timeout:
            continue
        except:
            logger.error("accept error", exc_info=True)
            continue
        connect_socket = create_local_bind_connect(local_host, local_port)
        if not connect_socket:
            logger.error("create local bind connect error")
            continue
        threads = [
            threading.Thread(target=data_communication, args=(local_conn, connect_socket)),
            threading.Thread(target=data_communication, args=(connect_socket, local_conn)),
        ]
        [t.setDaemon(True) for t in threads]
        [t.start() for t in threads]


def get_remote_addr(host, port):
    try:
        # local_addr, receive_data, _ = connect_server('192.168.1.2', 1234)
        local_addr, receive_data, _ = connect_server(host, port)
        public_addr, private_addr = receive_data.decode().split("|")
        public_match = pattern.search(public_addr)
        private_match = pattern.search(private_addr)
        if not public_match:
            return None, None, None
        if not private_match:
            return None, None, None
        return local_addr, (public_match.groupdict()["ip"], int(public_match.groupdict()["port"])), (private_match.groupdict()["ip"], int(private_match.groupdict()["port"]))
    except:
        logger.error("get remote connect address error", exc_info=True)
        return None, None, None


def create_connect(public_api_host, public_api_port, local_connect_host='192.168.1.2', local_connect_port=22):
    while True:
        local_addr, public_addr, private_addr = get_remote_addr(public_api_host, public_api_port)
        if not local_addr or not public_addr or not private_addr:
            logger.error("get another connect info error")
            continue
        stop_event = threading.Event()
        tasks = [
            threading.Thread(target=accept_from_peer, args=(int(private_addr[1]), local_connect_host, local_connect_port)),
            threading.Thread(target=accept_from_peer, args=(int(local_addr[1]), local_connect_host, local_connect_port)),
            threading.Thread(target=connect_peer, args=(local_addr, public_addr, stop_event)),
            threading.Thread(target=connect_peer, args=(local_addr, private_addr, stop_event))
        ]
        [t.setDaemon(True) for t in tasks]
        [t.start() for t in tasks]



def main():
    try:
        public_api_host = '192.168.1.2'
        public_api_port = '123'
        create_connect(public_api_host, public_api_port)
    except:
        logger.error("main error", exc_info=True)


if __name__ == "__main__":
    # 被动客户端，根据master发送的信息做相应处理
    main()
