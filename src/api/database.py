"""
database.py  —  SQLAlchemy database setup and Detection model.
"""
import os
import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Ensure the data directory exists before connecting
os.makedirs('data', exist_ok=True)

DATABASE_URL = 'sqlite:///data/detections.db'
Base         = declarative_base()
engine       = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine)


class Detection(Base):
    __tablename__ = 'detections'
    id             = Column(Integer, primary_key=True, autoincrement=True)
    url            = Column(String(2000), nullable=False)
    prediction     = Column(String(20),  nullable=False)   # 'PHISHING' | 'LEGITIMATE'
    confidence     = Column(Float,        nullable=False)
    risk_level     = Column(String(20),   nullable=False)
    raw_score      = Column(Float,        nullable=False)
    features_json  = Column(Text,         nullable=True)
    timestamp      = Column(DateTime,     default=lambda: datetime.datetime.now(datetime.timezone.utc))


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("Database initialised at data/detections.db")


def save_detection(result: dict):
    """Save one prediction result to the database."""
    db = SessionLocal()
    try:
        record = Detection(
            url           = result['url'],
            prediction    = result['prediction'],
            confidence    = result['confidence'],
            risk_level    = result['risk_level'],
            raw_score     = result['raw_score'],
            features_json = json.dumps(result.get('features', {})),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id
    except Exception as e:
        db.rollback()
        print(f"DB Error: {e}")
        return None
    finally:
        db.close()


def get_history(limit=50):
    """Return last N detection records."""
    db = SessionLocal()
    try:
        records = db.query(Detection).order_by(
            Detection.timestamp.desc()).limit(limit).all()
        return [
            {
                'id'        : r.id,
                'url'       : r.url,
                'prediction': r.prediction,
                'confidence': r.confidence,
                'risk_level': r.risk_level,
                'timestamp' : r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]
    finally:
        db.close()


def get_stats():
    """Return detection statistics."""
    db = SessionLocal()
    try:
        total    = db.query(Detection).count()
        phishing = db.query(Detection).filter(Detection.prediction=='PHISHING').count()
        legit    = total - phishing
        return {
            'total'          : total,
            'phishing_count' : phishing,
            'legitimate_count': legit,
            'phishing_pct'   : round(phishing/total*100, 1) if total else 0,
            'legitimate_pct' : round(legit/total*100, 1)    if total else 0,
        }
    finally:
        db.close()