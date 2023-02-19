from fastapi import FastAPI
import datetime
app = FastAPI()

@app.get("/")
def read_root():
    now = datetime.datetime.now()
    return {"Hello": "World at "+ now.strftime("%Y-%m-%d %H:%M:%S")}
