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

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
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


def receive_data(peer_socket: socket.socket, addr):
    logger.info("&&&&&&&&&&&&&& run server from sub thread")
    count = 0
    while True:
        try:
            if count > 10:
                return
            data = peer_socket.recv(1024)
        except:
            logger.error("-------------receive_data error", exc_info=True)
            count += 1
            continue
        if not data:
            return
        logger.info("receive data:{} from {}".format(data.decode(), addr))


def send_message(peer_socket: socket.socket, local_addr):
    global global_count
    while True:
        try:
            message = "send  {} message from {} at {}".format(global_count, local_addr, time.time())
            peer_socket.sendall(message.encode())
            global_count += 1
            print("send success", local_addr)
            time.sleep(1)
        except:
            logger.error("-------------send_message error", exc_info=True)
            return


def connect_peer(local_addr, addr):
    print("connect info", local_addr, addr)

    while True:
        try:
            print("try connect ",  addr)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(local_addr)
            s.settimeout(5)
            with lock:
                if STOP.is_set():
                    time.sleep(1)
                    continue
                s.connect(addr)
                STOP.set()
                logger.info("*********************, connect success:{}:{}".format(local_addr, addr))

            print("connected from %s to %s success!" % (local_addr, addr))

            tasks = []
            t1 = threading.Thread(target=receive_data, args=(s, local_addr))
            t1.setDaemon(True)
            t1.start()
            tasks.append(t1)

            t2 = threading.Thread(target=send_message, args=(s, local_addr))
            t2.setDaemon(True)
            t2.start()
            tasks.append(t2)
            for t in tasks:
                t.join()
            print("+++++++++++++++++++++++++")
            print("+++++++++++++++++++++++++")
            print("+++++++++++++++++++++++++")
            print("+++++++++++++++++++++++++")
            s.close()
            if STOP.is_set():
                STOP.clear()

        except:
            logger.error("-------------some thing wrong", exc_info=True)
            time.sleep(1)
            if STOP.is_set():
                STOP.clear()
            continue

    # except Exception as exc:
    #     logger.exception("unexpected exception encountered")
    #     break


def accept_from_peer(port):
    print("accept_from_peer at :%s port" % port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen(1)
    s.settimeout(5)
    while True:
        try:
            conn, addr = s.accept()
            while True:
                try:
                    data = conn.recv(1024)
                except:
                    logger.error("receive error for main", exc_info=True)
                    continue
                if not data:
                    break
                logger.info("+++++ recevie data :%s from %s", data, addr)
        except :
            logger.error("accept error", exc_info=True)
            time.sleep(1)
            continue
        else:
            print("Accept %s connected!" % port)
            # STOP.set()


def main():
    try:
        local_addr, receive_data, _ = connect_server('192.168.88.201', 50005)
        # local_addr, receive_data, sa = connect_server('www.xiaobaoielts.pw', 50005)
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
        # t3 = threading.Thread(target=beat_test,
        #                        args=(local_addr, ('www.xiaobaoielts.pw', 50005)))
        # t3.start()
        # tasks.append(t3)

        for t in tasks:
            t.join()
        print("should not get here")
        while True:
            time.sleep(1)
    except:
        traceback.print_exc()


if __name__ == "__main__":
    # 主客户端，负责主动请求
    main()
