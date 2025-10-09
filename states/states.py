from aiogram.fsm.state import State, StatesGroup


class NewSubjectState(StatesGroup):
    """State for adding a new quiz subject."""
    new_subject = State()

class DeleteSubjectState(StatesGroup):
    """State for deleting a quiz subject."""
    subject = State()

class QuizState(StatesGroup):
    """States for the quiz process."""
    right_answers = State()
    current_question = State()


class QuizSettingsState(StatesGroup):
    """States for quiz settings."""
    subject = State()
    level = State()


class Reg(StatesGroup):
    """States for user registration."""
    name = State()
    last_name = State()


class DeleteUserState(StatesGroup):
    user_id = State()