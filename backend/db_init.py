from backend_fastapi import models
from backend_fastapi.database import engine

models.Base.metadata.create_all(bind=engine)
