# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import re
import time

import logging
import threading
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

pattern = re.compile(r"(?P<ip>(\d+\.){3}\d+):(?P<port>\d+)")
PROGRESS_STOP = threading.Event()
# STOP = threading.Event()
lock = threading.Lock()

logging.basicConfig(filename='app.log', filemode='w', format= '%(asctime)s: %(name)s - %(levelname)s -[%(threadName)s]- %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
global_count = 0


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
    print("connect info", local_addr, addr)
    is_first = True
    stop_set_by_self = False
    while True:
        try:
            print("try connect ",  addr)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(local_addr)
            # if is_first:
            #     s.settimeout(5)
            with lock:
                logger.info("lock in **********")
                if stop_event.is_set() and not stop_set_by_self:
                    # 退出后记得清零，不然永远不会请求
                    return None
                logger.info(" event is set:%s", stop_event.isSet())
                s.connect(addr)
                stop_event.set()
                stop_set_by_self = True
                logger.info("*********************, connect success:{}:{}".format(local_addr, addr))
                if is_first:
                    time.sleep(1)
                    s.close()
                    is_first = False
                    time.sleep(3)
                    logger.info("continue here ++++")
                    continue
                logger.info("+++++++++set event++++")

                logger.info("lock out **********")
            logger.info("connected from %s to %s success!", local_addr, addr)
            return s
        except socket.timeout as e:
            continue
        except:
            logger.error("connect to peer error", exc_info=True)
            return None


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


def get_remote_addr(host, port):
    try:
        # local_addr, receive_data, _ = connect_server('192.168.1.2', 123)
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


def start_local_server(public_api_host, public_api_port,  port, host=""):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, int(port)))
    s.listen()
    while True:
        try:
            local_conn, addr = s.accept()
        except:
            logger.error("local server acc")
            continue
        print("++++++ get remote connect")
        stop_event = threading.Event()
        local_addr, public_addr, private_addr = get_remote_addr(public_api_host, public_api_port)
        if not local_addr or not public_addr or not private_addr:
            logger.error("get another connect info error")
            continue
        connect_infos = [(local_addr, public_addr, stop_event), (local_addr, private_addr, stop_event)]
        connect_socket = None
        with ThreadPoolExecutor(max_workers=2) as e:
            tasks = {e.submit(connect_peer, *t): t for t in connect_infos}
            for future in as_completed(tasks):
                info = tasks[future]
                try:
                    connect_socket = future.result()
                    if not connect_socket:
                        continue
                    else:
                        break
                except:
                    logger.error("connect to %s error", info)
                    continue
        if not connect_socket:
            continue
        threads = [
            threading.Thread(target=data_communication, args=(local_conn, connect_socket)),
            threading.Thread(target=data_communication, args=(connect_socket, local_conn)),
        ]
        [t.setDaemon(True) for t in threads]
        [t.start() for t in threads]
        print("++++++++++++++++++++++++")


def main():
    public_api_host = "192.168.1.2"
    public_api_port = "123"
    port = 10028
    start_local_server(public_api_host, public_api_port, port)


if __name__ == "__main__":
    main()
