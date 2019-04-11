# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import socket
import threading
import time


def process_request(clients, conn, addr, lock: threading.Lock):
    private_addr = conn.recv(1024)
    with lock:
        if "client1" not in clients:
            clients["client1"] = (private_addr, addr, conn)
        elif "client2" not in clients:
            clients["client2"] = (private_addr, addr, conn)
        else:
            conn.close()
            return

    while len(clients) != 2:
        time.sleep(1)
        continue
    with lock:
        if len(clients) != 2:
            return
        for client in clients:
            expect_client = "client2" if client == "client1" else "client1"
            expect_data = clients[expect_client]
            public_addr_format = "{}:{}".format(expect_data[1][0], expect_data[1][1])
            total_message = "{}|{}".format(public_addr_format, clients[expect_client][0])
            print(total_message, client, addr)
            clients[client][2].sendall(total_message.encode())
            clients[client][2].close()
        clients.pop("client2")
        clients.pop("client1")


def main(host="0.0.0.0", port=1234):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(1)
    s.settimeout(30)
    clients = {}

    while True:
        try:
            conn, addr = s.accept()
            print("get new connect ", addr)
        except socket.timeout:
            continue
        lock = threading.Lock()
        t = threading.Thread(target=process_request, args=(clients, conn, addr, lock))
        t.setDaemon(True)
        t.start()


if __name__ == "__main__":
    main()
