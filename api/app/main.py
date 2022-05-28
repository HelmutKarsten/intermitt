from typing import Union, Optional

from fastapi import FastAPI

import aioredis
from .utils import (
    change_status_to_eat,
    change_status_to_fast,
    get_state,
    get_date,
    get_last_entry_keys,
    create_new_state,
)

from pydantic import BaseModel


class WeightEntry(BaseModel):
    weight: float


class State(BaseModel):
    time: Optional[str]
    state: Optional[str]


app = FastAPI()


redis = aioredis.from_url(
    "redis://localhost", password="top-secret", decode_responses=True
)

# Fasting
@app.get("/")
async def read_root():
    range_of_days = get_last_entry_keys(7)
    result = await redis.mget(range_of_days)
    print("---------- result -----------")
    print(result)
    return {"data": [eval(entry) for entry in result if entry]}


@app.post("/break")
async def break_fast():
    state = await get_state(redis)
    state = change_status_to_eat(state, redis)
    await redis.set("state", str(state))
    return state


@app.post("/begin")
async def begin_fast():
    state = await get_state(redis)
    state = change_status_to_fast(state, redis)
    await redis.set("state", str(state))
    return state


@app.post("/toggle")
async def toggle_fast():
    state = await get_state(redis)
    if state["state"] == "eat":
        state = await change_status_to_fast(state, redis)
    else:
        state = await change_status_to_eat(state, redis)
    await redis.set("state", str(state))
    return state


# State
@app.get("/state")
async def read_state():
    result = await get_state(redis)
    print("---------- result -----------")
    print(result)
    return {"data": result if result else None}


# Weight
@app.post("/weight")
async def add_weigth(entry: WeightEntry):
    weigh_in_date = get_date()
    await redis.set(
        f"w_{weigh_in_date}", str({"date": weigh_in_date, "weight": entry.weight})
    )
    return "Weight {} for today set".format(entry.weight)


@app.get("/weight")
async def read_weights():
    keys = await redis.keys(pattern=r"w_*")
    result = await redis.mget(keys)
    print("---------- result -----------")
    print(result)
    return {"data": [eval(entry) for entry in result]}


# Debugging
@app.delete("/state")
async def delete_state():
    await redis.delete("state")
    await redis.delete("2022-05-28")
    await redis.delete("2022-05-27")
    await redis.delete("w_2022-05-27")
    return "deleted"


@app.post("/create_state")
async def create_state(state: Optional[State]):
    result = await create_new_state(redis, state)
    return {"data": result, "msg": "New state created."}


@app.post("/set_log")
async def set_log():
    result = await redis.set(
        "2022-05-28",
        str({"date": "2022-05-28", "start": "11:52:00", "end": "17:21:45"}),
    )
    return {"data": result, "msg": "New state created."}
