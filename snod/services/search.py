import random

from services.history import checking_already_has_answer
from services.snod_original import write_original_snod_answer
from VDA.celery import app


@app.task(serializer='json')
def snod_search_auto(message):
    flag_find_winner = 0
    while flag_find_winner == 0:
        answer: int = random.randint(0, 2)
        message = write_original_snod_answer(answer, auto=True, message=message)
        flag_find_winner = message['flag_find_winner']
        if flag_find_winner != 1:

            message, flag_checking = checking_already_has_answer(message, snod_original=True)
            while flag_checking:
                flag_find_winner = message['flag_find_winner']
                if flag_find_winner != 1:
                    message, flag_checking = checking_already_has_answer(message, snod_original=True)
