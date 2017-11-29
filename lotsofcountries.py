from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup1 import Country, Destination, Base, User

engine = create_engine('sqlite:///traveldestinationswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#create dummy user
User1 = User(name="Carson Wentz", email="carson@wentz.com", picture="https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png")
session.add(User1)
session.commit()

# destination for Iceland
country1 = Country(user_id=1, name="Iceland", image="https://images.unsplash.com/photo-1439122590297-dde626bb7cf5?auto=format&fit=crop&w=1052&q=60&ixid=dW5zcGxhc2guY29tOzs7Ozs%3D")

session.add(country1)
session.commit()

destination1 = Destination(user_id=1, name="Seljalandsfoss", description="65m high waterfall located in South Iceland",
                           location="thorsmerkurvegur", image="https://images.unsplash.com/photo-1505939374277-8d746c530068?auto=format&fit=crop&w=1001&q=60&ixid=dW5zcGxhc2guY29tOzs7Ozs%3D", country=country1)

session.add(destination1)
session.commit()

# destination for Korea
country2 = Country(user_id=1, name="Korea", image="https://images.unsplash.com/photo-1504107435030-c7cd582601b8?auto=format&fit=crop&w=1189&q=60&ixid=dW5zcGxhc2guY29tOzs7Ozs%3D")

session.add(country2)
session.commit()

destination1 = Destination(user_id=1, name="Gangnam", description="Neighborhood in Seoul with popular restaurants, bars, and night clubs",
                           location="Seoul", image="https://images.unsplash.com/photo-1478071573747-403b24bf59a9?auto=format&fit=crop&w=1189&q=60&ixid=dW5zcGxhc2guY29tOzs7Ozs%3D", country=country2)

session.add(destination1)
session.commit()

# destination for Mexico
country3 = Country(user_id=1, name="Mexico", image="https://images.unsplash.com/photo-1452838269443-c86e6a3134f9?auto=format&fit=crop&w=800&q=60&ixid=dW5zcGxhc2guY29tOzs7Ozs%3D")

session.add(country3)
session.commit()

destination1 = Destination(user_id=1, name="Tulum", description="Beach town packed with Mayan history, food, and culture",
                           location="Tulum", image="https://images.unsplash.com/photo-1501855901885-8b29fa615daf?auto=format&fit=crop&w=968&q=60&ixid=dW5zcGxhc2guY29tOzs7Ozs%3D", country=country3)

session.add(destination1)
session.commit()