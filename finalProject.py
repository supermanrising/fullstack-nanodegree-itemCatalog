from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

#done :)
@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
	restaurants = session.query(Restaurant).all()
	return render_template('restaurants.html', restaurants = restaurants)


#done :)
@app.route('/restaurants/new/', methods = ['GET', 'POST'])
def newRestaurant():
	if request.method == 'POST':
		newRestaurant = Restaurant(name=request.form['name'])
		session.add(newRestaurant)
		session.commit()
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('new-restaurant.html')


#done :)
@app.route('/restaurants/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'POST':
		if (request.form['name']):
			restaurant.name = request.form['name']
		session.add(restaurant)
		session.commit()
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('edit-restaurant.html', restaurant = restaurant)


#done :)
@app.route('/restaurants/<int:restaurant_id>/delete/', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'POST':
		session.delete(restaurant)
		session.commit()
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('delete-restaurant.html', restaurant = restaurant)


#done :)
@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return render_template('menu.html', restaurant = restaurant, items = items)


#done :)
@app.route('/restaurants/<int:restaurant_id>/menu/new/', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if request.method == 'POST':
		newItem = MenuItem(
			name = request.form['name'],
			price = request.form['price'],
			description = request.form['description'],
			restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('new-menu-item.html', restaurant = restaurant)


#done :)
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
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
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('edit-menu-item.html', item = item)


#done :)
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	item = session.query(MenuItem).filter_by(id = menu_id).one()
	if request.method == 'POST':
		session.delete(item)
		session.commit()
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('delete-menu-item.html', item = item)


#JSON stuff
#done :)
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