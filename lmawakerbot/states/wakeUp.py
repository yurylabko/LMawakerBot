from aiogram.dispatcher.filters.state import StatesGroup, State


class WakeUp(StatesGroup):
    start = State()
    end = State()
    cancel = State()
