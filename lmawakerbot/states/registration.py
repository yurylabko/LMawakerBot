from aiogram.dispatcher.filters.state import StatesGroup, State


class StateReg(StatesGroup):
    start = State()
    name = State()
    alias = State()
    phone = State()
    messenger = State()
    done = State()
