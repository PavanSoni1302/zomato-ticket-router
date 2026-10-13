from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./tickets.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    customer_email = Column(String, index=True)
    ticket_text = Column(String, unique=True)
    category = Column(String, index=True)
    priority = Column(Integer)  # 1: Low, 2: Medium, 3: High, 4: Critical
    sentiment = Column(String)
    tags = Column(String)
    suggested_reply = Column(String, nullable=True)

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    is_correct = Column(Boolean)
    comments = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)