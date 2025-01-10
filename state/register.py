from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_delivery_datetime = State()
