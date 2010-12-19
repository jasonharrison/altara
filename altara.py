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
	
	def sendLine(self,data):
		print "Send "+str(data)
		self.push(data+'\r\n')
	def handle_connect(self):
		self.sendLine("PASS "+str(config.linkpass)+" TS 6 "+str(config.sid)+"\r\n")
		self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD\r\n")
		self.sendLine("SERVER "+str(config.servername)+" 1 :"+str(config.serverdescription)+"\r\n")
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

if __name__ == '__main__':
	if config is None:
		print "Please edit config.py.dist.  After you're done, rename it to config.py and try launching altara services again."
		exit()

	altara_socket((config.networkIP, config.linkport))
	asyncore.loop()
