# Реализация классического метода ШНУР
import datetime

from django.db.models import Max

from model.models import Criterion, Model, Option
from services.normalisation import normalisation_time
from services.pairs_of_options import (_create_image_for_pair, _init_file,
                                       _read_file, _sort, _write_answer_model,
                                       _write_file, absolute_value_in_str,
                                       get_data_from_request, get_path, make_snd)
from snod.models import HistoryAnswerTrueSNOD, PairsOfOptionsTrueSNOD
from VDA.settings import MEDIA_ROOT, DEPLOY, MEDIA_URL
from snod.tasks import get_graph_snod


def get_original_snod_question(model):
    """Получение вопроса"""
    pair = PairsOfOptionsTrueSNOD.objects.filter(id_model=model).filter(already_find_winner=False).first()

    if pair:
        """ Пары для сравнения существуют """
        pair = PairsOfOptionsTrueSNOD.objects.filter(id_model=model, already_find_winner=False,
                                                     flag_not_compared=True).first()

        if pair:
            """ Есть пара без найденого победителя, получаем вопрос """
            return get_first_question_snod(model, pair, original_snod=True)

    else:
        """ Пары для сравнения не существуют """
        pair = PairsOfOptionsTrueSNOD.objects.filter(id_model=model)

        if not pair:
            """ Получаем самую первую пару для сравнения"""
            pair = _create_pair(model, 0, FIRST=True)
            Model.objects.filter(id=model.id).update(time_answer_snod=str(datetime.datetime.now()))
            _add_1_to_number_of_question(model)
            return get_first_question_snod(model, pair, original_snod=True)

        """ Первая пара уже создана. Работаем с квазипорядками"""
        quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_original_snod'))[
            'quasi_order_original_snod__max']
        options_with_quasi_max_order = Option.objects.filter(quasi_order_original_snod=quasi_max_order, id_model=model)
        options_with_quasi_first = Option.objects.filter(quasi_order_original_snod=-1, id_model=model).first()

        if options_with_quasi_first:
            """ Есть альтернативы с квазипорядком равным -1 (Начальный квазипорядок)"""
            for option in options_with_quasi_max_order:
                """ Создаем пары с максимальным квазипорядоком и минимальным квазипорядком (-1) """
                pair = _create_pair(model, quasi_max_order, option_1=option, option_2=options_with_quasi_first)

            _add_1_to_number_of_question(model)
            return get_first_question_snod(model, pair, original_snod=True)

        else:
            """Нашли победителей"""
            update_model_after_find_winner(model)
            return {'flag_find_winner': 1}


def write_original_snod_answer(answer, auto=False, message=None, request=None):
    if auto is False:
        answer, option_1, option_2, option_1_line, option_2_line, model_id, question = get_data_from_request(request,
                                                                                                             answer)
    else:
        answer, option_1, option_2, option_1_line, option_2_line, model_id, question = get_data_from_meaage(answer,
                                                                                                            message)
    _write_answer_to_history_original_snod(question, answer, option_1, option_2, model_id)
    model = Model.objects.get(id=model_id)
    pair = PairsOfOptionsTrueSNOD.objects.filter(id_option_1=option_1, id_option_2=option_2).first()

    data, delimeter_line, n = _read_file(model, pair, original_snod=True)
    _write_answer_model(option_1_line, option_2_line, model_id, data, answer, snod_original=True)

    path = get_path(model, pair, original_snod=True)
    name_1, name_2 = '', ''
    flag_new_pair = False

    if answer == 1:
        """Важнее преимущество по критерию а1"""

        find_delimeter = option_1_line.find(';')
        if find_delimeter == -1:
            """Строка состоит из одного критерия"""
            _write_file(f'{option_1_line}|{option_2_line}|=1\n', path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2 - 1]  # Строку которую мы добавляем
            list_2.append(str(new_line_2 - 1))
            option_2_line += f';{str(new_line_2 - 1)}'

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1]

            if float(line_begin[1]) <= 0 or (float(line_end[1])) >= 0:
                """Сошлись к центру  ---0---^"""
                flag_new_pair, message, name_1, name_2, trash_1, trash_2 = converged_to_the_center(model, pair, line_begin, line_end)

            else:
                """К центру не сошлись, формируем name_1 и name_2 для вопроса"""
                flag_new_pair = False
                criteria_number = int(line_begin[0])
                criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_1 = f'"{criteria_1.name}"'

                first_line = True
                for row in list_2:
                    if row == '-1':
                        """ ? """
                        _find_winner(model, pair)
                        message = get_original_snod_question(model)
                        flag_new_pair = True
                    else:
                        criteria_number = data[int(row[0])][0]
                        criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                        if first_line is True:
                            """Криткрий первый"""
                            name_2 = f'"{criteria_2.name}"'
                            first_line = False
                        else:
                            name_2 = f'{name_2} и "{criteria_2.name}"'

        else:
            """Строка победитель не состоит из 1 критерия"""
            _write_file(f'{option_1_line}|{option_2_line}|=0\n', path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2 - 1]

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1]

            option_2_line = str(new_line_2 - 1)
            option_1_line = str(new_line_1)

            if (float(line_end[1]) < 0) and (float(line_begin[1]) > 0):
                name_1, name_2 = _get_name_1_and_name_2(model, line_end, line_begin)

    elif answer == 0:
        """Равноценны"""
        flag_new_pair, message, name_1, name_2, option_1_line, option_2_line = _take_one_criterion_for_each_alternative(option_1_line, option_2_line,
                                                                                          path, data, model, pair)

    else:
        """Важнее преимущество по критерию а2"""

        find_delimeter = option_2_line.find(';')
        if find_delimeter == -1:
            """Строка состоит из одного критерия альтернативы А2"""
            _write_file(f'{option_1_line}|{option_2_line}|=2\n', path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2]

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1 + 1]
            list_1.append(str(new_line_1 + 1))
            option_1_line += f';{str(new_line_1 + 1)}'

            if float(line_begin[1]) <= 0 or (float(line_end[1])) >= 0:
                """Сошлись к центру  ---0---^"""
                flag_new_pair, message, name_1, name_2, trash_1, trash_2 = converged_to_the_center(model, pair, line_begin, line_end)

            else:
                """К центру не сошлись, формируем name_1 и name_2 для вопроса"""
                flag_new_pair = False
                criteria_number = int(line_end[0])
                criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                name_2 = criteria_2.name

                first_line = True
                for row in list_1:
                    if row == '-1':
                        """ ? """
                        _find_winner(model, pair)
                        message = get_original_snod_question(model)
                        flag_new_pair = True
                    else:
                        criteria_number = data[int(row[0])][0]
                        criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
                        if first_line is True:
                            """Критерий первый"""
                            name_1 = f'"{criteria_1.name}"'
                            first_line = False
                        else:
                            name_1 = f'{name_1} и "{criteria_1.name}"'

        else:
            """Строка победитель не состоит из 1 критерия"""
            _write_file(f'{option_1_line}|{option_2_line}|=0\n', path)

            list_2 = option_2_line.split(';')  # Разделили строку по разделителю
            new_line_2 = int(list_2[-1])  # Взяли номер строки самой близкой к центру из списка который сравнивали ранее
            line_end = data[new_line_2]

            list_1 = option_1_line.split(';')
            new_line_1 = int(list_1[-1])
            line_begin = data[new_line_1 + 1]

            option_2_line = str(new_line_2)
            option_1_line = str(new_line_1 + 1)

            if (float(line_end[1]) < 0) and (float(line_begin[1]) > 0):
                name_1, name_2 = _get_name_1_and_name_2(model, line_end, line_begin)

    try:
        if message['flag_find_winner'] == 1:
            """ Был найден победитель"""

            quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_original_snod'))[
                'quasi_order_original_snod__max']
            Model.objects.filter(id=model_id).update(quasi_max_order_snod=quasi_max_order)
            fix_quasi_order_snod(model_id)
            get_graph_snod.delay(model_id)
            return message

    except: pass

    if name_1 == '' or name_2 == '':
        _find_winner(model, pair)
        message = get_original_snod_question(model)

    elif flag_new_pair is False:

        _add_1_to_number_of_question(model)
        question = f'Преимущество по критерию: {name_1} важнее чем преимущество по критерию: {name_2} ?'
        message = {'question': question, 'option_1': option_1, 'option_2': option_2,
                   'option_1_line': option_1_line, 'option_2_line': option_2_line, 'model': model.id,
                   'flag_find_winner': 0}

    elif message is None:
        message = get_original_snod_question(model)

    return message


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


def _update_quasi_order_snod_for_pair(pair, result):
    """ Обновляем квазипорядок для альтерантив в паре """

    max_quasi_order_original_snod = pair.quasi_level

    if pair.id_option_1.quasi_order_original_snod == -1 and pair.id_option_2.quasi_order_original_snod == -1:
        lose = 0
    elif pair.id_option_1.quasi_order_original_snod > pair.id_option_2.quasi_order_original_snod:
        lose = pair.id_option_1.quasi_order_original_snod
    else:
        lose = pair.id_option_1.quasi_order_original_snod

    if result == 1:

        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)
        option = Option.objects.get(id=pair.id_option_2.id)
        if option.quasi_order_original_snod <= lose:
            Option.objects.filter(id=pair.id_option_2.id).update(
                quasi_order_original_snod=lose)
        PairsOfOptionsTrueSNOD.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                                 flag_winner_option=1)
    elif result == 2:
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)

        option = Option.objects.get(id=pair.id_option_1.id)
        if option.quasi_order_original_snod <= lose:
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


def _find_winner(model: object, pair: object, empty_option_1=False, empty_option_2=False) -> None:
    pair = PairsOfOptionsTrueSNOD.objects.get(id=pair.id)
    if pair.flag_winner_option != -1:
        return

    path = f'{MEDIA_ROOT}/files/models/{str(model.id)}/original_snod/{str(pair.id)}.txt'
    with open(path) as f:
        lines = f.readlines()

    n = len(lines)

    flag_1 = False
    flag_2 = False
    flag_0 = False

    for i in range(n):
        if lines[i].find('|=') != -1:

            temp_result = int(lines[i].split('|=')[1].split('\n')[0])
            set_1 = lines[i].split('|')[0].split(';')
            set_2 = lines[i].split('|')[1].split(';')

            if len(set_1) == 1 and len(set_2) == 1:
                if temp_result == 1:
                    flag_1 = True
                elif temp_result == 2:
                    flag_2 = True
                else:
                    flag_0 = True

    if flag_1 and flag_2:
        result = 3
    elif flag_1 and not flag_2 and empty_option_1 and not empty_option_2:
        result = 3
    elif flag_1 and not flag_2:
        result = 1
    elif flag_2 and not flag_1 and empty_option_2 and not empty_option_1:
        result = 3
    elif flag_2 and not flag_1:
        result = 2
    elif flag_0 and empty_option_1 and not empty_option_2:
        result = 2
    elif flag_0 and empty_option_2 and not empty_option_1:
        result = 1
    elif not flag_1 and not flag_2 and not flag_0 and empty_option_1 and not empty_option_2:
        result = 2
    elif not flag_1 and not flag_2 and not flag_0 and empty_option_2 and not empty_option_1:
        result = 1
    else:
        result = 0

    _update_quasi_order_snod_for_pair(pair, result)
    return PairsOfOptionsTrueSNOD.objects.get(id=pair.id)


def _create_pair(model, quasi_max_order, FIRST=False, option_1=None, option_2=None):
    if FIRST:
        options = Option.objects.filter(id_model=model)
        pair = PairsOfOptionsTrueSNOD.objects.create(id_option_1=options[0], id_option_2=options[1], id_model=model,
                                                     quasi_level=1)

    else:
        pair = PairsOfOptionsTrueSNOD.objects.create(id_option_1=option_1, id_option_2=option_2, id_model=model,
                                                     quasi_level=quasi_max_order+1)

    rows = make_snd(model, pair)
    rows = _sort(rows)  # Сортируем штобы привести к шкале и нормализуем под проценты
    _init_file(rows, pair, model, original_SNOD=True)
    _create_image_for_pair(rows, model, pair, original_shod=True)

    return pair


def _find_incomparable_pairs_in_result(model_id):
    """Ищем из списка победителей, пары результат которых несравнимость"""

    quasi_max_order = Option.objects.filter(id_model=model_id).aggregate(Max('quasi_order_original_snod'))[
        'quasi_order_original_snod__max']
    options = Option.objects.filter(id_model=model_id, quasi_order_original_snod=quasi_max_order)

    option_len = len(options)
    if option_len > 1:
        m = 1
        for option_1 in range(option_len):
            for option_2 in range(m, option_len):
                pair = PairsOfOptionsTrueSNOD.objects.filter(id_option_1=options[option_1],
                                                             id_option_2=options[option_2]) | \
                       PairsOfOptionsTrueSNOD.objects.filter(id_option_2=options[option_1],
                                                             id_option_1=options[option_2])
                if pair:
                    p = pair.first()
                    PairsOfOptionsTrueSNOD.objects.filter(id=p.id).update(in_result_and_not_comparable=True)

            m += 1

    pairs = PairsOfOptionsTrueSNOD.objects.filter(id_model=model_id, in_result_and_not_comparable=True)

    if pairs:
        return True
    else:
        return False


def update_model_after_find_winner(model):
    time_end = datetime.datetime.now()
    try:
        time_begin = model.time_answer_snod
        time_begin = datetime.datetime.strptime(time_begin, '%Y-%m-%d %H:%M:%S.%f')
        delta_time_many = time_end - time_begin
        delta_time_many = normalisation_time(delta_time_many)
    except:
        delta_time_many = 'Прошлое 1 мин. 3 сек.'

    number_of_pairs = len(PairsOfOptionsTrueSNOD.objects.filter(id_model=model))
    number_of_incomparable = len(PairsOfOptionsTrueSNOD.objects.filter(id_model=model, flag_winner_option=3))
    has_incomparable_pairs_result_snod = _find_incomparable_pairs_in_result(model)

    Model.objects.filter(id=model.id).update(
        time_answer_snod=delta_time_many,
        already_find_winner_SNOD=True,
        number_of_pairs_snod=number_of_pairs,
        number_of_incomparable_snod=number_of_incomparable,
        has_incomparable_pairs_result_snod=has_incomparable_pairs_result_snod
    )


def _update_pair_to_not_comparable(pair):
    """ Делает пару не сравнимой """

    option_1 = Option.objects.filter(id=pair.id_option_1.id).first()
    option_2 = Option.objects.filter(id=pair.id_option_2.id).first()

    if option_1.quasi_order_original_snod > option_2.quasi_order_original_snod:
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

        if DEPLOY:
            item['img'] = f'{MEDIA_URL}{str(model)}/{str(pair.id)}.png'
        else:
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


def _take_one_criterion_for_each_alternative(option_1_line, option_2_line, path, data, model, pair):
    _write_file(f'{option_1_line}|{option_2_line}|=0\n', path)

    """ Разделили строку по разделителю """
    list_1 = option_1_line.split(';')
    list_2 = option_2_line.split(';')

    """ Номер строки из последнего тестирования А1"""
    new_line_1 = int(list_1[-1])
    """Следующая строка"""
    line_begin = data[new_line_1 + 1]

    """ Номер строки из последнего тестирования А2"""
    new_line_2 = int(list_2[-1])
    """Следующая строка"""
    line_end = data[new_line_2 - 1]

    if (float(line_end[1]) >= 0) or (float(line_begin[1]) <= 0):
        """ Сошлись к центру """
        return converged_to_the_center(model, pair, line_begin, line_end)

    else:
        option_2_line = str(new_line_2 - 1)
        option_1_line = str(new_line_1 + 1)
        name_1, name_2 = _get_name_1_and_name_2(model, line_end, line_begin)
        return False, None, name_1, name_2, option_1_line, option_2_line


def converged_to_the_center(model, pair, line_begin, line_end):
    """Сошлись к центру"""

    if (float(line_end[1]) < 0) and (float(line_begin[1]) <= 0):
        _find_winner(model, pair, empty_option_1=True)
    elif (float(line_end[1]) >= 0) and (float(line_begin[1]) > 0):
        _find_winner(model, pair, empty_option_2=True)
    else:
        _find_winner(model, pair)

    message = get_original_snod_question(model)
    flag_new_pair = True
    return flag_new_pair, message, '', '', None, None


def get_first_question_snod(model, pair, original_snod: bool = False) -> dict:
    """ Получаем первый вопрос """
    data, delimeter_line, n = _read_file(model, pair,original_snod=original_snod)

    if delimeter_line + 1 == n:
        """ Данные не разу не сравнивались """
        line_first = data[0]
        line_end = data[delimeter_line - 1]

        if float(line_first[1]) > 0 and float(line_end[1]) < 0:
            criteria_number = int(line_first[0])
            criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
            name_1 = criteria_1.name

            criteria_number = int(line_end[0])
            criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
            name_2 = criteria_2.name
            question = f'Преимущество по критерию: "{name_1}" важнее чем преимущество по критерию: "{name_2}" ?'

            return {'question': question, 'option_1': pair.id_option_1.id, 'option_2': pair.id_option_2.id,
                       'option_1_line': str(0), 'option_2_line': str(delimeter_line - 1), 'model': model.id,
                       'flag_find_winner': 0}
        else:
            """ Сошлись к центру """
            flag_new_pair, message, trash_1, trash_2, trash_3, trash_4 = converged_to_the_center(model, pair,
                                                                                                 line_first, line_end)
            return message


def _get_name_1_and_name_2(model, line_end, line_begin):
    """Получаем name_1 и name_2, состоящие из одного критерия"""
    criteria_number = int(line_end[0])
    criteria_2 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
    name_2 = f'"{criteria_2.name}"'

    criteria_number = int(line_begin[0])
    criteria_1 = Criterion.objects.filter(id_model=model).get(number=criteria_number)
    name_1 = f'"{criteria_1.name}"'

    return name_1, name_2


def fix_quasi_order_snod(model_id):
    """Правим квазипорядок после нахождения победителя"""
    n = Option.objects.filter(id_model=model_id).count()
    ni = 0
    model = Model.objects.filter(id=model_id).first()
    quasi_max_order_snod = model.quasi_max_order_snod

    real_quasi = 0
    for i in range(quasi_max_order_snod+1):
        options = Option.objects.filter(id_model=model_id, quasi_order_original_snod=i)
        if options:
            if real_quasi != i:
                for option in options:
                    o = Option.objects.get(id=option.id)
                    Option.objects.filter(id=o.id).update(quasi_order_original_snod=real_quasi)
                    ni += 1
                    if ni == n:
                        Model.objects.filter(id=model_id).update(quasi_max_order_snod=real_quasi)
                        options = Option.objects.filter(id_model=model_id)
                        for option in options:
                            print(f'{option.name} {str(option.quasi_order_original_snod)}')
                        return
            real_quasi += 1





