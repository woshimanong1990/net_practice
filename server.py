# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import socket
import threading
import time


def process_request(clients, conn, addr, lock: threading.Lock):
    with lock:
        if "client1" not in clients:
            client = "client1"
            clients[client] = (addr, conn)
        elif "client2" not in clients:
            client = "client2"
            clients[client] = (addr, conn)
        else:
            conn.close()
            return
    private_addr = conn.recv(1024)
    expect_client = "client2" if client == "client1" else "client1"
    while expect_client not in clients:
        time.sleep(1)
        continue
    public_addr = "{}:{}".format(addr[0], addr[1])
    total_message = "{}|{}".format(public_addr, private_addr)
    print(total_message, client, addr)
    clients[expect_client][1].sendall(total_message.encode())
    clients[expect_client][1].close()
    del clients[expect_client]


def main(host="0.0.0.0", port=50005):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(1)
    s.settimeout(30)
    clients = {}

    while True:
        try:
            conn, addr = s.accept()
        except socket.timeout:
            continue
        lock = threading.Lock()
        t = threading.Thread(target=process_request, args=(clients, conn, addr, lock))
        t.setDaemon(True)
        t.start()


if __name__ == "__main__":
    main()
