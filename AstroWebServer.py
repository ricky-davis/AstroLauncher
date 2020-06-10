import threading
import http.server
import socketserver
import sys
import os

queue = None


class ServerHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

	def do_GET(self):
		if self.path == '/':
			# home page

			htmlFile = open(os.path.join(sys._MEIPASS, 'index.html'), 'r')
			html = htmlFile.read()

			self.send_response(200)

			self.send_header("Content-type", "text/html")
			self.end_headers()

			self.wfile.write(bytes(html, "utf8"))

			htmlFile.close()

		elif self.path == '/api':
			# api
			global queue

			launcher = queue.get()
			queue.put(launcher)
			print("test val: %s" % launcher.testValue)
			launcher.logPrint("test test")

			self.send_response(200)

			self.send_header("Content-type", "text/json")
			self.end_headers()

			self.wfile.write(bytes("{data: 'test'}", "utf8"))

		else:
			# 404
			self.send_response(404)

			self.send_header("Content-type", "text/html")
			self.end_headers()

			self.wfile.write(bytes("<html><head><title>Not Found</title></head><body>Not Found</body></html>", "utf8"))

		return
		#http.server.SimpleHTTPRequestHandler.do_GET(self)

	def log_message(self, format, *args):
		return
		


#handler = http.server.SimpleHTTPRequestHandler
handler = ServerHttpRequestHandler

class AstroWebServer(threading.Thread):
	def __init__(self, queue):
		threading.Thread.__init__(self)
		self.queue = queue

	def run(self):
		# assign queue inside the thread
		global queue
		queue = self.queue

		with socketserver.TCPServer(("", 80), handler) as httpd:
			httpd.serve_forever()

def startWebServer(exchangeQueue):
	try:
		server = AstroWebServer(exchangeQueue)
		server.start()
	except Exception as e:
		print("ERROR: %s" % e)
