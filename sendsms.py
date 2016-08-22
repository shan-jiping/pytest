#coding:gb2312
'''
Created on 2015-07-08

@author: jiping505
'''

import urllib
import urllib2
import sys
from datetime import datetime

#stime = datetime.now()
stime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#stime = ''
sn = 'SDK-BBX-010-18994'
pwd = 'ddc#4dd-'
mobile = '13718534739'
adeps = "%u3010%u4F17%u4FE1%u5728%u7EBF%u3011"
ms='this a test'
context = ms.decode('gb2312')+adeps


data = {}
data['sn'] = sn
data['pwd'] = pwd
data['mobile'] = mobile
data['content'] = context
data['ext'] = ''
data['stime'] = stime
data['rrid'] = ''
url='http://sdk.entinfo.cn:8060/webservice.asmx/SendSMS'
post_data = urllib.urlencode(data)
req = urllib2.urlopen(url,post_data)
content = req.read()

print data
