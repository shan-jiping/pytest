#coding:utf-8
'''
Created on 2015年11月16日

@author: shan.jiping
'''

import datetime
from hashlib import sha256
import urllib
import urllib2
import base64
import hmac
import json
import MySQLdb
import sys

from time import sleep
from sjp.chh import utcToe8
reload(sys)

sys.setdefaultencoding('utf-8')
sys.setrecursionlimit(1000000)          #手动设置递归深度

#utime 参数  青云请求访问使用的是utc0时间  需要将本地时间转化为utc0的时间

#all_instance 用于存储所有云主机的主机配置
all_instance=[]
all_volumeinfo=[]
all_loadbalancer=[]
all_portforward=[]
all_snapshots=[]
all_securitygroup=[]
all_fairerules=[]
all_eips=[]
all_router=[]
#初始化一次青云一次查找数量，青云默认一次最多可以查询100调数据，多余100条数据，需要通过使用offset参数进行调整，青云定义offset为偏移量
total_count=100
#qres 向青云请求url所用到的参数
def utcToe8(utctime):
    if len(utctime)<2:
        return utctime
    else:
        #print utctime ,type(utctime)
        return str(datetime.datetime.strptime(utctime,"%Y-%m-%dT%H:%M:%SZ")+datetime.timedelta(hours=8))
def getdefaultqres():
    utime = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    qres={}
    qres.clear()
    qres={
      'access_key_id':'XXXXXXXXXXXXXXXXXXXXXX',
      'offset':0,
      'signature_method':'HmacSHA256',
      'signature_version':'1',
      'time_stamp':utime,
      'limit':'100',
      'version':'1'
      }
    
    return qres

def getqc_set(qres):
    #通过传入的请求字典拼接访问URL 并添加signature 并想青云API进行访问并将访问的结果json的结构进行保存，并返回查询结果
    #首先拼接请求字符串，并对访问URL编码  然后构造被签名串  之后将API密钥的私钥 ( secret_access_key ) 作为key，生成被签名串的 HMAC-SHA256签名
    #醉生成的签名在进行Base64编码，最有将编码得到的以变量signature 添加到最终访问的URL中   得到最后的访问URL
    qingurl='https://api.qingcloud.com/iaas/?'
    secret_access_key='XXXXXXXXXXXXXXXXXXXXXx'
    aurl=''
    # 拼接url 并将字典中的值进行url encoding 
    for i in sorted(qres):
        if len(aurl) == 0:
            aurl = str(i) + '=' + urllib.quote(str(qres[i]))
        else:
            aurl = aurl + '&' + str(i) + '=' + urllib.quote(str(qres[i]))
    
    string_to_sign ='GET\n/iaas/\n' + aurl
    h = hmac.new(secret_access_key, digestmod=sha256)
    h.update(string_to_sign)
    sign = base64.b64encode(h.digest()).strip()
    signature = urllib.quote_plus(sign)
    furl= qingurl + aurl + '&signature=' + signature
    res=urllib2.urlopen(furl).read()
    res2=json.loads(res)
    json.dumps(res2,encoding="UTF-8",ensure_ascii=False)
    #print furl
    return res2
    
def saveget(sql):
    dbhost='localhost'
    dbuser='root'
    dbpass='root'
    dbbase='test'
    dbsql=sql
    db = MySQLdb.connect(dbhost,dbuser,dbpass,dbbase,charset="utf8")
    cursor = db.cursor()
    #try:
    cursor.execute(dbsql)
    db.commit()
    #except:
    db.rollback()
    #db.close()

#判断一次查询是否将所有数据取回  一次没取完整会调整偏移量参数offset进行再次请求并将请求放入到all_instance中,并将all_instance中的数据根据是否有网络参数区分  分别插入数据库中
def qinginstanceinfo():
    qres=getdefaultqres()
    qres['action']='DescribeInstances'
    qres['zone']='pek2'
    #qres['instances.1']='XXXX' #根据ID请求虚拟机信息
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        instance_set=res2['instance_set']
        total_count = res2['total_count']
        for i in instance_set:
            all_instance.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    
    print 'all_instance number:',len(all_instance)
    for i in all_instance:
        sql=''
        if len(i['vxnets']) > 0:
            sql='''INSERT INTO qcinstance(instance_id,instance_name,vcpus_current,status,memory_current,nic_id,private_ip,lastest_snapshot_time,image_id,image_name,image_size,create_time,status_time,description) VALUE('%s','%s','%d','%s','%d','%s','%s','%s','%s','%s','%d','%s','%s','%s')''' \
            %(i['instance_id'],i['instance_name'],i['vcpus_current'],i['status'],i['memory_current'],i['vxnets'][0]['nic_id'],i['vxnets'][0]['private_ip'],utcToe8(str(i['lastest_snapshot_time'])),i['image']['image_id'],i['image']['image_name'],i['image']['image_size'],utcToe8(str(i['create_time'])),utcToe8(str(i['status_time'])),str(i['description']))
        else:
            
            sql='''INSERT INTO qcinstance(instance_id,instance_name,vcpus_current,status,memory_current,lastest_snapshot_time,image_id,image_name,image_size,create_time,status_time,description) VALUE('%s','%s','%d','%s','%d','%s','%s','%s','%d','%s','%s','%s')''' \
            %(i['instance_id'],i['instance_name'],i['vcpus_current'],i['status'],i['memory_current'],utcToe8(str(i['lastest_snapshot_time'])),i['image']['image_id'],i['image']['image_name'],i['image']['image_size'],utcToe8(str(i['create_time'])),utcToe8(str(i['status_time'])),i['description'])
        print sql
        saveget(sql)
#判断一次查询是否将所有数据取回  一次没取完整会调整偏移量参数offset进行再次请求并将请求放入到all_volumeinfo中,并将all_volumeinfo中的数据根据是否正在呗挂载区分  分别插入数据库中
def qingvolumeinfo():
    qres=getdefaultqres()
    qres['action']='DescribeVolumes'
    qres['zone']='pek2'
    #qres['status']='in-use'   #根据ID请求硬盘信息

    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        volume_set=res2['volume_set']
        total_count = res2['total_count']
        for i in volume_set:
            all_volumeinfo.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    
    print 'all_volume number:',len(all_volumeinfo)
    #print all_volumeinfo
    for i in all_volumeinfo:
        sql=''
        if i['status'] == 'in-use':
            sql='''INSERT INTO qcvolume(volume_id,volume_name,status,size,instance_id,instance_name,device,create_time,status_time,description) VALUES ('%s','%s','%s','%d','%s','%s','%s','%s','%s','%s')''' %(i['volume_id'],i['volume_name'],i['status'],i['size'],i['instance']['instance_id'],i['instance']['instance_name'],i['instance']['device'],utcToe8(i['create_time']),utcToe8(i['status_time']),i['description'])
            #print 'ID:' + i['volume_id'].encode('utf-8') + ' 名称：' + i['volume_name'].encode('utf-8') + ' 状态：' + i['status'].encode('utf-8') + ' 容量：' + str(i['size']) + 'G 挂载主机ID：' + i['instance']['instance_id'].encode('utf-8') +' 挂载主机：' + i['instance']['instance_name'].encode('utf-8') + ' 挂载位置：' + i['instance']['device'].encode('utf-8') + ' 创建时间：' + str(i['create_time']) + ' 最后状态改变时间：' + str(i['status_time']) + ' 过度状态：' + str(i['transition_status']) + ' 描述：' + str(i['description'])
        else:
            sql='''INSERT INTO qcvolume(volume_id,volume_name,status,size,create_time,status_time,description) VALUE('%s','%s','%s','%d','%s','%s','%s')''' %(i['volume_id'],i['volume_name'],i['status'],i['size'],utcToe8(i['create_time']),utcToe8(i['status_time']),i['description'])
            #print 'ID:' + i['volume_id'].encode('utf-8') + ' 名称：' + i['volume_name'].encode('utf-8') + ' 状态：' + i['status'].encode('utf-8') + ' 容量：' + str(i['size']) + 'G 创建时间：' + str(i['create_time']) + ' 最后状态改变时间：' + str(i['status_time']) + ' 过度状态：' + str(i['transition_status']) + ' 描述：' + str(i['description'])
        print sql
        
        saveget(sql)
#判断一次查询是否将所有数据取回  一次没取完整会调整偏移量参数offset进行再次请求并将请求放入到all_loadbalancer中,并将all_loadbalancer中的数据插入数据库中
def qingLoadBalancers ():
    qres=getdefaultqres()
    qres['action']='DescribeLoadBalancers'
    qres['zone']='pek2'
    qres['verbose']=1    #要求返回listeners列表
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        LoadBalancers=res2['loadbalancer_set']
        total_count = res2['total_count']
        for i in LoadBalancers:
            all_loadbalancer.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    print 'all_loadbalancer number:',len(all_loadbalancer)
    #print all_loadbalancer
    for i in all_loadbalancer:
        eip=''
        if len(i['listeners'])>0:
            for j in i['listeners']:
                lbsql='''INSERT INTO loadbalancer_policy(loadbalancer_id,forwardfor,listener_option,listener_protocol,server_certificate_id,backend_protocol,healthy_check_method,session_sticky,timeout,loadbalancer_listener_name,disabled,create_time,healthy_check_option,balance_mode,loadbalancer_listener_id,listener_port) VALUE("%s","%d","%d","%s","%s","%s","%s","%s","%d","%s","%d","%s","%s","%s","%s","%d") ''' \
                %(j['loadbalancer_id'],j['forwardfor'],j['listener_option'],j['listener_protocol'],j['server_certificate_id'],j['backend_protocol'],j['healthy_check_method'],j['session_sticky'],j['timeout'],j['loadbalancer_listener_name'],j['disabled'],utcToe8(j['create_time']),j['healthy_check_option'],j['balance_mode'],j['loadbalancer_listener_id'],j['listener_port'])
                print lbsql
                saveget(lbsql)
        if len(i['eips'])>0:
            for m in i['eips']:
                eip=eip+"[" + m['eip_id'] + "]"
        sql='''INSERT INTO loadbalancer(loadbalancer_id,loadbalancer_name,description,is_applied,status,eip_id,create_time,status_time,security_group_id) VALUE("%s","%s","%s","%s","%s","%s","%s","%s","%s")''' %(i['loadbalancer_id'],i['loadbalancer_name'],i['description'],i['is_applied'],i['status'],eip,utcToe8(i['create_time']),utcToe8(i['status_time']),i['security_group_id'])
        print sql
        saveget(sql)
#判断一次查询是否将所有数据取回  一次没取完整会调整偏移量参数offset进行再次请求并将请求放入到all_portforward中,并将all_portforward中的数据插入数据库中
def qingPortForward():
    qres=getdefaultqres()
    qres['action']='DescribeRouterStatics'
    qres['zone']='pek2'
    qres['static_type']='1'
    qres['verbose']=0    
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        PortForward=res2['router_static_set']
        total_count = res2['total_count']
        for i in PortForward:
            all_portforward.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    print 'all_portforward number:',len(all_portforward)
    
    for i in all_portforward:
        #print 'router_id:' + i['router_id'] + ' router_static_id:' + i['router_static_id'] + ' static_type:' + str(i['static_type']) + ' router_static_name:' + i['router_static_name'] + ' disabled:' + str(i['disabled']) + ' create_time:' + i['create_time'] + ' val1:' + i['val1'] + ' val2:' + i['val2'] + ' val3:' + i['val3'] + ' val4:' + i['val4'] + ' val5:' + i['val5'] + ' val6:' + i['val6'] 
        sql = '''INSERT INTO portforward(router_id,router_static_id,static_type,router_static_name,disabled,create_time,dstport,forwardip,srcport,protocol) VALUE("%s","%s",%d,"%s",%d,"%s","%s","%s","%s","%s")''' \
        %(i['router_id'],i['router_static_id'],i['static_type'],i['router_static_name'],i['disabled'],utcToe8(i['create_time']),i['val1'],i['val2'],i['val3'],i['val4'])
        print sql
        saveget(sql)
        
def qingSnapshots():
    qres=getdefaultqres()
    qres['action']='DescribeSnapshots'
    qres['zone']='pek2'
    qres['verbose']=1
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        Snapshots=res2['snapshot_set']
        total_count = res2['total_count']
        for i in Snapshots:
            all_snapshots.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    print 'all_snapshots number:',len(all_snapshots)
    
    for i in all_snapshots:
        #snapshots_resource=''
        #if len(i['resource'])>0:
        #    for k,v in i['resource'].items():
        #        snapshots_resource= snapshots_resource + k + ':' + v + ' '
        if i.has_key('total_size'):
            pass
        else:
            i['total_size']=0
        
        sql = '''INSERT INTO snapshots(status,snapshot_name,snapshot_id,description,total_size,tags,parent_id,provider,status_time,size,is_taken,snapshot_time,root_id,visibility,virtual_size,resource_id,resource_type,is_head,snapshot_type,create_time) \
        VALUE("%s","%s","%s","%s","%d","%s","%s","%s","%s","%d","%d","%s","%s","%s","%d","%s","%s","%d","%d","%s")'''  \
        %(i['status'],i['snapshot_name'],i['snapshot_id'],i['description'],i['total_size'],i['tags'],i['parent_id'],i['provider'],utcToe8(i['status_time']),i['size'],i['is_taken'],utcToe8(i['snapshot_time']),i['root_id'],i['visibility'],i['virtual_size'],i['resource']['resource_id'],i['resource']['resource_type'],i['is_head'],i['snapshot_type'],utcToe8(i['create_time']))
        #print sql
        saveget(sql)
def qingSecurityGroups():
    qres=getdefaultqres()
    qres['action']='DescribeSecurityGroups'
    qres['zone']='pek2'
    qres['verbose']=1
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        securitygroup=res2['security_group_set']
        total_count = res2['total_count']
        for i in securitygroup:
            all_securitygroup.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    print 'all_securitygroup number:',len(all_securitygroup)

    for i in all_securitygroup:
        print i
        if len(i['resources']):
            resources_id=''
            resources_type=''
            for j in i['resources']:

                resources_id=resources_id + "["+j['resource_id'] +"]"
                resources_type=resources_type + "[" +j['resource_type'] + "]"
            sql = '''INSERT INTO securitygroup(is_applied,description,tags,security_group_name,is_default,create_time,security_group_id,resources_id,resources_type) VALUE("%d","%s","%s","%s","%d","%s","%s","%s","%s")''' %(i['is_applied'],i['description'],i['tags'],i['security_group_name'],i['is_default'],utcToe8(i['create_time']),i['security_group_id'],resources_id,resources_type)
        else:
            sql = '''INSERT INTO securitygroup(is_applied,description,tags,security_group_name,is_default,create_time,security_group_id) VALUE("%d","%s","%s","%s","%d","%s","%s")''' %(i['is_applied'],i['description'],i['tags'],i['security_group_name'],i['is_default'],utcToe8(i['create_time']),i['security_group_id'])
        #print sql
        
        saveget(sql)
def qingfairerules():
    qres=getdefaultqres()
    qres['action']='DescribeSecurityGroupRules'
    qres['zone']='pek2'
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        securitygroup=res2['security_group_rule_set']
        total_count = res2['total_count']
        for i in securitygroup:
            all_fairerules.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    print 'all_fairerules number:',len(all_fairerules)
    for i in all_fairerules:
        sql = '''INSERT INTO firerules(priority,direction,protocol,security_group_id,disabled,action,security_group_rule_id,security_group_rule_name,startport,stopport,srcip) VALUE("%d","%d","%s","%s","%d","%s","%s","%s","%s","%s","%s")''' %(i['priority'],i['direction'],i['protocol'],i['security_group_id'],i['disabled'],i['action'],i['security_group_rule_id'],i['security_group_rule_name'],i['val1'],i['val2'],i['val3'])
        print sql
        saveget(sql)

    
#添加硬盘  默认300G
def qingAddVolume(volumeSize=300):
    qres=getdefaultqres()
    qres['action']='CreateVolumes'  #创建硬盘请求
    qres['size']=volumeSize  #硬盘容量，目前可创建最小 10G，最大 500G 的硬盘， 在此范围内的容量值必须是 10 的倍数
    qres['volume_name']='python-test-sjp' #硬盘名称
    qres['volume_type']=2               #硬盘类型 性能型是 0  超高性能型是 3 (只能与超高性能主机挂载，目前只支持北京2区)， 容量型因技术升级过程中，在各区的 type 值略有不同: 北京1区，亚太1区：容量型是 1 北京2区，广东1区：容量型是 2
    qres['count']=1         #创建硬盘的数量，默认是1
    qres['zone']='pek2'
    newVolume=getqc_set(qres)
    print "硬盘ID：" + str(newVolume['volumes'])
    return newVolume
def qingAddInstance():
    volumeSize=300          #添加硬盘大小    调用添加硬盘方法中参数  如果不传该参数 默认硬盘大小为300G  
    addvolume=qingAddVolume(volumeSize)
    volumeId=addvolume['volumes'][0]
    print "等待创建硬盘..."
    while True:
        sleep(30)
        volume_status=qingvolumestatus(volumeId)
        print "volume_status:" + volume_status
        if volume_status=='available' :
            print "创建硬盘成功"
            break
        elif volume_status=='pending':
            pass
        else:
            print "发生异常，请检查"
            exit
        
    #volumeId='vol-9mgqmwp5'
    qres=getdefaultqres()
    vxnet9='vxnet-gyxpc7g'
    lip='192.168.9.225'
    vxnetIP= vxnet9 + "|" + lip
    qres['vxnets.1']=vxnetIP
    qres['action']='RunInstances'
    qres['image_id']='centos66x64a'
    qres['cpu']=1
    qres['memory']=2048
    qres['instance_name']='python-test-sjp'
    qres['login_mode']='passwd'
    qres['login_passwd']='JY123qwe'
    qres['volumes.1']=volumeId
    qres['zone']='pek2'
    #print qres
    newInstance=getqc_set(qres)
    print newInstance
#获取公网信息
def qingEips():
    qres=getdefaultqres()
    qres['action']='DescribeEips'
    qres['verbose']=0
    qres['zone']='pek2'
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        alleip=res2['eip_set']
        total_count = res2['total_count']
        for i in alleip:
            all_eips.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    print 'all_eip number:',len(all_eips)
    for j in all_eips:
        sql='''INSERT INTO eip(status,resource_name,resource_type,resource_id,eip_id,description,tags,eip_name,icp_codes,billing_mode,bandwidth,create_time,status_time,eip_addr,alarm_status) VALUE("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%d","%s","%s","%s","%s")''' \
        %(j['status'],j['resource']['resource_name'],j['resource']['resource_type'],j['resource']['resource_id'],j['eip_id'],j['description'],j['tags'],j['eip_name'],j['icp_codes'],j['billing_mode'],j['bandwidth'],utcToe8(str(j['create_time'])),utcToe8(str(j['status_time'])),j['eip_addr'],j['alarm_status'])
        #print sql
        saveget(sql)
        
#获取路由信息
def qingRouters():
    qres=getdefaultqres()
    qres['action']='DescribeRouters'
    qres['verbose']=1
    qres['zone']='pek2'
    while True :
        print 'offset:' + str(qres['offset'])
        res2=getqc_set(qres)
        allrouter=res2['router_set']
        total_count = res2['total_count']
        for i in allrouter:
            all_router.append(i)
        qres['offset']=qres['offset']+100
        if total_count-qres['offset'] < 0:
            break
    print 'all_router number:',len(all_router)
    for j in all_router:
        vxnet=''
        for k in j['vxnets']:
            vxnet=vxnet + "[" + k['vxnet_id'] + "]"
        sql='''INSERT INTO router(router_id,router_name,status,description,tags,is_applied,router_type,eip_name,eip_id,eip_addr,dns_aliases,create_time,private_ip,status_time,vxnets,alarm_status,security_group_id,features) VALUE("%s","%s","%s","%s","%s","%d","%d","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%d")''' \
        %(j['router_id'],j['router_name'],j['status'],j['description'],j['tags'],j['is_applied'],j['router_type'],j['eip']['eip_name'],j['eip']['eip_id'],j['eip']['eip_addr'],j['dns_aliases'],utcToe8(j['create_time']),j['private_ip'],utcToe8(j['status_time']),vxnet,j['alarm_status'],j['security_group_id'],j['features'])
        #print sql
        saveget(sql)
def qingjobstatus(job_id):
    qres=getdefaultqres()
    qres['action']='DescribeJobs'
    qres['zone']='pek2'
    qres['job.1']=job_id
    res2=getqc_set(qres)
    job_status=res2['job_set'][0]['status']
    return job_status
def qingvolumestatus(volume_id):
    qres=getdefaultqres()
    qres['action']='DescribeVolumes'
    qres['zone']='pek2'
    qres['volumes.1']=volume_id
    res2=getqc_set(qres)
    volume_status=res2['volume_set'][0]['status']
    return volume_status
def GetEstimatedConsumption():
    qres=getdefaultqres()
    qres['action']='GetEstimatedConsumption'
    qres['zone']='pek2'
    res2=getqc_set(qres)
    estimated_consumption_set=res2['estimated_consumption_set']
    #print res2 
    #print estimated_consumption_set
    print '预计每天总消费' + res2['total_day']
    print " 资源名称         每小时      每天        每月      每年"
    for i in estimated_consumption_set:
        print i['resource_type'] + ' ' + i['hour'] + '  ' + i['day'] +'  ' +i['month'] + '  ' +i['month']
def GetBalance():
    qres=getdefaultqres()
    qres['action']='GetBalance'
    qres['user']='usr-Fo9Aqbdq'
    res2=getqc_set(qres)
    #print res2
    print "账户余额" + res2['balance']
#调用方法请 分别调用 由于每个查询数据中加入参数不同  在一次性执行中由于请求的参数不同  会导致 请求数据返回为空
qi=qinginstanceinfo()        #获取所有虚拟机信息程序入口
#getVolume=qingvolumeinfo()   #获取所有硬盘信息程序入口
#getLoadBalancers=qingLoadBalancers()    #获取所有负载均衡信息程序入口
#portforward=qingPortForward()       #获取所有路由信息程序入口  主要显示端口转发
#snapshots=qingSnapshots()           #获取所有备份信息程序入口
#firewall=qingSecurityGroups()       #获取所有防火墙信息
#firerules=qingfairerules()          #获取所有端口转发规则
#addvolume=qingAddVolume()            #添加硬盘
#addInstance=qingAddInstance()           #添加虚拟机
#eips=qingEips()                         #公网IP
#rout=qingRouters()                      #路由信息
#Estimated=GetEstimatedConsumption()                    #获取消费预估信息
#balance=GetBalance()                                                #获取指定用户的账目信息
