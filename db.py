import os, logging
from sqlalchemy import Column, create_engine, Date, Float, Integer, Sequence, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base
# from sqlalchemy.ext.asyncio import create_async_engine

Base = declarative_base()

class WeightData(Base):
    __tablename__ = "WeightData"

    Id = Column(Integer, Sequence("WeightData_Id_seq"), primary_key=True, unique=True)
    Beach = Column(String)
    Lat = Column(Float)
    Longit = Column(Float)
    Weight = Column(Float)
    Dates = Column(Date)
    team = Column(String)
    person = Column(String)
    Teams = Column(ARRAY(String))

    def __repr__(self):
        return f"<WeightData(Dates={self.Dates}, Beach={self.Beach}, Weight={self.Weight}>"

class TeamMember(Base):
    __tablename__ = "Team_members"

    Id = Column(Integer, Sequence("TeamMember_Id_seq"), primary_key=True, unique=True)
    Name = Column(String)
    Team = Column(String)

    def __repr__(self):
        return f"<TeamMember(Name={self.Name}, Team={self.Team})>"

class Beach(Base):
    __tablename__ = "Beach2coord"

    Id = Column(Integer, Sequence("Beach2coord_Id_seq"), primary_key=True, unique=True)
    Beach = Column(String, unique=True)
    Lat = Column(Float)
    Lon = Column(Float)
    Country = Column(String)
    State = Column(String)

    def __repr__(self):
        return f"<Beach(Beach={self.Beach}, Lat={self.Lat} Lon={self.Lon}>"

def init_db(drop=False):
    db_url = os.getenv('DATABASE_URL')
    logger.debug(f'URL: {db_url}')
    if not db_url:
        raise Exception("Environment variable DATABASE_URL must be set")

    # DATABASE_URL uses postgres:// but SQLAlchemy only accepts postgresql://
    db_url = db_url.replace('postgres://', 'postgresql://')

    engine = create_engine(db_url)
    logger.info('Engine created')
    if (drop):
        logger.info('Base dropped')
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    return engine

logging.basicConfig(format='%(levelname)s:%(asctime)s__%(message)s', datefmt='%m/%d/%Y %I:%M:%S')
logger = logging.getLogger('sealice_logger')
logger.setLevel(logging.DEBUG)
