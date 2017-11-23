from flask import Flask, render_template, request, redirect
from flask import url_for, flash, jsonify
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup1 import Base, Country, Destination, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open(
    'client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Travel Destinations Application"

engine = create_engine('sqlite:///traveldestinationswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# gConnect


# login decorator
def login_required(f):
    # @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(
            json.dumps('Invalid state parameters'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # obtain authorization code
    code = request.data
    try:
        # upgrade auth code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # check that access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # if there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(
            json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify that the access token is used for intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's id doesn't match"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID doesn't match"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # store the access token in the session for later use

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if users exists, it not create one
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
    output += ' " style = "width: 300px; height: 300px; \
                border-radius: 150px; \
                -webkit-border-radius: 150px; \
                -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    # print "done!"
    return output

# user creation and information


def createUser(login_session):
    newUser = User(name=login_session['username'],
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

# gDisconnect


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    # print "~~~** login_session", login_session
    if access_token is None:
        # print "Access token is none"
        response = make_response(
            json.dumps('Current User not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # print "~~~** access token", access_token
    # print 'User name is: '
    # print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # print 'result is '
    # print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Unable to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# facebook login


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(
            json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token \
    ?grant_type=fb_exchange_token&client_id=%s \
    &client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.10/me"
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.10/me?access_token \
    =%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.10/me/picture?access_token \
    =%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px; height: 300px; \
                border-radius: 150px; \
                -webkit-border-radius: 150px; \
                -moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

# facebook disconnect


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
    % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# show countries


@app.route('/')
@app.route('/country/')
def showCountries():
    countries = session.query(Country).order_by(Country.name)
    # print "~~***country", countries
    if 'username' not in login_session:
        return render_template('publiccountry.html',
                               countries=countries)
    else:
        return render_template('country.html',
                               countries=countries)

# add new countries


@login_required
@app.route('/country/new', methods=['GET', 'POST'])
def newCountry():
    if request.method == 'POST':
        newCountry = Country(name=request.form['name'],
                             image=request.form['image'],
                             user_id=login_session['user_id'])
        session.add(newCountry)
        flash('New Country %s Successfully Created' % newCountry.name)
        session.commit()
        return redirect(url_for('showCountries'))
    else:
        return render_template('newcountry.html')

# edit countries


@login_required
@app.route('/country/<int:country_id>/edit', methods=['GET', 'POST'])
def editCountry(country_id):
    editedCountry = session.query(Country).filter_by(id=country_id).one()
    if editedCountry.user_id != login_session['user_id']:
        return "<script>function myFunction() \
                {alert('You are not authorized to edit this country. \
                Please add your own country in order to edit.');} \
                </script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedCountry.name = request.form['name']
        flash('Country Successfully Edited %s' % editedCountry.name)
        return redirect(url_for('showCountries'))
    else:
        return render_template('editcountry.html',
                               country=editedCountry)

# delete countries


@login_required
@app.route('/country/<int:country_id>/delete', methods=['GET', 'POST'])
def deleteCountry(country_id):
    countryToDelete = session.query(Country).filter_by(id=country_id).one()
    if countryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are \
                not the authorized to delete this country. \
                Please add your own country in order to delete.');} \
                </script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(countryToDelete)
        flash('%s Successfully Deleted' % countryToDelete.name)
        session.commit()
        return redirect(url_for('showCountries',
                                country_id=country_id))
    else:
        return render_template('deletecountry.html',
                               country=countryToDelete)

# show destinations


@app.route('/country/<int:country_id>/')
@app.route('/country/<int:country_id>/destination')
@app.route('/country/<int:country_id>/destination/')
def showDestination(country_id):
    country = session.query(Country).filter_by(id=country_id).one()
    creator = getUserInfo(country.user_id)
    destinations = session.query(Destination).filter_by(
        country_id=country_id).all()
    if 'username' not in login_session or creator.id \
    != login_session['user_id']:
        return render_template('publicdestination.html',
                               destinations=destinations,
                               country=country,
                               creator=creator)
    else:
        return render_template('destination.html',
                               destinations=destinations,
                               country=country)

# add new destination


@login_required
@app.route('/country/<int:country_id>/destination/new',
           methods=['GET', 'POST'])
def newDestination(country_id):

    country = session.query(Country).filter_by(id=country_id).one()
    if login_session['user_id'] != country.user_id:
        return "<script>funtion myFunction(){alert('You are \
                not authorized to add a destination to this country. \
                Please create your own country to add a destination.');} \
                </script><body onload='myFunction()'"
    if request.method == 'POST':
        newDestination = Destination(name=request.form['name'],
                                     location=request.form['location'],
                                     description=request.form['description'],
                                     image=request.form['image'],
                                     country_id=country_id,
                                     user_id=country.user_id)
        session.add(newDestination)
        session.commit()
        flash('New Destination %s Successfully Created'
              % (newDestination.name))
        return redirect(url_for('showDestination',
                                country_id=country_id))
    else:
        return render_template('newdestination.html',
                               country_id=country_id)

# edit destination


@login_required
@app.route('/country/<int:country_id>/destination/<int:destination_id>/edit',
           methods=['GET', 'POST'])
def editDestination(country_id, destination_id):
    editedDestination = session.query(Destination).filter_by(
        id=destination_id).one()
    country = session.query(Country).filter_by(id=country_id).one()
    if login_session['user_id'] != country.user_id:
        return "<script>function myFunction(){alert('You are \
            not authorized to edit destinations for this country. \
            Please create your own country to edit destinations.');} \
            </script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedDestination.name = request.form['name']
        if request.form['location']:
            editedDestination.location = request.form['location']
        if request.form['description']:
            editedDestination.description = request.form['description']
        session.add(editedDestination)
        session.commit()
        flash('Destination Successfully Edited')
        return redirect(url_for('showDestination',
                                country_id=country_id))
    else:
        return render_template('editdestination.html',
                               country_id=country_id,
                               destination_id=destination_id,
                               destination=editedDestination)

# delete destination


@login_required
@app.route('/country/<int:country_id>/destination/<int:destination_id>/delete',
           methods=['GET', 'POST'])
def deleteDestination(country_id, destination_id):
    country = session.query(Country).filter_by(id=country_id).one()
    # print "~~~**country: ", country
    destinationToDelete = session.query(Destination).filter_by(
        id=destination_id).one_or_none()
    # print "~~~**destination: ", destinationToDelete
    if login_session['user_id'] != country.user_id:
        return "<script>function myFunction(){alert('You are \
                not authorized to delete destination for this country. \
                Please create your own country to delete destination.');} \
                </script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(destinationToDelete)
        session.commit()
        flash('Destination Successfully Deleted')
        return redirect(url_for('showDestination', country_id=country_id))
    else:
        return render_template('deletedestination.html',
                               destinationss=destinationToDelete,
                               country_id=country_id,
                               destination_id=destination_id)

# disconnect


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            # gdisconnect()
            del login_session['access_token']
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        del login_session['picture']
        del login_session['provider']
        flash("You have been sucessfully logged out")
        return redirect(url_for('showCountries'))
    else:
        flash("You were not logged in")
        redirect(url_for('showCountries'))

# destination JSON


@app.route('/country/<int:country_id>/destination/JSON')
def countryDestinationJSON(country_id):
    country = session.query(Country).filter_by(id=country_id).one()
    destinations = session.query(Destination).filter_by(
        country_id=country_id).all()
    return jsonify(Destination=[d.serialize for d in destinations])

# destination list JSON


@app.route('/country/<int:country_id>/destination/<int:destination_id>/JSON')
def destinationListJSON(country_id, destination_id):
    destination_list = session.query(Destination).filter_by(
        id=destination_id).one()
    return jsonify(destination_list=destination_list.serialize)

# country JSON


@app.route('/country/JSON')
def destinationJSON():
    countries = session.query(Country).all()
    return jsonify(countries=[c.serialize for c in countries])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
