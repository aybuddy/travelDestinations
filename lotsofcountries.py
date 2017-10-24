from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup1 import Country, Destination, Base

engine = create_engine('sqlite:///traveldestinations.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# destination for Iceland
country1 = Country(name="Iceland")

session.add(country1)
session.commit()

destination1 = Destination(name="Seljalandsfoss", description="65m high waterfall located in South Iceland",
                           location="thorsmerkurvegur", country=country1)

session.add(destination1)
session.commit()

# destination for Korea
country2 = Country(name="Korea")

session.add(country2)
session.commit()

destination1 = Destination(name="Gangnam", description="Neighborhood in Seoul with popular restaurants, bars, and night clubs",
                           location="Seoul", country=country2)

session.add(destination1)
session.commit()

# destination for Mexico
country3 = Country(name="Mexico")

session.add(country3)
session.commit()

destination1 = Destination(name="Tulum", description="Beach town packed with Mayan history, food, and culture",
                           location="Tulum", country=country3)

session.add(destination1)
session.commit()