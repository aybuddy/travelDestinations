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
country1 = Country(user_id=1, name="Iceland")

session.add(country1)
session.commit()

destination1 = Destination(user_id=1, name="Seljalandsfoss", description="65m high waterfall located in South Iceland",
                           location="thorsmerkurvegur", country=country1)

session.add(destination1)
session.commit()

# destination for Korea
country2 = Country(user_id=1, name="Korea")

session.add(country2)
session.commit()

destination1 = Destination(user_id=1, name="Gangnam", description="Neighborhood in Seoul with popular restaurants, bars, and night clubs",
                           location="Seoul", country=country2)

session.add(destination1)
session.commit()

# destination for Mexico
country3 = Country(user_id=1, name="Mexico")

session.add(country3)
session.commit()

destination1 = Destination(user_id=1, name="Tulum", description="Beach town packed with Mayan history, food, and culture",
                           location="Tulum", country=country3)

session.add(destination1)
session.commit()