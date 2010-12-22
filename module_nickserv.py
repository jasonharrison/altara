import hashlib
import sqlite3 as sqlite

def modinit(self):
	self.nickserv = self.createClient('NickServ','NickServ','services.','Altara Nickname Services')
	self.connection = sqlite.connect("db/accounts.db")
	self.cursor = self.connection.cursor()
	self.cursor.execute("create table if not exists accounts (account,password,email,vhost)")
	self.connection.commit()
def onPrivmsg(self,uid,target,message):
	if target == self.nickserv:
		msplit=message.split(" ")
		if msplit[0].lower() == "register":
			try:
				account=self.uidstore[uid]['nick']
				password=msplit[1]
				email=msplit[2]
				if len(self.cursor.execute('select * from accounts where account=?',(account,)).fetchall())>0:
					self.sendNotice(self.nickserv,uid,"\x02"+account+"\x02 is already registered.")
				else:
					pwhash=str(hashlib.sha512(password).hexdigest())
					self.sendPrivmsg(self.nickserv,self.reportchan,"Register: \x02"+account+"\x02 to \x02"+email+"\x02")
					if "@" in email:
						self.cursor.execute('INSERT INTO accounts VALUES (?,?,?,?)',(account,pwhash,email,"None"))
						self.connection.commit()
					elif "@" not in email:
						self.sendNotice(self.nickserv,uid,"Please enter a valid email address.")
			except Exception,e:
				self.sendNotice(self.nickserv,"#services","Error: "+str(e))
				self.sendNotice(self.nickserv,uid,"Syntax: \x02register <password> <email>\x02 (Please do NOT include the <>'s)")
		elif msplit[0].lower() == "login" or msplit[0].lower() == "identify" or msplit[0].lower() == "id":
			try:
				account = self.uidstore[uid]['nick']
				password = msplit[1]
				pwhash = str(hashlib.sha512(password).hexdigest())
				self.cursor.execute("SELECT * from accounts where account=?",(account,))
				for row in self.cursor:
					print row[1]
					print pwhash
					if row[1] == pwhash:
						print "1"
					else:
						print "0"
				self.AccountLogin(uid,msplit[1])
				self.sendNotice(self.nickserv,uid,"You are now identified for \x02"+msplit[1]+"\x02")
			except Exception, e:
				self.sendNotice(self.nickserv,"#services","Error: "+str(e))
				self.sendNotice(self.nickserv,uid,"Syntax: \x02login <account name> <password>\x02 (Please do NOT include the <>'s)")
		elif msplit[0].lower() == "logout":
			self.connection.commit()
			self.AccountLogout(uid)
			self.sendNotice(self.nickserv,uid,"You are now logged out.")
		elif msplit[0].lower() == "help":
			self.sendNotice(self.nickserv,uid,"No help, yet.")
def moddeinit(self):
	self.connection.close()
	self.destroyClient(self.nickserv,"Shutting down")
