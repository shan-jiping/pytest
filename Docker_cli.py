#coding:utf-8
'''
Created on 2016年7月15日

@author: shan.jiping
'''
from __future__ import division
from docker import client


docker_url='tcp://10.10.20.94:5555'
cli=client.Client(base_url=docker_url)
all_c= cli.containers(all)
for i in all_c:
    print i
print type(all_c)
print len(all_c)
for i in all_c:
    j=cli.stats(i,stream=False)['memory_stats']
    print  j['usage']/1024/1024,j['limit']/1024/1024
    print "%.4f" %(j['usage']/j['limit'])