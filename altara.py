import asynchat,asyncore,socket,time

class asynchat_bot(asynchat.async_chat):
	def __init__(self, host, port):
		asynchat.async_chat.__init__(self)
		self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
		self.set_terminator('\r\n')
		self.data=''
		self.remote=(host,port)
		self.connect(self.remote)
	
	def handle_connect(self):
		def srvsend(data):
			print "Send: "+data
			self.push(data+"\r\n")
		srvsend("PASS "+config.linkpass+" TS 6 "+config.sid)
		srvsend("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD")
		srvsend("SERVER "+config.servername+" 1 :"+config.serverdescription)
	
	def get_data(self):
		r=self.data
		self.data=''
		return r
	def collect_incoming_data(self, data):
		self.data+=data
	def found_terminator(self):
		def srvsend(data):
			print "Send: "+data
			self.push(data+"\r\n")
		data=self.get_data()
		split = str(data).split(" ")
		print "Recv: "+data
		if split[0] == "PING":
			srvsend("PONG "+split[1])
if __name__ == '__main__':
	try:
		import config
	except:
		print "Please edit config.py.dist.  After you're done, rename it to config.py and try launching altara services again."
		exit()
	asynchat_bot(config.networkIP,config.linkport)
	asyncore.loop()
