def modinit(self):
	self.pieserv = self.createClient("PieServ","PieServ","services.","PieServ!")
def moddeinit(self):
	self.destroyClient(self.pieserv,"Shutting down")
#def onPrivmsg(self,uid,nick,host,realhost,account,message):
def onPrivmsg(self,uid,target,message):
	if target == self.pieserv:
		if message.lower() == "pie":
			self.sendNotice(self.pieserv,uid,"Pie? Where!")
		else:
			self.sendNotice(self.pieserv,uid,"This is an example module for altara showing how to create a simple module.  This serves no purpose at all.  Commands: pie")
	
	#self.sendPrivmsg(self.pieserv,"#altara","Pie!")
	
