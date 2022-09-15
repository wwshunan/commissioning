from fastapi import FastAPI, Depends
from backend.lattice import router as lattice_router
from backend.phasescan import router as phase_scan_router
from backend.snapshot import router as snapshot_router
from backend.cavity_epk import router as epk_router
from backend.auth import router as auth_router
from backend.manual import router as manual_router
from backend.redis_config import register_redis
from backend.orbitcorrection import router as orbit_correction_router
from backend.hebt_match import router as hebt_match_router
from backend.sequencer import router as sequencer_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import fastapi_plugins
import typing
import aioredis
import pydantic
import uuid

job_id = str(uuid.uuid4()).replace('-', '')

app = FastAPI()
config = fastapi_plugins.get_config()
register_redis(app, config)
app.include_router(lattice_router.router)
app.include_router(phase_scan_router.router)
app.include_router(epk_router.router)
app.include_router(orbit_correction_router.router)
app.include_router(auth_router.router)
app.include_router(snapshot_router.router)
app.include_router(manual_router.router)
app.include_router(hebt_match_router.router)
app.include_router(sequencer_router.router)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root_get(
        cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis),
        conf: pydantic.BaseSettings = Depends(fastapi_plugins.depends_config)  # noqa E501
) -> typing.Dict:
    await cache.set(job_id, 'xxx')

    return dict(ping=await cache.ping(), api_name=conf.api_name)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=5000, debug=True)
