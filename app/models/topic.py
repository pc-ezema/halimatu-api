from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    order = Column(Integer, default=0)  # Order within the course
    
    # Course relationship
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    course = relationship("Course", back_populates="topics")
    
    # Classes relationship
    classes = relationship("Class", back_populates="topic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Topic {self.title}>"