import asynchat,asyncore,socket,time

try:
	import config
except ImportError:
	config = None


class altara_socket(asynchat.async_chat):
	def __init__(self, (host, port)):
		asynchat.async_chat.__init__(self)
		self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
		self.set_terminator('\r\n')
		self.data=''
		self.remote=(host,port)
		self.connect(self.remote)
		self.firstSync = 1
		self.modules = {}
		self.uidstore = {} #Create dictionary.
		self.createdClients = {} #Create another dictionary for clients that altara makes.
		self.suid = 100000
	def load(self,modname):
		self.modules[modname] = __import__(modname)
		return self.modules[modname]

	def handle_connect(self):
		#introduce server
		self.sendLine("PASS "+str(config.linkpass)+" TS 6 "+str(config.sid))
		self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD")
		self.sendLine("SERVER "+str(config.servername)+" 1 :"+str(config.serverdescription))
		#Create a client
		self.createClient(config.clientnick,config.clientuser,config.clienthostname,config.clientgecos)
		self.startSyncTS = time.time()

	def get_data(self):
		r=self.data
		self.data=''
		return r
	
	def collect_incoming_data(self, data):
		self.data+=data
	def handle_error(self):
		raise
	#START API
	def sendLine(self,data):
		print "Send: "+str(data)
		self.push(data+'\r\n')
	def createClient(self,cnick,cuser,chost,cgecos):
		self.suid+=1
		cuid = str(config.sid)+str(self.suid)
		#:SID EUID nickname, hopcount, nickTS, umodes, username, visible hostname, IP address, UID, real hostname, account name, gecos
		self.sendLine(':'+str(config.sid)+' EUID '+cnick+' 0 '+str(time.time())+' +i '+cuser+' '+chost+' 0.0.0.0 '+cuid+' 0.0.0.0 0 :'+cgecos) 
		self.sendLine(':'+cuid+' JOIN '+str(time.time())+' '+config.reportchan+' +')
		self.sendLine("MODE "+config.reportchan+" +o "+cuid)
		self.createdClients[cnick] = {'uid': cuid}
		return cuid
	def suidtoNick(self,nick):
		return self.createdClients[nick]['uid']
	def sendPrivmsg(self,sender,target,message):
		self.sendLine(":"+sender+" PRIVMSG "+target+" :"+message)
	def sendNotice(self,sender,target,message):
		self.sendLine(":"+sender+" NOTICE "+target+" :"+message)
	#END API
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
			#Recv: :05K EUID jason 3 1292805989 +i ~jason nat/bikcmp.com/session 0 05KAAANCY * * :Jason
			#Note: could use some cleanup here.
			modes = split[5]
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
			if "o" in modes:
				self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': True, 'modes': modes}
			else:
				self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': False, 'modes': modes}
			for modname,module in self.modules.items():
				if hasattr(module, "onConnect"):
					module.onConnect(self,uid)
		elif split[1] == "ENCAP":
			if split[3] == "OPER":
				uid = split[0].replace(":","")
				self.uidstore[uid]['oper'] = True
			elif split[3] == "SU":
				try:
					uid = split[4]
					newaccount = split[5].replace(":","")
					self.uidstore[uid]['account'] = newaccount
					for modname,module in self.modules.items():
						if hasattr(module, "onLogin"):
							module.onLogin(self,uid,oldhost,newhost)
				except:
					pass
		elif split[1] == "CHGHOST":
			uid = split[2]
			oldhost = self.uidstore[uid]['host']
			newhost = split[3]
			self.uidstore[uid]['host'] = split[3]
			for modname,module in self.modules.items():
				if hasattr(module, "onChghost"):
					module.onChghost(self,uid,oldhost,newhost)
		#Recv: :05CAAA61H NICK TrinityFlash :1292821028
		elif split[1] == "NICK":
			uid = split[0].replace(":","")
			oldnick = self.uidstore[uid]['nick']
			newnick = split[2]
			self.uidstore[uid]['nick'] = newnick
			for modname,module in self.modules.items():
				if hasattr(module, "onNickChange"):
					module.onNickChange(self,uid,oldnick,newnick)
		elif split[1] == "QUIT":
			uid = split[0].replace(":","")
			del self.uidstore[uid]
			for modname,module in self.modules.items():
				if hasattr(module, "onQuit"):
					module.onQuit(self,uid)
		#:SID EUID nickname, hopcount, nickTS, umodes, username, visible hostname, IP address, UID, real hostname, account name, gecos
		elif split[1] == "PRIVMSG":
			target = split[2]
			message = data.split("PRIVMSG "+target+" :")[1]
			uid = split[0].replace(":","")
			nick = self.uidstore[uid]['nick']
			host = self.uidstore[uid]['host']
			user = self.uidstore[uid]['user']
			account = self.uidstore[uid]['account']
			realhost = self.uidstore[uid]['realhost']
			oper = self.uidstore[uid]['oper']
			splitm = message.split(" ")
			if splitm[0].lower() == "modload": #TODO: only ircops can use this feature
				try:
					modtoload = splitm[1]
					self.sendLine("NOTICE "+config.reportchan+" :Loading "+str(modtoload)+" (requested by "+nick+"!"+user+"@"+host+")")
					module = self.load("module_"+modtoload)
					module.modinit(self)
				except Exception,e:
					self.sendLine("NOTICE "+config.reportchan+" :ERROR: "+(str(e)))
				#TODO: Reload/unload
			elif splitm[0] == "info":
				self.sendLine("NOTICE #altara :Info about you: "+nick+"!"+user+"@"+host+" realhost "+realhost+" opered = "+str(oper)+" account = "+account)
			for modname,module in self.modules.items():
				if hasattr(module, "onPrivmsg"):
					#module.onPrivmsg(self,target,uid,nick,host,realhost,account,message)
					module.onPrivmsg(self,uid,target,message)
			    #do other functions here!
			

if __name__ == '__main__':
	if config is None:
		print "Please edit config.py.dist.  After you're done, rename it to config.py and try launching Altara services again."
		exit()

	altara_socket((config.networkIP, config.linkport))
	asyncore.loop()
