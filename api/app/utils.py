import datetime
from fastapi.exceptions import HTTPException


def get_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_last_entry_keys(number_of_entries: int):
    range_of_days = range(0, number_of_entries)
    return [
        (datetime.datetime.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range_of_days
    ]


async def _entry_already_exists(redis):
    return await redis.exists(datetime.datetime.utcnow().strftime("%Y-%m-%d"))


async def change_status_to_fast(state, redis):
    current_date = get_date()
    if await _entry_already_exists(redis):
        raise HTTPException(status_code=400, detail="Entry already exists for today")
    await redis.set(
        current_date,
        str(
            {
                "date": current_date,
                "start": state["last_toggle"].strftime("%H:%M:%S"),
                "end": datetime.datetime.now().strftime("%H:%M:%S"),
            }
        ),
    )
    state["state"] = "fast"
    state["last_toggle"] = datetime.datetime.now()
    return state


async def change_status_to_eat(state, redis):
    if await _entry_already_exists(redis):
        raise HTTPException(
            status_code=400, detail="You can switch to eat the next day again"
        )
    state["state"] = "eat"
    state["last_toggle"] = datetime.datetime.now()
    return state


async def create_new_state(redis, state=None):
    print(state)
    if state:
        state = {
            "state": state.state if state.state else "eat",
            "goal": (16, 8),
            "last_toggle": datetime.datetime.strptime(state.time, "%Y-%m-%d %H:%M")
            if state.time
            else datetime.datetime.now(),
        }
    else:
        state = {
            "state": "eat",
            "goal": (16, 8),
            "last_toggle": datetime.datetime.now(),
        }
    await redis.set("state", str(state))
    return state


async def get_state(redis):
    state = await redis.get("state")
    if state == None:
        raise HTTPException(
            status_code=400,
            detail="state object does not exist, please run GET /create_state first",
        )
    else:
        state = eval(state)
    return state
