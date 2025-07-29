from fastapi import FastAPI

app = FastAPI()

@app.post("/hackrx/hello")
async def run():
    return {"message": "hello"}