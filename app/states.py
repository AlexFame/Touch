from aiogram.fsm.state import State, StatesGroup


class BookingState(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_contact = State()
    confirming = State()
    admin_reschedule_date = State()
    admin_reschedule_time = State()
