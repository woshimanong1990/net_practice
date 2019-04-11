# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import socket
import time


def main():

    HOST = 'www.baidu.com'  # The remote host
    PORT = 1234  # The same port as used by the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            s.sendall(b'Hello, world')
            data = s.recv(1024)
            print('Received', repr(data))
            time.sleep(1)


if __name__ == "__main__":
    main()
