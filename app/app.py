from fastapi import FastAPI

app = FastAPI()

@app.get("/hello_world")
def hello_world():
    return{"message": "Hello world"}
