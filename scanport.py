#coding:utf-8
'''
Created on 2016年7月19日

@author: shan.jiping
'''
from threading import Thread, activeCount
import socket
import os
def test_port(dst,port):
    os.system('title '+str(port))
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        indicator = cli_sock.connect_ex((dst, port))
        if indicator == 0:
            print(port)
        cli_sock.close()
    except:
        pass
if __name__=='__main__':
    dst = '10.10.33.89'

    i = 0
    while i < 65535:
        if activeCount() <= 200:
            Thread(target = test_port, args = (dst, i)).start()

            i = i + 1
    while True:
        if activeCount() == 2:

            break

    input('Finished scanning.')