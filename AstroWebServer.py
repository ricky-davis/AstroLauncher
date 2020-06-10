import threading
import http.server
import socketserver

handler = http.server.SimpleHTTPRequestHandler

class AstroWebServer(threading.Thread):

	def run(self, launcher):
		with socketserver.TCPServer(("", 80), handler) as httpd:
			#print("Server started at localhost:80")
			httpd.serve_forever()

def startWebServer(launcher):
	try:
		#print("starting http thread")
		server = AstroWebServer()
		server.start(launcher)
	except Exception as e:
		print("error: %s" % e)
