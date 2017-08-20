#! /usr/bin/python

import os
import sys
import subprocess
import json
import argparse
import io
import time


parser = argparse.ArgumentParser(description='Circuit Pusher')
parser.add_argument('--controller', dest='controllerRestIp', action='store', default='localhost:8080', help='controller IP:RESTport, e.g., localhost:8080 or A.B.C.D:8080')
parser.add_argument('--add', dest='action', action='store_const', const='add', default='add', help='action: add, delete')
parser.add_argument('--delete', dest='action', action='store_const', const='delete', default='add', help='action: add, delete')
parser.add_argument('--type', dest='type', action='store', default='ip', help='valid types: ip')
parser.add_argument('--src', dest='srcAddress', action='store', default='0.0.0.0', help='source address: if type=ip, A.B.C.D')
parser.add_argument('--dst', dest='dstAddress', action='store', default='0.0.0.0', help='destination address: if type=ip, A.B.C.D')
parser.add_argument('--name', dest='circuitName', action='store', default='circuit-1', help='name for circuit, e.g., circuit-1')

#user catches
if len(sys.argv) == 1:
 command = './circuitpusher.py -h'
 instruct = os.popen(command).read()
 print instruct
 exit(1)
elif sys.argv[1] == "help":
 command = './circuitpusher.py -h'
 instruct = os.popen(command).read()
 print instruct
 exit(1)

#parse arguments
args = parser.parse_args()
print args

controllerRestIp = "192.168.150.1:8080"
print controllerRestIp

# first check if a local file exists, which needs to be updated after add/delete
if os.path.exists('./circuits.json'):
    circuitDb = open('./circuits.json','r')
    lines = circuitDb.readlines()
    circuitDb.close()
else:
    lines={}

if args.action=='add':

    circuitDb = open('./circuits.json','a')
    
    for line in lines:
        data = json.loads(line)
        if data['name']==(args.circuitName):
            print "Circuit %s exists already. Use new name to create." % args.circuitName
            sys.exit()
        else:
            circuitExists = False
    
    # retrieve source and destination device attachment points
    # using DeviceManager rest API 
    
    command = "curl -s http://%s/wm/device/" % (controllerRestIp)
    result = os.popen(command).read()
    parsedResult = json.loads(result)
    print command
    for parameter in parsedResult:
         if parameter['ipv4']:
             if parameter['ipv4'][0]==args.srcAddress:
                 parameterResult=parameter
    sourceSwitch = parameterResult['attachmentPoint'][0]['switchDPID']
    sourcePort = parameterResult['attachmentPoint'][0]['port']
    
    command = "curl -s http://%s/wm/device/" % (controllerRestIp)
    result = os.popen(command).read()
    parsedResult = json.loads(result)
    print command+"\n"
    for parameter in parsedResult:
         if parameter['ipv4']:
             if parameter['ipv4'][0]==args.dstAddress:
                 parameterResult=parameter
    destSwitch = parameterResult['attachmentPoint'][0]['switchDPID']
    destPort = parameterResult['attachmentPoint'][0]['port']
    
    print "Creating circuit:"
    print "from source device at switch %s port %s" % (sourceSwitch,sourcePort)
    print "to destination device at switch %s port %s"% (destSwitch,destPort)
    
    # retrieving route from source to destination
    # using Routing rest API
    
    command = "curl -s http://%s/wm/topology/route/%s/%s/%s/%s/json" % (controllerRestIp, sourceSwitch, sourcePort, destSwitch, destPort)
    
    result = os.popen(command).read()
    parsedResult = json.loads(result)

    print command+"\n"
    print result+"\n"

    for i in range(len(parsedResult)):
        if i % 2 == 0:
            ap1Dpid = parsedResult[i]['switch']
            ap1Port = parsedResult[i]['port']
            print ap1Dpid, ap1Port
            
        else:
            ap2Dpid = parsedResult[i]['switch']
            ap2Port = parsedResult[i]['port']
            print ap2Dpid, ap2Port
            
            command = "curl -s -d '{\"switch\": \"%s\", \"name\":\"%s\", \"src-ip\":\"%s\", \"dst-ip\":\"%s\", \"ether-type\":\"%s\", \"cookie\":\"0\", \"priority\":\"32768\", \"ingress-port\":\"%s\",\"active\":\"true\", \"actions\":\"output=%s\"}' http://%s/wm/staticflowentrypusher/json" % (ap1Dpid, ap1Dpid+"."+args.circuitName+".f", args.srcAddress, args.dstAddress, "0x800", ap1Port, ap2Port, controllerRestIp)
            #result = os.popen(command).read()
           

            command = "curl -s -d '{\"switch\": \"%s\", \"name\":\"%s\", \"ether-type\":\"%s\", \"cookie\":\"0\", \"priority\":\"32768\", \"ingress-port\":\"%s\",\"active\":\"true\", \"actions\":\"output=%s\"}' http://%s/wm/staticflowentrypusher/json" % (ap1Dpid, ap1Dpid+"."+args.circuitName+".farp", "0x806", ap1Port, ap2Port, controllerRestIp)
            #result = os.popen(command).read()
            


            command = "curl -s -d '{\"switch\": \"%s\", \"name\":\"%s\", \"src-ip\":\"%s\", \"dst-ip\":\"%s\", \"ether-type\":\"%s\", \"cookie\":\"0\", \"priority\":\"32768\", \"ingress-port\":\"%s\",\"active\":\"true\", \"actions\":\"output=%s\"}' http://%s/wm/staticflowentrypusher/json" % (ap1Dpid, ap1Dpid+"."+args.circuitName+".r", args.dstAddress, args.srcAddress, "0x800", ap2Port, ap1Port, controllerRestIp)
            #result = os.popen(command).read()
           

            command = "curl -s -d '{\"switch\": \"%s\", \"name\":\"%s\", \"ether-type\":\"%s\", \"cookie\":\"0\", \"priority\":\"32768\", \"ingress-port\":\"%s\",\"active\":\"true\", \"actions\":\"output=%s\"}' http://%s/wm/staticflowentrypusher/json" % (ap1Dpid, ap1Dpid+"."+args.circuitName+".rarp", "0x806", ap2Port, ap1Port, controllerRestIp)
            #result = os.popen(command).read()
           
            
            # store created circuit attributes in local ./circuits.json
            datetime = time.asctime()
            circuitParams = {'name':args.circuitName, 'Dpid':ap1Dpid, 'inPort':ap1Port, 'outPort':ap2Port, 'datetime':datetime}
            str = json.dumps(circuitParams)
            circuitDb.write(str+"\n")

        # confirm successful circuit creation
        # using controller rest API
            
        command="curl -s http://%s/wm/core/switch/all/flow/json| python -mjson.tool" % (controllerRestIp)
        #result = os.popen(command).read()
        print command + "\n" + result

elif args.action=='delete':
    
    circuitDb = open('./circuits.json','w')                                 

    circuitExists = False

    for line in lines:
        data = json.loads(line)
        if data['name']==(args.circuitName):
            circuitExists = True

            sw = data['Dpid']
            print data, sw

            command = "curl -X DELETE -d '{\"name\":\"%s\", \"switch\":\"%s\"}' http://%s/wm/staticflowentrypusher/json" % (sw+"."+args.circuitName+".f", sw, controllerRestIp)
            #result = os.popen(command).read()

            command = "curl -X DELETE -d '{\"name\":\"%s\", \"switch\":\"%s\"}' http://%s/wm/staticflowentrypusher/json" % (sw+"."+args.circuitName+".farp", sw, controllerRestIp)
            #result = os.popen(command).read()

            command = "curl -X DELETE -d '{\"name\":\"%s\", \"switch\":\"%s\"}' http://%s/wm/staticflowentrypusher/json" % (sw+"."+args.circuitName+".r", sw, controllerRestIp)
            #result = os.popen(command).read()

            command = "curl -X DELETE -d '{\"name\":\"%s\", \"switch\":\"%s\"}' http://%s/wm/staticflowentrypusher/json" % (sw+"."+args.circuitName+".rarp", sw, controllerRestIp)
            #result = os.popen(command).read()         
            
        else:
            circuitDb.write(line)

    circuitDb.close()

    if not circuitExists:
        print "specified circuit does not exist"
        sys.exit()
