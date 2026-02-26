import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DB_PATH

Base = declarative_base()


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    tags = Column(String(500), default="")
    images = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def get_images(self) -> list:
        return json.loads(self.images) if self.images else []

    def set_images(self, img_list: list):
        self.images = json.dumps(img_list, ensure_ascii=False)


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    return SessionLocal()
