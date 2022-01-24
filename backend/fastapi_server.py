from typing import Optional, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/commissioning/phasescan/curve-fit")
def curve_fit(json_data: Dict):
    print(json_data)

@app.get("/")
def index():
    for i in range(10000000):
        i*1 + 100
        print(i)

@app.get("/test")
def test():
    return "OK"

if __name__ == '__main__':
    uvicorn.run(app)