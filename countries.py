from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup1 import Base, Country, Destination, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Travel Destinations Application"

engine = create_engine('sqlite:///traveldestinations.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase+string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# gConnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    #validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameters'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #obtain authorization code
    code = request.data
    try:
        #upgrade auth code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # check that access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    #if there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    #verify that the access token is used for intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's id doesn't match"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    #verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID doesn't match"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # store the access token in the session for later use
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    #get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = json.loads(answer.text)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    #print "done!"
    return output

# user creation and information
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
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

# gDisconnect
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current User not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % 'access_token'
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.header['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Unable to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# show countries
@app.route('/')
@app.route('/country/')
def showCountries():
    countries = session.query(Country).order_by(Country.name)
    if 'username' not in login_session:
        return render_template('publiccountry.html', countries=countries)
    else:
        return render_template('country.html', countries=countries)

# add new countries
@app.route('/country/new', methods=['GET', 'POST'])
def newCountry():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCountry = Country(name=request.form['name'], user_id = login_session['user_id'])     
        session.add(newCountry)
        flash('New Country %s Successfully Created' % newCountry.name)
        session.commit()
        return redirect(url_for('showCountries'))
    else:
        return render_template('newcountry.html')

# edit countries
@app.route('/country/<int:country_id>/edit', methods=['GET', 'POST'])
def editCountry(country_id):
    editedCountry = session.query(Country).filter_by(id=country_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCountry.user_id != login_session['user_id']:
         return "<script>function myFunction() {alert('You are not authorized to edit this country. Please create your own country in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedCountry.name = request.form['name']
            flash('Country Successfully Edited %s' % editedCountry.name)
            return redirect(url_for('showCountries'))
    else:
        return render_template('editcountry.html', country=editedCountry)

# delete countries
@app.route('/country/<int:country_id>/delete', methods=['GET', 'POST'])
def deleteCountry(country_id):
    countryToDelete = session.query(Country).filter_by(id=country_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if countryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not the authorized to delete this country. Please create your own country in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(countryToDelete)
        flash('%s Successfully Deleted' % countryToDelete.name)
        session.commit()
        return redirect(url_for('showCountries', country_id=country_id))
    else:
        return render_template('deletecountry.html', country=countryToDelete)

# show destinations
@app.route('/country/<int:country_id>/')
@app.route('/country/<int:country_id>/destination')
def showDestination(country_id):
    country = session.query(Country).filter_by(id = country_id).one()
    creator = getUserInfo(country.user_id)
    destinations = session.query(Destination).filter_by(id=country_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicdestination.html', destinations=destinations, country=country, creator=creator)
    return render_template('destination.html', destinations=destinations, country=country, creator=creator)

# add new destination
@app.route('/country/<int:country_id>/destination/new', methods=['GET', 'POST'])
def newDestination(country_id):
    if 'username' not in login_session:
        return redirect('/login')
    country = session.query(Country).filter_by(id=country_id).one()
    if login_session['user_id'] != country.user_id:
        return "<script>funtion myFunction() {alert('You are not authorized to add destinations to this country. Please create your own country in order to add destinations.');}</script><body onload='myFunction()'"
    if request.method == 'POST':
        newDestination = Destination(name=request.form['name'], description=['description'], location=['location'], country_id=country_id)
        session.add(newDestination)
        session.commit()
        flash('New Destination %s Successfully Created' % (newDestination.name))
        return redirect(url_for('showDestination', country_id=country_id))
    else:
        return render_template('newdestination.html', country_iddd=country_id)

# edit destination
@app.route('/country/<int:country_id>/destination/<int:destination_id>/edit', methods=['GET', 'POST'])
def editDestination(country_id, destination_id):
    #if 'username' not in login_session:
    #    return redirect('/login')
    editedDestination = session.query(Destination).filter_by(id=destination_id).one()
    country = session.query(Country).filter_by(id=country_id).one()
    if login_session['user_id'] != country.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit destinations for this country. Please create your own country in order to edit destinations.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedDestination.name = request.form['name']
        if request.form['description']:
            editedDestination.description = request.form['description']
        if request.form['location']:
            editedDestination.location = request.form['location']
        session.add(editedDestination)
        session.commit()
        flash('Destination Successfully Edited')
        return redirect(url_for('showDestination'), country_id=country_id)
    else:
        return render_template('editdestination.html', country_id=country_id, destination_id=destination_id, destination=editedDestination)

# delete destination
@app.route('/country/<int:country_id>/destination/<int:destination_id>/delete', methods=['GET', 'POST'])
def deleteDestination(country_id, destination_id):
    if 'username' not in login_session:
        return redirect('/login')
    country = session.query(Country).filter_by(id=country_id).one()
    destinationToDelete = session.query(Country).filter_by(id=destination_id).one()
    if login_session['user_id'] != Country.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete destinations for this country. Please create your own country in order to delete destinations.');}</script><body onload='myFunction()'>" 
    if request.method == 'POST':
        session.delete(destinationToDelete)
        session.commit()
        flash('Destination Successfully Deleted')
        return redirect(url_for('showDestination', country_id=country_id))
    else:
        return render_template('deletedestination.html', destination=destinationToDelete)

# destination JSON
@app.route('/country/<int:country_id>/destination/JSON')
def countryDestinationJSON(country_id):
    country = session.query(Country).filter_by(id = country_id).one()
    destinations = session.query(Destination).filter_by(country_id=country_id).all()
    return jsonify(Destination=[d.serialize for d in destinations])

# destination list JSON
@app.route('/country/<int:country_id>/destination/<int:destination_id>/JSON')
def destinationListJSON(country_id, destination_id):
    destination_list = session.query(Destination).filter_by(id=destination_id).one()
    return jsonify(destination_list=destination_list.serialize)

# country JSON
@app.route('/country/JSON')
def destinationJSON():
    countries = session.query(Country).all()
    return jsonify(countries=[c.serialize for c in countries])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)