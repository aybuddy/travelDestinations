                                                Introduction
_________________________________________________________________________________________________________________

Travel Destinations is a web app that allows users to enter in a country they would like to visit and the destinations they could visit.

A visitor to the app can view the countries listed displayed in the home screen. If a country is clicked, the destinations will show up that have been added by other users.

To add, edit or delete a country or destination, the user needs to be logged in using a google or facebook sign-in.

Once logged in, they are able to add a country and destination of their choice. Users may only edit and delete countries they have added.


                                         Installation Instruction
_________________________________________________________________________________________________________________
These libraries/dependencies are required for use of the application:

Flask version 0.12.2
SQLAlchemy version 1.1.14
Python version 2.7.12

Google and Facebook oauth logins are available for us to login and add countries and destinations with.

A vagrant machine is required to run the application as a localhost.


                                                How It Works
_________________________________________________________________________________________________________________
To use the application launch your vagrant machine from command line. Once your in you follow the next steps:

Run database_setup1.py to get the database set up.

Populate the database by running lotsofcountries.py and with starter countries and destinations.

Launch countries.py to use the application.

