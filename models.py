from sqlalchemy import Column, Integer, String
from database import Base

class Pokemon(Base):
    __tablename__ = "pokemons"

    id = Column(Integer, primary_key=True, index=True) 
    name = Column(String(100), unique=True, index=True)
    sprite = Column(String(255)) 
    type = Column(String(50))