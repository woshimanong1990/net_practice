# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import socket
import threading
import re
import time
import random
import traceback
import logging

pattern = re.compile(r"(?P<ip>(\d+\.){3}\d+):(?P<port>\d+)")
STOP = threading.Event()
lock = threading.Lock()
logging.basicConfig(filename='app.log', filemode='w', format= '%(asctime)s: %(name)s - %(levelname)s -[%(threadName)s]- %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
global_count = 0


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
            sa.close()
            return priv_addr, data, sa


def connect_peer(local_addr, addr):
    global global_count
    print("connect info", local_addr, addr)

    while True:
        try:
            print("try connect ",  addr)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(local_addr)
            s.settimeout(3)
            with lock:
                if STOP.is_set():
                    time.sleep(1)
                    continue
                s.connect(addr)
                STOP.set()
                logger.info("*********************, connect success:{}:{}".format(local_addr, addr))
            # data = s.recv(1024)
            # try:
            #     while data:
            #         logger.info("^^ receive from {} ".format(data))
            #         message = "message {} at {}".format(global_count, time.time())
            #         s.sendall(message.encode())
            #         global_count += 1
            #         data = s.recv(1024)
            # except:
            #     logger.error("communication socket error")
            #     time.sleep(1)
            #     s.close()
            #     raise
        except:
            logger.error("connect peer error", exc_info=True)
            time.sleep(1)
            if STOP.is_set():
                STOP.clear()
            continue


def accept_from_peer(port):
    print("accept_from_peer at :%s port" % port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen(1)
    s.settimeout(5)
    global global_count
    while True:
        try:
            conn, addr = s.accept()
            while True:
                data = conn.recv(1024)
                logger.info("+++++ recevie data :%s from %s", data, addr)
                if not data:
                    break
                message = "_-_-==_--{}".format(global_count)
                conn.sendall(message.encode())
                global_count +=1

        except:
            logger.error("accecp error", exc_info=True)
            continue
        else:
            print("Accept %s connected!" % port)
            # STOP.set()


def main():
    try:
        local_addr, receive_data, _ = connect_server('192.168.1.2', 123)
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
    except:
        traceback.print_exc()


if __name__ == "__main__":
    # 被动客户端，根据master发送的信息做相应处理
    main()
