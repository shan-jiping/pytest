#coding=utf-8
'''
Created on 2016年6月22日

@author: shan.jiping
'''
from pymongo import MongoClient

conn=MongoClient('192.168.28.200',27017)   #连接mongo
db=conn.house                               #选择数据库
anjk= db.newhouse.find({ "houseId" : { "$lt" : 0 } }).limit(10000)
conn.close()
atfs=[]

for i in anjk:
    #print i
    #print type(i)
    if len(i['houseImg']['realImgs'])==0:
        pass
    else:
        for l in i['houseImg']['realImgs']:
            atfs.append(l)
    if len(i['houseImg']['apartmentLayoutDiagrams'])==0:
        pass
    else:
        for k in  i['houseImg']['apartmentLayoutDiagrams']:
            atfs.append(k)
    if len(i['houseImg']['planeImgs'])==0:
        pass
    else:
        for m in i['houseImg']['planeImgs']:
            atfs.append(m)
    if len(i['houseImg']['roomDiagrams'])==0:
        pass
    else:
        for n in i['houseImg']['roomDiagrams']:
            atfs.append(n)
    if len(i['houseApartmentLayouts'])==1:
        atfs.append(i['houseApartmentLayouts'][0]['layoutDiagram'])
    else:
        for j in i['houseApartmentLayouts']:
            atfs.append(j['layoutDiagram'])
#print atfs
atfs=list(set(atfs))
print len(atfs)
f=open('anjk','a')
for img in atfs:
    f.write(img+'\n')
print "done"