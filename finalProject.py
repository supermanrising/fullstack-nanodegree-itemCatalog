from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User
import random, string

# IMPORTS FOR OAUTH STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu App"

engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants')
def showRestaurants():
	restaurants = session.query(Restaurant).all()
	return render_template('restaurants.html', restaurants = restaurants)


@app.route('/restaurants/new', methods = ['GET', 'POST'])
def newRestaurant():
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newRestaurant = Restaurant(
			name = request.form['name'],
			user_id = login_session['user_id'])
		session.add(newRestaurant)
		session.commit()
		flash("New Restaurant Created")
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('new-restaurant.html')


@app.route('/restaurants/<int:restaurant_id>/edit', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'POST':
		if (request.form['name']):
			restaurant.name = request.form['name']
		session.add(restaurant)
		session.commit()
		flash("Restaurant Successfully Edited")
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('edit-restaurant.html', restaurant = restaurant)


@app.route('/restaurants/<int:restaurant_id>/delete', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'POST':
		session.delete(restaurant)
		session.commit()
		flash("Restaurant Successfully Deleted")
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('delete-restaurant.html', restaurant = restaurant)


@app.route('/restaurants/<int:restaurant_id>')
@app.route('/restaurants/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return render_template('menu.html', restaurant = restaurant, items = items)


@app.route('/restaurants/<int:restaurant_id>/menu/new', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'POST':
		newItem = MenuItem(
			name = request.form['name'],
			price = request.form['price'],
			description = request.form['description'],
			course = request.form['course'],
			restaurant_id = restaurant_id,
			user_id = restaurant.user_id)
		session.add(newItem)
		session.commit()
		flash("Menu Item Created")
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('new-menu-item.html', restaurant = restaurant)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	if 'username' not in login_session:
		return redirect('/login')
	item = session.query(MenuItem).filter_by(id = menu_id).one()
	if request.method == 'POST':
		if request.form['name']:
			item.name = request.form['name']
		if request.form['price']:
			item.price = request.form['price']
		if request.form['description']:
			item.description = request.form['description']
		else:
			item.description = ""
		if request.form['course']:
			item.course = request.form['course']
		else:
			item.course = ""
		session.add(item)
		session.commit()
		flash("Menu Item Successfully Edited")
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('edit-menu-item.html', item = item)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	if 'username' not in login_session:
		return redirect('/login')
	item = session.query(MenuItem).filter_by(id = menu_id).one()
	if request.method == 'POST':
		session.delete(item)
		session.commit()
		flash("Menu Item Deleted")
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('delete-menu-item.html', item = item)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Obtain authorization code
	# this was passed here as POST data by AJAX request in login.html
	# data: authResult.code
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
			% access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		print result.get('error')
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
	if 'credentials' not in login_session:
		print 'Access Token is None'
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = login_session['credentials']
	print 'In gdisconnect access token is %s', access_token
	print 'User name is: ' 
	print login_session['username']
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['credentials']
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	print 'result is '
	print result
	if result['status'] == '200':
		del login_session['credentials'] 
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response


# User Helper Functions
def createUser(login_session):
	newUser = User(
		name=login_session['username'],
		email=login_session['email'],
		picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id


def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user


def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None


# JSON APIs to view Restaurant Information
@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants=[i.serialize for i in restaurants])


@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=menuItem.serialize)


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)