from backend import models
from backend.database import engine, SessionLocal
from backend.dependencies import get_db
from backend.crud import insert_tasks

models.Base.metadata.create_all(bind=engine)
with SessionLocal() as session:
    insert_tasks(session)


