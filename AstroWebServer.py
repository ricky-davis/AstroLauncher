import threading
import http.server
import socketserver

handler = http.server.SimpleHTTPRequestHandler
launcher = None

class AstroWebServer(threading.Thread):

	def run(self):
		with socketserver.TCPServer(("", 80), handler) as httpd:
			print("Server started at localhost:80")
			httpd.serve_forever()

def startWebServer(astroLauncher):
	try:
		launcher = astroLauncher
		server = AstroWebServer()
		server.start()
	except Exception as e:
		print("ERROR: %s" % e)
