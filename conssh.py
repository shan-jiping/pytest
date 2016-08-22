#coding:utf-8
'''
Created on 2016年7月21日

@author: shan.jiping
'''
from paramiko import SSHClient,AutoAddPolicy
import socket
import logging
from time import sleep
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='/tmp/pyssh.log',
                    filemode='w')


def check_port(dst,port):
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        indicator = cli_sock.connect_ex((dst, port))
        if indicator == 0:
            return True
        cli_sock.close()
    except:
        pass


def con_ser(host,port=22,username='root',password='root'):
    start_java='/data/server/start.sh'

    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(host, port, username=username, password=password, timeout=4)
    stdin, stdout, stderr = client.exec_command('jps -l |grep -v sun.tools.jps.Jps|wc -l')
    if int(stdout.readlines()[0].replace('\n',''))==1:
        logging.info("The process of existence")
    else:
        logging.info("Server Off")
        logging.info("start the server")
        stdin, stdout, stderr = client.exec_command(start_java)
        for std in stdout.readlines():
            logging.info(std.replace('\n',''),)


    client.close()
serrr=['192.168.30.37','192.168.31.37','192.168.30.102','192.168.31.102','192.168.30.52','192.168.31.52','192.168.30.38','192.168.31.38']
if __name__ == '__main__':
    while True:
        for i in serrr:
            if check_port(i,80)==True:
                logging.info("Server on " +i )
            else:
                logging.info("Server Off  start the server")
                logging.info('connect server '+i )
                con_ser(i)
        sleep(60)