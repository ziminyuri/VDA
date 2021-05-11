# Реализация классического метода ШНУР
import datetime

from django.db.models import Max

from model.models import Criterion, Model, Option
from services.normalisation import normalisation_time
from services.pairs_of_options import (_create_image_for_pair, _init_file,
                                       _read_file, _sort, _write_answer_model,
                                       _write_file, absolute_value_in_str,
                                       get_data_from_request,
                                       get_first_question, get_path, make_snd)
from snod.models import HistoryAnswerTrueSNOD, PairsOfOptionsTrueSNOD
from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from snod.tasks import get_graph_snod


def get_original_snod_question(model):
    """Получение вопроса"""

    pair = PairsOfOptionsTrueSNOD.objects.filter(id_model=model).filter(already_find_winner=False).first()
    # Пары для сравнения существуют
    if pair:

        pair = PairsOfOptionsTrueSNOD.objects.filter(id_model=model, already_find_winner=False, flag_not_compared=True).first()

        # Есть пара без найденого победителя, получаем вопрос
        if pair:
            return get_first_question(model, pair, original_snod=True)

    else:
        pair = PairsOfOptionsTrueSNOD.objects.filter(id_model=model)
        if not pair:
            pair = _create_pair(model, FIRST=True)
            Model.objects.filter(id=model.id).update(time_answer_snod=str(datetime.datetime.now()))
            _add_1_to_number_of_question(model)
            return get_first_question(model, pair, original_snod=True)
        else:
            quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_original_snod'))[
                'quasi_order_original_snod__max']
            options_with_quasi_max_order = Option.objects.filter(quasi_order_original_snod=quasi_max_order, id_model=model)
            options_with_quasi_0 = Option.objects.filter(quasi_order_original_snod=-1, id_model=model).first()

            if options_with_quasi_0:
                # Пока есть альтернативы с квазипорядком равным 0
                for option in options_with_quasi_max_order:
                    pair = _create_pair(model, option_1=option, option_2=options_with_quasi_0)

                _add_1_to_number_of_question(model)
                return get_first_question(model, pair, original_snod=True)

            else:
                # Нашли победителей
                update_model_after_find_winner(model)
                return {'flag_find_winner': 1}


def write_original_snod_answer(answer, auto=False, message=None, request=None):
    if auto is False:
        answer, option_1, option_2, option_1_line, option_2_line, model_id, question = get_data_from_request(request,
                                                                                                         answer)
    else:
        answer, option_1, option_2, option_1_line, option_2_line, model_id, question = get_data_from_meaage(answer, message)
    _write_answer_to_history_original_snod(question, answer, option_1, option_2, model_id)

    model = Model.objects.get(id=model_id)
    pair = PairsOfOptionsTrueSNOD.objects.filter(id_option_1=option_1).get(id_option_2=option_2)

    data, delimeter_line, n = _read_file(model, pair, original_snod=True)
    _write_answer_model(option_1_line, option_2_line, model_id, data, answer, snod_original=True)

    flag_new_pair = False
    name_1 = ''
    name_2 = ''

    path = get_path(model, pair, original_snod=True)
    Message = None
    if answer == 1:

        # Важнее преимущество по критерию а1

        # Строка состоит из одного критерия или из нескольких, если из одного то -1
        find_delimeter = option_1_line.find(';')
        if find_delimeter == -1:
            line = f'{option_1_line}|{option_2_line}|=1\n'
            _write_file(line, path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2 - 1]  # Строку которую мы добавляем
            list_2.append(str(new_line_2 - 1))
            option_2_line += f';{str(new_line_2 - 1)}'

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1]

            value_line_end = float(line_end[1])

            if float(line_begin[1]) <= 0 or (float(line_end[1])) >= 0:
                # Сошлись к центру  ---0---^
                _find_winner(model, pair)
                Message = get_original_snod_question(model)
                flag_new_pair = True

            elif value_line_end == 0.0:
                # Если значение с одного края стали равны нулю, а с другого не дошли до центра или до 0
                i = 1
                while (i != 0):
                    line_end = data[new_line_2 - i]
                    if float(line_end[1]) != 0.0:
                        line = f'{option_1_line}|{str(new_line_2 - i)}|=2\n'
                        _write_file(line, path)
                        i += 1

                    else:
                        break

                _find_winner(model, pair)
                Message = get_original_snod_question(model)
                flag_new_pair = True

            else:
                criteria_number = int(line_begin[0])
                criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_1 = criteria_1.name

                first_line = True

                for row in list_2:
                    # TODO ЗДЕСЬ ОШИБКА
                    if row == '-1':
                        _find_winner(model, pair)
                        Message = get_original_snod_question(model)
                        flag_new_pair = True
                    else:
                        try:
                            criteria_number = data[int(row[0])][0]
                            # criteria_number = int(data[row[0]][0])
                        except Exception as e:
                            pass
                        criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                        if first_line is True:
                            name_2 = criteria_2.name
                            first_line = False
                        else:
                            name_2 += f' и {criteria_2.name}'

        else:
            line = f'{option_1_line}|{option_2_line}|=0\n'
            _write_file(line, path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2 - 1]

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1]

            option_2_line = str(new_line_2 - 1)
            option_1_line = str(new_line_1)

            if line_begin[0] != line_end[0]:
                criteria_number = int(line_end[0])
                criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_2 = criteria_2.name

                criteria_number = int(line_begin[0])
                criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_1 = criteria_1.name

    elif answer == 0:

        line = f'{option_1_line}|{option_2_line}|=0\n'
        _write_file(line, path)

        list_2 = option_2_line.split(';')  # Разделили строку по разделителю
        new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
        line_end = data[new_line_2 - 1]

        list_1 = option_1_line.split(';')
        new_line_1 = int(list_1[-1])
        line_begin = data[new_line_1 + 1]

        option_2_line = str(new_line_2 - 1)
        option_1_line = str(new_line_1 + 1)

        if (float(line_end[1]) >= 0) or (float(line_begin[1]) <=0):
            # Сошлись к центру  ---0---^

            if (float(line_end[1]) < 0) or (float(line_begin[1]) <=0):
                _find_winner(model, pair, empty_option_1=True)
            elif (float(line_end[1]) >= 0) or (float(line_begin[1]) >0):
                _find_winner(model, pair, empty_option_2=True)
            else:
                _find_winner(model, pair)
            Message = get_original_snod_question(model)
            flag_new_pair = True

        # elif line_begin[0] != line_end[0] or new_line_1 + 1 != new_line_2:
        else:
            criteria_number = int(line_end[0])
            criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
            name_2 = criteria_2.name

            criteria_number = int(line_begin[0])
            criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
            name_1 = criteria_1.name

    else:

        # Строка состоит из одного критерия или из нескольких, если из одного то -1
        find_delimeter = option_2_line.find(';')

        if find_delimeter == -1:

            line = f'{option_1_line}|{option_2_line}|=2\n'
            _write_file(line, path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2]

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1 + 1]
            list_1.append(str(new_line_1 + 1))
            option_1_line += f';{str(new_line_1 + 1)}'

            value_line_begin = float(line_begin[1])

            if (float(line_begin[1]) > 0 and (float(line_end[1])) < 0) and new_line_1 != new_line_2:
                first_line = True
                for row in list_1:
                    criteria_number = data[int(row[0])][0]
                    criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                    if first_line is True:
                        name_1 = criteria_1.name
                        first_line = False
                    else:
                        name_1 += f' и {criteria_1.name}'

                criteria_number = int(line_end[0])
                criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_2 = criteria_2.name

            elif value_line_begin == 0.0:
                # Если значение с одного края стали равны нулю, а с другого не дошли до центра или до 0

                i = 1
                while (i != 0):
                    line_end = data[new_line_2 - i]
                    if float(line_end[1]) != 0.0:
                        line = f'{option_1_line}|{str(new_line_2 - i)}|=2\n'
                        _write_file(line, path)

                        i += 1

                    else:
                        break

                _find_winner(model, pair)
                Message = get_original_snod_question(model)
                flag_new_pair = True

            else:
                # Сошлись к центру  ---0---^
                _find_winner(model, pair)
                Message = get_original_snod_question(model)
                flag_new_pair = True

        else:
            line = f'{option_1_line}|{option_2_line}|=0\n'
            _write_file(line, path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2]

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1 + 1]

            option_2_line = str(new_line_2)
            option_1_line = str(new_line_1 + 1)

            if line_begin[0] != line_end[0]:
                criteria_number = int(line_end[0])
                criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_2 = criteria_2.name

                criteria_number = int(line_begin[0])
                criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_1 = criteria_1.name
    try:
        if Message['flag_find_winner'] == 1:
            quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_original_snod'))[
                'quasi_order_original_snod__max']
            Model.objects.filter(id=model_id).update(quasi_max_order_snod=quasi_max_order)
            get_graph_snod.delay(model_id)
            return Message
    except:
        pass

    if name_1 == '' or name_2 == '':
        _find_winner(model, pair)
        Message = get_original_snod_question(model)

    elif flag_new_pair is False:

        _add_1_to_number_of_question(model)
        question = f'Преимущество по критерию: "{name_1}" важнее чем преимущество по критерию: "{ name_2}" ?'
        Message = {'question': question, 'option_1': option_1, 'option_2': option_2,
                   'option_1_line': option_1_line, 'option_2_line': option_2_line, 'model': model.id,
                   'flag_find_winner': 0}

    elif Message is None:
        Message = get_original_snod_question(model)

    return Message


def _add_1_to_number_of_question(model):
    """ Добавление +1 к кол-ву вопросов """

    Model.objects.filter(id=model.id).update(number_of_questions_snod=model.number_of_questions_snod + 1)


def _write_answer_to_history_original_snod(question, answer, option_1, option_2, model_id):
    model = Model.objects.get(id=model_id)
    option_1 = Option.objects.get(id=option_1)
    option_2 = Option.objects.get(id=option_2)
    pair = PairsOfOptionsTrueSNOD.objects.get(id_option_1=option_1, id_option_2=option_2, id_model=model.id)
    if answer == 1:
        HistoryAnswerTrueSNOD.objects.create(question=question, answer='Важнее первое', pair=pair, id_model=model)
    elif answer == 2:
        HistoryAnswerTrueSNOD.objects.create(question=question, answer='Важнее второе', pair=pair, id_model=model)
    else:
        HistoryAnswerTrueSNOD.objects.create(question=question, answer='Одинаково важны', pair=pair, id_model=model)


def _find_winner(model: object, pair: object, empty_option_1 = False, empty_option_2 = False) -> None:
    path = f'{MEDIA_ROOT}/files/models/{str(model.id)}/original_snod/{str(pair.id)}.txt'
    with open(path) as f:
        lines = f.readlines()

    n = len(lines)

    flag_1 = False
    flag_2 = False

    first_line = False
    flag_1_compensable = False
    flag_2_compensable = False

    winner_1 = False
    winner_2 = False

    for i in range(n):
        if lines[i].find('|=') != -1:
            temp_result = int(lines[i].split('|=')[1].split('\n')[0])
            if temp_result == 1 and flag_1 is False:

                if not first_line:
                    flag_1_compensable = True
                    first_line = True

                flag_1 = True
                option_1_is_empty = False

            elif temp_result == 2 and flag_2 is False:

                if not first_line:
                    flag_2_compensable = True
                    first_line = True

                flag_2 = True
                option_2_is_empty = False

            elif temp_result == 0 and flag_1 is False and flag_2 is True:
                winner_2 = True
            elif temp_result == 0 and flag_2 is False and flag_1 is True:
                winner_1 = True

    if temp_result == 1:
        winner_1 = True
    if temp_result ==2:
        winner_2 = True

    if winner_1 and winner_2:
        result = 3

    elif flag_1_compensable and not flag_2 and flag_1:
        result = 1
    elif flag_2_compensable and not flag_1 and flag_2:
        result = 2

    elif not flag_1_compensable and not flag_2_compensable and empty_option_1  and not empty_option_2 :
        result = 1
    elif not flag_1_compensable and not flag_2_compensable and not empty_option_1  and empty_option_2:
        result = 2

    else:
        result = 0

    if pair.id_option_1.quasi_order_original_snod == -1 and pair.id_option_2.quasi_order_original_snod == -1:
        max_quasi_order_original_snod = 1
        lose = 0
    elif pair.id_option_1.quasi_order_original_snod > pair.id_option_2.quasi_order_original_snod:
        max_quasi_order_original_snod = pair.id_option_1.quasi_order_original_snod + 1
        lose = pair.id_option_1.quasi_order_original_snod
    else:
        max_quasi_order_original_snod = pair.id_option_2.quasi_order_original_snod + 1
        lose = pair.id_option_1.quasi_order_original_snod

    if result == 1:

        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_original_snod= max_quasi_order_original_snod)
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_original_snod=lose)
        PairsOfOptionsTrueSNOD.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                             flag_winner_option=1)
    elif result == 2:
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)
        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_original_snod=lose)
        PairsOfOptionsTrueSNOD.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                             flag_winner_option=2)
    else:
        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)

        if result == 0:
            PairsOfOptionsTrueSNOD.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                             flag_winner_option=0)
        else:
            PairsOfOptionsTrueSNOD.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=True,
                                                                     flag_winner_option=3)


def _create_pair(model, FIRST=False, option_1=None, option_2=None):
    if FIRST:
        options = Option.objects.filter(id_model=model)
        pair = PairsOfOptionsTrueSNOD.objects.create(id_option_1=options[0], id_option_2=options[1], id_model=model)


    else:
        pair = PairsOfOptionsTrueSNOD.objects.create(id_option_1=option_1, id_option_2=option_2, id_model=model)

    rows = make_snd(model, pair)
    rows = _sort(rows)  # Сортируем штобы привести к шкале и нормализуем под проценты
    _init_file(rows, pair, model, original_SNOD=True)
    _create_image_for_pair(rows, model, pair, original_shod=True)

    return pair


def update_model_after_find_winner(model):
    time_end = datetime.datetime.now()
    time_begin = model.time_answer_snod
    time_begin = datetime.datetime.strptime(time_begin, '%Y-%m-%d %H:%M:%S.%f')
    delta_time_many = time_end - time_begin
    delta_time_many = normalisation_time(delta_time_many)
    number_of_pairs = len(PairsOfOptionsTrueSNOD.objects.filter(id_model=model))
    number_of_incomparable = len(PairsOfOptionsTrueSNOD.objects.filter(id_model=model, flag_winner_option=3))

    Model.objects.filter(id=model.id).update(
        time_answer_snod=delta_time_many,
        already_find_winner_SNOD=True,
        number_of_pairs_snod=number_of_pairs,
        number_of_incomparable_snod=number_of_incomparable
    )


def _update_pair_to_not_comparable(pair):
    """ Делает пару не сравнимой """

    option_1 = Option.objects.filter(id=pair.id_option_1.id).first()
    option_2 = Option.objects.filter(id=pair.id_option_2.id).first()

    if option_1.quasi_order_pacom > option_2.quasi_order_pacom:
        max_quasi_order_original_snod = option_1.quasi_order_original_snod
    else:
        max_quasi_order_original_snod = option_2.quasi_order_original_snod

    Option.objects.filter(id=pair.id_option_1.id).update(
        quasi_order_original_snod=max_quasi_order_original_snod + 1)
    Option.objects.filter(id=pair.id_option_2.id).update(
        quasi_order_original_snod=max_quasi_order_original_snod + 1)

    PairsOfOptionsTrueSNOD.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=True,
                                                         flag_winner_option=3)


def get_winners_from_model_original_snod(model_id):
    model = Model.objects.get(id=model_id)
    options_with_quasi_max_order = Option.objects.filter(quasi_order_original_snod=model.quasi_max_order_snod,
                                                         id_model=model_id)
    return {'flag_find_winner': 1, 'winner_options': options_with_quasi_max_order}


def get_context_history_answer_original_snod(model) -> list:
    """ Возвращаем контекст истории ответов пользователей """

    pairs = PairsOfOptionsTrueSNOD.objects.select_related('id_option_1', 'id_option_2').filter(id_model=model)
    context = []

    for pair in pairs:

        item = {'pair': f'{pair.id_option_1.name} {pair.id_option_2.name}'}
        history_answers = HistoryAnswerTrueSNOD.objects.filter(id_model=model, pair=pair)

        answers = []
        for answer_history in history_answers:
            answers.append({'question': answer_history.question, 'answer': answer_history.answer})
        item['body'] = answers

        if pair.flag_winner_option == 3:
            item['winner'] = 'Альтернативы не сравнимы'
        elif pair.flag_winner_option == 2:
            item['winner'] = f'Победитель: {pair.id_option_2.name}'
        elif pair.flag_winner_option == 1:
            item['winner'] = f'Победитель: {pair.id_option_1.name}'
        elif pair.flag_winner_option == 0:
            item['winner'] = 'Альтернативы одинаковы'

        item['img'] = f'http://127.0.0.1:8000/media/{str(model)}/{str(pair.id)}.png'

        absolute_value = absolute_value_in_str(model, pair.id, original_snod=True)
        item['absolute_value'] = absolute_value
        context.append(item)

    return context


def get_data_from_meaage(answer, message):
    answer: int = int(answer)
    option_1: int = int(message["option_1"])
    option_2: int = int(message["option_2"])
    option_1_line: str = message["option_1_line"]
    option_2_line: str = message["option_2_line"]
    model_id: int = int(message["model"])
    question: str = message["question"]

    return answer, option_1, option_2, option_1_line, option_2_line, model_id, question
