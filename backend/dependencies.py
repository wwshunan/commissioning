from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Request, HTTPException, Security, Depends, Security
from .auth.auth import auth_handler
from .schemas import EnergyModel
from scipy.constants import c
from .database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def calc_energy(energy_model: EnergyModel):
    tof = energy_model.tof * 1e-9
    length = energy_model.distance
    v = length / tof
    beta = v / c
    if beta < 1:
        gamma = 1 / (1 - beta ** 2) ** 0.5
        energy = round((gamma - 1) * energy_model.mass, 3)
        return {
            'energy': energy
        }
    else:
        return {
            'warning': '超光速了'
        }


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = False):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            return auth_handler.decode_token(credentials.credentials)
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")




