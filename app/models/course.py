from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import enum

# Association table for many-to-many relationship between courses and plans
course_plan = Table(
    'course_plan',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id', ondelete='CASCADE'), primary_key=True),
    Column('plan_id', Integer, ForeignKey('plans.id', ondelete='CASCADE'), primary_key=True)
)

class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, default=0)  # 0 for free
    status = Column(Enum(CourseStatus), default=CourseStatus.DRAFT)
    image = Column(String(500), nullable=True)
    instructor = Column(String(100), nullable=True)
    duration_months = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topics = relationship("Topic", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="course", cascade="all, delete-orphan")

    # Many-to-many relationship with plans
    plans = relationship("Plan", secondary=course_plan, back_populates="courses")

    def __repr__(self):
        return f"<Course {self.title}>"