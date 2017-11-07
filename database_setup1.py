import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(32), nullable=False)
    picture = Column(String(250))
    #password_hash = Column(String(32))

class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    image = Column(String(250))

    @property
    def serialize(self):
        return {
        'name'  : self.name,
        'id'    : self.id,
    }

class Destination(Base):
    __tablename__ = 'destination'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    location = Column(String(250))
    description = Column(String(250)) 
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship(Country)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    image = Column(String(250))

    @property
    def serialize(self):
        return {
        'name'  : self.name,
        'location'  : self.location,
        'description'   : self.description,
    }


engine = create_engine('sqlite:///traveldestinationswithusers.db')
Base.metadata.create_all(engine)