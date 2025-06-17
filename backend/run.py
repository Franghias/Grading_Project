import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
    # uvicorn.run("app.main:app", host="10.80.88.255", port=8000, reload=True) 
    # uvicorn.run("app.main:app", host="192.168.1.167", port=8000, reload=True)