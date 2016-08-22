#coding:utf-8
import redis

'''
Created on 2016年1月4日

@author: shan.jiping
'''

rhost='10.10.20.60'
rport=6379
r= redis.Redis(host=rhost,port=rport,db=0)
print r.dbsize()

for i in r.info():
    print i,r.info()[i]
