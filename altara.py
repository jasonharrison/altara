#Note: before you do anything with this in production, DISABLE D-EXEC!


import asynchat,asyncore,socket,time,re

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
		self.nickstore = {}
		self.chanstore = {}
		self.suid = 100000
		self.altaraversion = "Altara-git 0.03 [TS6]"
		self.reportchan = config.reportchan
		self.onloadmodules = config.onloadmodules
	def handle_connect(self):
		#introduce server
		self.sendLine("PASS "+str(config.linkpass)+" TS 6 "+str(config.sid))
		self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD")
		self.sendLine("SERVER "+str(config.servername)+" 1 :"+str(config.serverdescription))
		#Create a client
		self.createClient(config.clientnick,config.clientuser,config.clienthostname,config.clientgecos)
		self.startSyncTS = time.time()
		#Load modules
		if self.onloadmodules != '':
			for modtoload in self.onloadmodules.split(" "):
				module = self.load("module_"+modtoload)
				module.modinit(self)


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
	def AccountLogin(self,uid,accountname):
		self.sendLine(':'+config.sid+' ENCAP * SU '+uid+' :'+accountname)
		self.uidstore[uid]['account'] = accountname
	def AccountLogout(self,uid):
		self.sendLine(':'+config.sid+' ENCAP * SU :'+uid)
		self.uidstore[uid]['account'] = 'None'
		for modname,module in self.modules.items():
			if hasattr(module, "onLogin"):
				module.onLogin(self,uid,oldhost,newhost)
	def clientChghost(self,uid,newhost):
		oldhost = self.uidstore[uid]['host']
		self.sendLine("CHGHOST "+str(uid)+" "+str(newhost))
		self.uidstore[uid]['host'] = str(newhost)
		for modname,module in self.modules.items():
			if hasattr(module, "onChghost"):
				module.onChghost(self,uid,oldhost,newhost)
	
	def clientJoin(self,client,channel):
		self.sendLine(':'+client+' JOIN '+str(time.time())+' '+channel+' +')
		#self.sendLine("MODE "+channel+" +o "+client)
	def clientPart(self,client,channel,reason):
		self.sendLine(':'+client+' PART '+channel+' :'+reason)
	def clientKill(self,client,killee,reason):
		cserver = config.servername
		chost = self.uidstore[client]['host']
		cuser = self.uidstore[client]['user']
		cnick = self.uidstore[client]['nick']
		self.sendLine(":"+client+" KILL "+killee+" :"+cserver+"!"+chost+"!"+cuser+"!"+cnick+" ("+reason+")") #needs work.
	def createClient(self,cnick,cuser,chost,cgecos):
		self.suid+=1
		cuid = str(config.sid)+str(self.suid)
		#:SID EUID nickname, hopcount, nickTS, umodes, username, visible hostname, IP address, UID, real hostname, account name, gecos
		self.sendLine(':'+str(config.sid)+' EUID '+cnick+' 0 '+str(time.time())+' +iSo '+cuser+' '+chost+' 0.0.0.0 '+cuid+' 0.0.0.0 0 :'+cgecos) 
		self.uidstore[cuid] = {'nick': cnick, 'user': cuser, 'host': chost, 'realhost': chost, 'account': "None", 'oper': True, 'modes': "+iSo", 'channels': [], 'gecos': cgecos}
		self.sendLine(':'+cuid+' JOIN '+str(time.time())+' '+config.reportchan+' +')
		self.sendLine("MODE "+config.reportchan+" +o "+cuid)
		return cuid
	def destroyClient(self,cuid,reason):
		self.sendLine(":"+cuid+" QUIT :"+reason)
	def sendPrivmsg(self,sender,target,message):
		self.sendLine(":"+sender+" PRIVMSG "+target+" :"+str(message))
	def sendNotice(self,sender,target,message):
		self.sendLine(":"+sender+" NOTICE "+target+" :"+str(message))
	def load(self,modname):
		self.modules[modname] = __import__(modname)
		return self.modules[modname]
	def modunload(self,modname):
		self.modules["module_"+modname].moddeinit(self)
		del self.modules["module_"+modname]
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
			gecos = ' '.join(split[12:]).strip(":")
			if split[10] == "*":
				realhost = split[7]
			else:
				realhost = split[10]
			ip = split[8]
			uid = split[9]
			account = split[11]
			if account == "*":
				account = "None"
			self.nickstore[nick] = {'uid': uid}
			if "o" in modes:
				self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': True, 'modes': modes, 'channels': [], 'gecos': gecos, 'ip': ip}
			else:
				self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': False, 'modes': modes, 'channels': [], 'gecos': gecos, 'ip': ip}
			for modname,module in self.modules.items():
				if hasattr(module, "onConnect"):
					module.onConnect(self,uid)
		elif split[1] == "SJOIN":
			chandata = re.match("^:[A-Z0-9]{3} SJOIN (\d+) (#[^ ]*) \+(.*) :(.*)$", data).groups()
			channel = chandata[1]
			uids = chandata[3]
			self.chanstore[channel] = {'ts': chandata[0], 'modes': chandata[2], 'uids': [], 'nicks': []}
			for uid in uids.strip("+").strip("@").split(" "):
				uidstrip = uid.replace("@","").replace("+","")
				if uidstrip == '':
					pass
				else:
					nick = self.uidstore[uidstrip]['nick']
					self.uidstore[uidstrip]['channels'].append(channel)
					self.chanstore[channel]['nicks'].append(nick)
					self.chanstore[channel]['uids'].append(uid)
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
		elif split[1] == "JOIN":
                 try:
			uid = split[0].replace(":","")
			channel = split[3]
			nick = self.uidstore[uid]['nick']
			self.uidstore[uid]['channels'].append(channel)
			self.chanstore[channel]['nicks'].append(nick)
			self.chanstore[channel]['uids'].append(uid)
			for modname,module in self.modules.items():
				if hasattr(module, "onJoin"):
					module.onJoin(self,uid,channel)
                 except: pass
		elif split[1] == "PART":
                 try:
			uid = split[0].replace(":","")
			channel = split[2]
			nick = self.uidstore[uid]['nick']
			self.uidstore[uid]['channels'].remove(channel)
			self.chanstore[channel]['nicks'].remove(nick)
			self.chanstore[channel]['uids'].remove(uid)
			for modname,module in self.modules.items():
				if hasattr(module, "onPart"):
					module.onPart(self,uid,channel)
                 except: pass
		elif split[1] == "CHGHOST":
			uid = split[2]
			oldhost = self.uidstore[uid]['host']
			newhost = split[3]
			self.uidstore[uid]['host'] = split[3]
			for modname,module in self.modules.items():
				if hasattr(module, "onChghost"):
					module.onChghost(self,uid,oldhost,newhost)
		elif split[1] == "NICK":
                 try:
			uid = split[0].replace(":","")
			oldnick = self.uidstore[uid]['nick']
			newnick = split[2]
			for channel in self.uidstore[uid]['channels']:
				self.chanstore[channel]['nicks'].remove(self.uidstore[uid]['nick'])
				self.chanstore[channel]['nicks'].append(newnick)
			self.uidstore[uid]['nick'] = newnick
			for modname,module in self.modules.items():
				if hasattr(module, "onNickChange"):
					module.onNickChange(self,uid,oldnick,newnick)
                 except: pass
		elif split[1] == "TMODE": #channel modes
			target = split[3]
			uid = split[0].strip(":")
			ts = split[2]
			modes = split[4]
			if split[5] == '': #Don't process the mode if it has args
				if "+" in modes:
					curmodes = self.chanstore[target]['modes']
					self.chanstore[target]['modes'] = curmodes+modes.strip("+")
				elif "-" in modes:
					removedmode = modes.strip("-")
					self.chanstore[target]['modes'] = self.chanstore[target]['modes'].strip(removedmode)
				
		elif split[1] == "QUIT":
			try:
				uid = split[0].replace(":","")
				for modname,module in self.modules.items():
					if hasattr(module, "onQuit"):
						module.onQuit(self,uid)
				for channel in self.uidstore[uid]['channels']:
					self.chanstore[channel]['nicks'].remove(self.uidstore[uid]['nick'])
					self.chanstore[channel]['uids'].remove(uid)
				del self.uidstore[uid]
			except:
				pass       
                elif split[1] == "KILL":
                 try:   
                        uid = split[2]
                        for channel in self.uidstore[uid]['channels']:
                                self.chanstore[channel]['nicks'].remove(self.uidstore[uid]['nick'])
                                self.chanstore[channel]['uids'].remove(uid)
                 except: pass
			
		#:SID EUID nickname, hopcount, nickTS, umodes, username, visible hostname, IP address, UID, real hostname, account name, gecos
		elif split[1] == "NOTICE":
			try:
				target = split[2]
				message = data.split("NOTICE "+target+" :")[1]
				uid = split[0].replace(":","")
				for modname,module in self.modules.items():
					if hasattr(module, "onNotice"):
						module.onNotice(self,uid,target,message)
			except Exception,e:
				print "Error: "+str(e)
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
			for modname,module in self.modules.items():
				if hasattr(module, "onPrivmsg"):
					module.onPrivmsg(self,target,uid,nick,host,realhost,account,message)
			#CTCP version replies
			if target[0] != "#":
				if message == "\x01VERSION\x01":
					self.sendLine(":"+target+" NOTICE "+uid+" :\x01VERSION "+self.altaraversion+"\x01")
			if splitm[0].lower() == "modload" and self.uidstore[uid]['oper'] == True:
				try:
					modtoload = splitm[1]
					self.sendLine("NOTICE "+config.reportchan+" :Loading "+str(modtoload)+" (requested by "+nick+"!"+user+"@"+host+")")
					module = self.load("module_"+modtoload)
					module.modinit(self)
				except Exception,e:
					self.sendLine("NOTICE "+config.reportchan+" :ERROR: "+(str(e)))
				#TODO: Reload/unload
			elif splitm[0].lower() == "modlist" and self.uidstore[uid]['oper'] == True:
				#modname = splitm[1]
				#del self.modules[modname]
				self.sendLine("NOTICE "+config.reportchan+" :Modules: "+str(self.modules.keys()))
			elif splitm[0].lower() == "modunload" and self.uidstore[uid]['oper'] == True:
				try:
					modname = splitm[1]
					self.modunload(modname)
				except Exception,e:
					self.sendLine("NOTICE "+config.reportchan+" :ERROR: "+(str(e)))
			elif splitm[0].lower() == "modfullreload" and self.uidstore[uid]['oper'] == True:
				try:
					modname = splitm[1]
					self.modules["module_"+modname].moddeinit(self)
					reload(self.modules["module_"+modname])
					self.modules["module_"+modname].modinit(self)
				except Exception,e:
					self.sendLine("NOTICE "+uid+" :ERROR Reloading: "+(str(e)+" (is the module loaded?)"))
			#Reload without using modinit/deinit
			elif splitm[0].lower() == "modreload" and self.uidstore[uid]['oper'] == True:
				try:
					modname = splitm[1]
					reload(self.modules["module_"+modname])
					self.sendLine("NOTICE "+config.reportchan+" :Reloaded "+modname+" (requested by "+nick+"!"+user+"@"+host+")")
				except Exception,e:
					self.sendLine("NOTICE "+uid+" :ERROR Reloading: "+(str(e)+" (is the module loaded?)"))
			elif splitm[0].lower() == "d-exec" and host == "FOSSnet/staff/bikcmp": #Do *NOT* enable this on a production network.  Used for debugging ONLY.  
				try:
					query = message.split('d-exec ')[1]
					ret=str(eval(query))
					if "#" in target:
						self.sendLine("NOTICE "+target+" :Debug: "+ret)
					else:
						self.sendLine("NOTICE "+uid+" :Debug: "+ret)
				except Exception,e:
					if "#" in target:
						self.sendLine("NOTICE "+target+" :Debug ERROR: "+str(e))
					else:
						self.sendLine("NOTICE "+uid+" :Debug ERROR: "+str(e))
			

if __name__ == '__main__':
	if config is None:
		print "Please edit config.py.dist.  After you're done, rename it to config.py and try launching Altara services again."
		exit()

	altara_socket((config.networkIP, config.linkport))
	asyncore.loop()
