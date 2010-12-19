import asynchat,asyncore,socket,time

try:
	import config
except ImportError:
	config = None
import sqlite3 as sqlite
#~ connection = sqlite.connect(':memory:')
#~ cursor = connection.cursor()
#~ cursor.execute("create table if not exists users (uid,nick,user,host,account,ip,realhost)")
#~ connection.commit()  #Let's try a dict. 
uidstore = {} #Create dictionary
import altaramodule
#05CAAA5J7|noidea`|~noidea`|cpe-098-026-094-124.nc.res.rr.com|*|~noidea`|cpe-098-026-094-124.nc.res.rr.com

class altara_socket(asynchat.async_chat):
	def __init__(self, (host, port)):
		asynchat.async_chat.__init__(self)
		self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
		self.set_terminator('\r\n')
		self.data=''
		self.remote=(host,port)
		self.connect(self.remote)
		self.firstSync = 1
	
	def sendLine(self,data):
		print "Send "+str(data)
		self.push(data+'\r\n')
	def handle_connect(self):
		#introduce server
		self.sendLine("PASS "+str(config.linkpass)+" TS 6 "+str(config.sid))
		self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD")
		self.sendLine("SERVER "+str(config.servername)+" 1 :"+str(config.serverdescription))
		#bring in a client
		#:SID EUID nickname, hopcount, nickTS, umodes, username, visible hostname, IP address, UID, real hostname, account name, gecos
		self.sendLine(':'+str(config.sid)+' EUID '+config.clientnick+' 0 '+str(time.time())+' +i '+config.clientuser+' '+config.clienthostname+' 0.0.0.0 '+str(config.sid)+'AAAAAB 0.0.0.0 0 :'+config.clientgecos) 
		self.sendLine(':31DAAAAAB JOIN %d #altara +' % int(time.time()))
		self.startSyncTS = time.time()

	def get_data(self):
		r=self.data
		self.data=''
		return r
	
	def collect_incoming_data(self, data):
		self.data+=data

	def found_terminator(self):
		data=self.get_data()
		split = str(data).split(" ")
		print "Recv: "+data
		if split[0] == "PING":
			self.sendLine("PONG "+split[1])
			if self.firstSync == 1:
				synctime = float(time.time()) - float(self.startSyncTS)
				self.sendLine("WALLOPS :Synced with network in "+str(synctime)+" seconds.")
				self.firstSync = 0
		elif split[1] == "EUID":
			nick = split[2]
			user = split[6]
			host = split[7]
			if split[10] == "*":
				realhost = split[7]
			else:
				realhost = split[10]
			ip = split[6]
			uid = split[9]
			account = split[11]
			if account == "*":
				account = "None"
			uidstore[uid] = {'nick': nick, 'host': host, 'realhost': realhost, 'account': account}

		#Recv: :05K EUID jason 3 1292733825 +i ~jason nat/bikcmp.com/session 0 05KAAAM8K * * :Jason
		#:SID EUID nickname, hopcount, nickTS, umodes, username, visible hostname, IP address, UID, real hostname, account name, gecos
		elif split[1] == "PRIVMSG":
			target = split[2]
			message = data.split("PRIVMSG "+target+" :")[1]
			uid = split[0].replace(":","")
			nick = uidstore[uid]['nick']
			host = uidstore[uid]['host']
			account = uidstore[uid]['account']
			realhost = uidstore[uid]['realhost']
			altaramodule.onPrivmsg(self,uid,nick,host,realhost,account,message)
			#self.sendLine('NOTICE #altara :'+str(self.uidtonick(split[0].replace(":",""))))
			#self.sendLine("NOTICE #altara :"+str(nick))

			

if __name__ == '__main__':
	if config is None:
		print "Please edit config.py.dist.  After you're done, rename it to config.py and try launching Altara services again."
		exit()

	altara_socket((config.networkIP, config.linkport))
	asyncore.loop()
