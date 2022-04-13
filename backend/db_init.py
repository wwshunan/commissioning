from backend import models
from backend.database import engine

models.Base.metadata.create_all(bind=engine)
