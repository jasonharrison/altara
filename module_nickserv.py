def modinit(self):
	self.nickserv = self.createClient('NickServ','NickServ','services.','Altara Nickname Services')
def onPrivmsg(self,uid,target,message):
	msplit=message.split(" ")
	if msplit[0].lower() == "help":
		self.sendPrivmsg(self.nickserv,uid,"Helpa!")
def moddeinit(self):
	self.destroyClient(self.nickserv,"Shutting down")
