import json
import enum
from sqlalchemy import (
    Column, BigInteger, String, Text, Enum as SQLAlchemyEnum, Float,
    TIMESTAMP, ForeignKey, UniqueConstraint, Integer, Date, JSON
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import UserDefinedType
from sqlalchemy.sql import func
from sqlalchemy import Index

# --- Custom VECTOR Type Definition for TiDB ---
class VECTOR(UserDefinedType):
    """A custom SQLAlchemy type to handle TiDB's VECTOR data type."""
    cache_ok = True
    def __init__(self, dimension=None):
        self.dimension = dimension
    def get_col_spec(self, **kw):
        return f"VECTOR({self.dimension})" if self.dimension else "VECTOR"
    def bind_processor(self, dialect):
        def process(value): return json.dumps(value) if value is not None else None
        return process
    def result_processor(self, dialect, coltype):
        def process(value): return json.loads(value) if value is not None else None
        return process

# --- Base Class for All Models ---
# This must be defined ONCE, before any models that use it.
Base = declarative_base()

# --- Enum Definitions ---
class SkillRelationshipType(enum.Enum):
    PREREQUISITE = "PREREQUISITE"; COMPLEMENTARY = "COMPLEMENTARY"; ALTERNATIVE = "ALTERNATIVE"
class ResourceType(enum.Enum):
    COURSE = "COURSE"; VIDEO = "VIDEO"; REPOSITORY = "REPOSITORY"; ARTICLE = "ARTICLE"; TUTORIAL = "TUTORIAL"
class SourcePlatform(enum.Enum):
    COURSERA = "COURSERA"; YOUTUBE = "YOUTUBE"; GITHUB = "GITHUB"; REDDIT = "REDDIT"; STACKOVERFLOW = "STACKOVERFLOW"
class MetricSource(enum.Enum):
    GITHUB = "GITHUB"; STACKOVERFLOW = "STACKOVERFLOW"; REDDIT_JOBS = "REDDIT_JOBS"
class AliasStatus(enum.Enum):
    PENDING = "PENDING"; APPROVED = "APPROVED"; REJECTED = "REJECTED"

# --- ORM Model Definitions ---

class Skill(Base):
    __tablename__ = 'skills'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100))
    description = Column(Text)
    skill_embedding = Column(VECTOR(1536))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class SkillRelationship(Base):
    __tablename__ = 'skill_relationships'
    id = Column(BigInteger, primary_key=True)
    source_skill_id = Column(BigInteger, ForeignKey('skills.id'), nullable=False)
    target_skill_id = Column(BigInteger, ForeignKey('skills.id'), nullable=False)
    relationship_type = Column(SQLAlchemyEnum(SkillRelationshipType), nullable=False)
    strength = Column(Float)
    inference_source = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    confidence_score = Column(Float, default=0.5) # For the Guardian module
    __table_args__ = (UniqueConstraint('source_skill_id', 'target_skill_id', 'relationship_type'),)

class LearningResource(Base):
    __tablename__ = 'learning_resources'
    id = Column(BigInteger, primary_key=True)
    title = Column(String(512), nullable=False)
    
    # --- THIS IS THE FINAL FIX ---
    # We remove both `unique=True` and the `__table_args__` Index.
    # We will rely ENTIRELY on your original, correct TiDB schema which uses a
    # GENERATED `url_hash` column with a UNIQUE constraint.
    # SQLAlchemy does not need to know about this database-level optimization.
    url = Column(String(1024), nullable=False)
    
    resource_type = Column(SQLAlchemyEnum(ResourceType), nullable=False)
    source_platform = Column(SQLAlchemyEnum(SourcePlatform), nullable=False)
    resource_embedding = Column(VECTOR(1536))
    quality_score = Column(Float)
    raw_metadata = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())


class SkillResourceMap(Base):
    __tablename__ = 'skill_resource_map'
    skill_id = Column(BigInteger, ForeignKey('skills.id'), primary_key=True)
    resource_id = Column(BigInteger, ForeignKey('learning_resources.id'), primary_key=True)
    relevance_score = Column(Float)

class TemporalSkillTrend(Base):
    __tablename__ = 'temporal_skill_trends'
    skill_id = Column(BigInteger, ForeignKey('skills.id'), primary_key=True)
    record_date = Column(Date, primary_key=True)
    metric_source = Column(SQLAlchemyEnum(MetricSource, name='metric_source_enum'), primary_key=True)
    value = Column(BigInteger, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(String(255), primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    user_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    current_skills = Column(JSON)
    learning_goals = Column(JSON)
    uploaded_resume_url = Column(String(1024))
    last_updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class CareerRoadmap(Base):
    __tablename__ = 'career_roadmaps'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    target_role = Column(String(255))
    generated_path = Column(JSON, nullable=False)
    estimated_duration_months = Column(Integer)
    confidence_score = Column(Float)
    created_at = Column(TIMESTAMP, server_default=func.now())

class TargetRole(Base):
    __tablename__ = 'target_roles'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

class RoleSkillRequirement(Base):
    __tablename__ = 'role_skill_requirements'
    role_id = Column(BigInteger, ForeignKey('target_roles.id'), primary_key=True)
    skill_id = Column(BigInteger, ForeignKey('skills.id'), primary_key=True)

class ResourceFeedback(Base):
    __tablename__ = 'resource_feedback'
    id = Column(BigInteger, primary_key=True)
    resource_id = Column(BigInteger, ForeignKey('learning_resources.id'))
    user_id = Column(String(255), ForeignKey('users.id'))
    rating = Column(Integer)

class SkillAlias(Base):
    __tablename__ = 'skill_aliases'
    alias = Column(String(255), primary_key=True)
    skill_id = Column(BigInteger, ForeignKey('skills.id'), nullable=False)
    source = Column(String(100))
    status = Column(SQLAlchemyEnum(AliasStatus, name='alias_status_enum'), default='PENDING')
    created_at = Column(TIMESTAMP, server_default=func.now())