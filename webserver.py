from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

#Import modules for CRUD operations
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///restaurantMenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

class webServerHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			if self.path.endswith("/restaurants"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body>"
				output += "<a href='/restaurants/new' style='font-size: 18px; margin-bottom: 20px;'>Create A New Restaurant</a>"

				restaurants = session.query(Restaurant).all()
				for restaurant in restaurants:
					output += "<h3 style='margin-bottom: 5px;'>" + restaurant.name + "</h3>"
					output += "<a href='#'>Edit</a>"
					output += "<br>"
					output += "<a href='#'>Delete</a>"

				output += "</body></html>"

				self.wfile.write(output)
				print output
				return

			if self.path.endswith("/restaurants/new"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body>"
				output += "<h1>Create A New Restaurant</h1>"

				output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/new'>"
				output += "<input name='new' type='text'>"
				output += "<input type='submit' value='Create'></form>"

				output += "</body></html>"

				self.wfile.write(output)
				print output
				return


		except IOError:
			self.send_error(404, "File not found %s" % self.path)


	def do_POST(self):
		try:
			if self.path.endswith("/restaurants/new"):
				ctype, pdict = cgi.parse_header(self.headers.getheader('Content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
					messagecontent = fields.get('new')

				newRestaurant = Restaurant(name = messagecontent[0])
				session.add(newRestaurant)
				session.commit()

				print "Added " + newRestaurant.name

				self.send_response(301)
				self.send_header('Content-type', 'text/html')
				self.send_header('Location', '/restaurants')
				self.end_headers()
				return

		except:
			pass


def main():
	try:
		port = 8080
		server = HTTPServer(('',port), webServerHandler)
		print "Server running on port %s" % port
		server.serve_forever()

	except KeyboardInterrupt:
		print "Stopping Web Server"
		server.socket.close()

if __name__ == '__main__':
	main()