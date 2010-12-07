import time
from time import sleep
import random,string,socket,re
try:
	import config
except:
	print "Please edit config.py.dist, then rename it to config.py and try launching altara services again."


def srvsend(data):
	print "Send: "+repr(data)
	irc.send(data+"\r\n")

tmp1=0
queue = '' # set once.
irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
irc.connect ( ( config.netw.orkIP, config.linkport ) )
while True:
	tmp = irc.recv(1024)
	if tmp == '': close()
	queue = queue + tmp
	for item in queue.split('\r\n'):
		if not item.endswith('\r\n'):
		  if item != '':
			queue = queue[len(item)+2:]
			print "Recv: "+repr(item)
			splitmsg = str(item).split(" ")
			#handle_data.handle(irc,str(item))
			if "NOTICE * :*** Found your hostname" in item and tmp1 != 1:
				tmp1=1
				srvsend("PASS "+config.linkpass+" TS 6 "+config.sid)
				srvsend("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD")
				srvsend("SERVER "+config.servername+" 1 :"+config.serverdescription)
			if newmsg[0] == "PING":
				srvsend("PONG "+newmsg[1])
