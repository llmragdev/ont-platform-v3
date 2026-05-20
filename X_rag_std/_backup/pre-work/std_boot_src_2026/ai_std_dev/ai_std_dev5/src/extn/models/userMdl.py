from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from extn.utility.databaseUtil import Base

class User(Base):
    __tablename__ = "temp_users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)  