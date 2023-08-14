from fastapi import FastAPI

from .routers import events

app = FastAPI()


app.include_router(
    events.router,
    prefix="/events",
)


@app.get("/")
async def root():
    return {"message": "Hey there! I am willow."}


# @app.post("/events")
# async def events(request: Request):
#     body = await request.json()
#     print("********************")
#     print(body)
#     print("********************")
#     challenge = body.get("challenge")
#     return {"challenge": challenge}
