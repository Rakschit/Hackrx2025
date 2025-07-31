from fastapi import FastAPI

app = FastAPI()

@app.post("/")
def read_root():
    return {"message": "Hello World"}