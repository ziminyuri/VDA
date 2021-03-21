import datetime

from services.normalisation import normalisation_time
from spbpu.models import PairsOfOptionsPARK, Option, Criterion, Value, PerfectAlternativePARK, \
    ValueOfPerfectAlternativePARK, RangeValue, Model, HistoryAnswerPACOM
from services.range_value import create_range_value
from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from services.pairs_of_options import _write_file, _replace_line_file
from collections import deque
from django.db.models import Max


def get_park_question(model):
    # Пары для сравнения существуют
    pair = PairsOfOptionsPARK.objects.filter(id_model=model).filter(already_find_winner=False). \
        filter(already_range=True).first()

    if not pair:
        pair = PairsOfOptionsPARK.objects.filter(id_model=model).filter(already_find_winner=False). \
            filter(already_range=False).first()

        if pair:
            data, option_1, option_2 = _get_range_data(model, pair)
            _add_1_to_number_of_question(model)
            return {'flag_find_winner': False, 'flag_range': False, 'flag_compare': False, 'pair': pair.id,
                    'option_1': option_1, 'option_2': option_2, 'data': data}
        else:
            pair = PairsOfOptionsPARK.objects.filter(id_model=model)

            if not pair:
                # Впервые пришли к сранению -> Пар сравнения нет
                # Процесс подготовки данных для ранжирования

                pair = _create_pair(model, FIRST=True)
                data, option_1, option_2 = _get_range_data(model, pair)

                _create_perfect_fit(pair, model)  # Создаем идеальный вариант в паре (лучшие значения по критериям)

                time_begin = datetime.datetime.now()
                Model.objects.filter(id=model.id).update(time_answer_pacom=str(time_begin))
                _add_1_to_number_of_question(model)
                return {'flag_find_winner': 0, 'flag_range': False, 'flag_compare': False, 'pair': pair.id,
                        'option_1': option_1,
                        'option_2': option_2, 'data': data}
            else:
                quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_pacom'))[
                    'quasi_order_pacom__max']
                options_with_quasi_max_order = Option.objects.filter(quasi_order_pacom=quasi_max_order, id_model=model)
                options_with_quasi_0 = Option.objects.filter(quasi_order_pacom=0, id_model=model).first()

                if options_with_quasi_0:
                    # Пока есть альтернативы с квазипорядком равным 0
                    for option in options_with_quasi_max_order:
                        pair = _create_pair(model, option_1=option, option_2=options_with_quasi_0)
                        _create_perfect_fit(pair,
                                            model)  # Создаем идеальный вариант в паре (лучшие значения по критериям)

                    data, option_1, option_2 = _get_range_data(model, pair)
                    _add_1_to_number_of_question(model)
                    return {'flag_find_winner': False, 'flag_range': False, 'flag_compare': False, 'pair': pair.id,
                            'option_1': option_1, 'option_2': option_2, 'data': data}
                else:
                    # Нашли победителей
                    time_end = datetime.datetime.now()
                    time_begin = model.time_answer_shnur
                    time_begin = datetime.datetime.strptime(time_begin, '%Y-%m-%d %H:%M:%S.%f')
                    delta_time_many = time_end - time_begin
                    delta_time_many = normalisation_time(delta_time_many)

                    Model.objects.filter(id=model.id).update(
                        time_answer_pacom=delta_time_many,
                        already_find_winner_PACOM=True
                    )
                    return get_winners_from_model(model)

    if pair.init_file is False:
        # Подготавливаем данные для первого сравнения
        _init_file_for_PARK(model, pair)
    else:
        # Данные в файл для второго сравнения
        winner_find = _fill_file_alternative(model, pair)
        if winner_find:
            response = get_park_question(model)
            return response

    perfect_alternative = PerfectAlternativePARK.objects.get(pair=pair)
    criterions = Criterion.objects.filter(id_model=model.id)

    new_alternative_1, new_alternative_2 = _fill_new_alternative(criterions, perfect_alternative, pair)
    _add_1_to_number_of_question(model)
    return {'flag_range': True, 'alternative_1': new_alternative_1, 'alternative_2': new_alternative_2,
            'criterions': criterions, 'pair': pair.id, 'flag_find_winner': False}


# Записываем данные о ранжировании критериев в паре
def write_range_data(response, model):
    criterions = Criterion.objects.filter(id_model=model.id)
    pair_id = int(response.POST["pair"])
    pair: object = PairsOfOptionsPARK.objects.get(id=pair_id)

    for criterion in criterions:
        try:
            value_name = 'value_' + str(criterion.id) + '_1'
            value = int(response.POST[value_name])
            create_range_value(pair, pair.id_option_1, criterion, value)
        except:
            try:
                value_name = 'value_' + str(criterion.id) + '_2'
                value = int(response.POST[value_name])
                create_range_value(pair, pair.id_option_2, criterion, value)
            except:
                pass

    PairsOfOptionsPARK.objects.filter(id=pair_id).update(already_range=True)


# Записываем результаты сравнения парной компенсации
def write_result_of_compare_pacom(response, model):
    pair_id = int(response.POST["pair"])
    pair: object = PairsOfOptionsPARK.objects.get(id=pair_id)
    answer = int(response.POST["answer"])

    if pair.compensable_option is None:
        # Не найдена компенсируемая альтернатива

        if answer == 1:
            PairsOfOptionsPARK.objects.filter(id=pair_id).update(compensable_option=pair.id_option_2)
        elif answer == 2:
            PairsOfOptionsPARK.objects.filter(id=pair.id).update(compensable_option=pair.id_option_1)
        elif answer == 3:
            _update_pair_to_not_comparable(pair)

    path_dir = MEDIA_ROOT + '/files/models/' + str(model.id) + '/pacom/'
    path = path_dir + 'PAIR' + str(pair.id) + '.txt'
    last_line = _get_last_line(path)
    new_line = last_line + '=' + str(answer) + '\n'
    _replace_line_file(new_line, last_line, path)
    _write_history(pair, model, last_line, answer)


def _create_pair(model, FIRST=False, option_1=None, option_2=None):
    if FIRST:
        options = Option.objects.filter(id_model=model)
        pair = PairsOfOptionsPARK.objects.create(id_option_1=options[0], id_option_2=options[1], id_model=model)
        return pair

    else:
        pair = PairsOfOptionsPARK.objects.create(id_option_1=option_1, id_option_2=option_2, id_model=model)
        return pair


# Возвращает данные для ранжирования: 2 модели и значения критериев
def _get_range_data(model, pair):
    data = []
    criterions = Criterion.objects.filter(id_model=model.id)
    for criterion in criterions:
        id_option_1 = pair.id_option_1
        id_option_2 = pair.id_option_2

        value_2 = Value.objects.filter(id_option=id_option_2, id_criterion=criterion).first()
        value_1 = Value.objects.filter(id_option=id_option_1, id_criterion=criterion).first()

        line = {'criterion': criterion.name, 'criterion_id': criterion.id, 'direction': criterion.direction,
                'pair': pair.id,
                'option_1': value_1.value, 'option_2': value_2.value}
        data.append(line)

    return data, pair.id_option_1.name, pair.id_option_2.name


# Создаем идеальную альтернативу в паре: лучшие значения критериев в паре
def _create_perfect_fit(pair: object, model: object) -> None:
    try:
        perfect_alternative = PerfectAlternativePARK.objects.create(pair=pair)
        criterions = Criterion.objects.filter(id_model=model.id)
        for criterion in criterions:
            value_1 = Value.objects.get(id_option=pair.id_option_1, id_criterion=criterion)
            value_2 = Value.objects.get(id_option=pair.id_option_2, id_criterion=criterion)

            # Направление -> max
            if criterion.direction is True:
                if value_1.value > value_2.value:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_1.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative)
                else:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_2.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative)
            # Направление -> min
            else:
                if value_1.value < value_2.value:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_1.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative)
                else:
                    ValueOfPerfectAlternativePARK.objects.create(value=value_2.value, criteria=criterion,
                                                                 perfect_alternative=perfect_alternative)

    except Exception as e:
        print(e)


# Создаем историю ответов для пары альтернатив
def _init_file_for_PARK(model: object, pair: object) -> None:
    import os

    range_1 = RangeValue.objects.filter(pair=pair).filter(option=pair.id_option_1).filter(value=1).first()
    range_2 = RangeValue.objects.filter(pair=pair).filter(option=pair.id_option_2).filter(value=1).first()

    value_1 = Value.objects.filter(id_option=pair.id_option_1).filter(id_criterion=range_1.criteria).first()
    value_2 = Value.objects.filter(id_option=pair.id_option_2).filter(id_criterion=range_2.criteria).first()

    path_dir = MEDIA_ROOT + '/files/models/' + str(model.id)
    try:
        os.mkdir(path_dir)
    except:
        pass

    path_dir = MEDIA_ROOT + '/files/models/' + str(model.id) + '/pacom/'
    try:
        os.mkdir(path_dir)
    except:
        pass

    path = path_dir + 'PAIR' + str(pair.id) + '.txt'
    line = str(value_1.id_criterion.number) + '|' + str(value_2.id_criterion.number)
    _write_file(line, path)
    PairsOfOptionsPARK.objects.filter(id=pair.id).update(init_file=True)


# Заполняем файл НЕ для первого сравнения
def _fill_file_alternative(model, pair):
    path = MEDIA_ROOT + '/files/models/' + str(pair.id_model.id) + '/pacom/PAIR' + str(pair.id) + '.txt'
    last_line = _get_last_line(path)

    set_1_line = last_line.split('|')[0]
    set_2_line = last_line.split('|')[1].split('=')[0]
    result = int(last_line.split('|')[1].split('=')[1])
    set_1 = set_1_line.split(';')
    set_2 = set_2_line.split(';')

    if pair.compensable_option == pair.id_option_1:
        id_compensable_option = 1
    else:
        id_compensable_option = 2

    criterion_1 = Criterion.objects.get(id_model=model, number=set_1[-1])
    criterion_2 = Criterion.objects.get(id_model=model, number=set_2[-1])

    range_obj_next_1 = None
    range_obj_next_2 = None

    if result == 0 or result == 1 or (result == 2 and id_compensable_option == 2):
        range_obj_old_1 = RangeValue.objects.filter(pair=pair, option=pair.id_option_1, criteria=criterion_1).first()
        range_obj_next_1 = RangeValue.objects.filter(pair=pair, option=pair.id_option_1, value=range_obj_old_1.value + 1).first()

    if result == 0 or result == 2 or (result == 1 and id_compensable_option == 1):
        range_obj_old_2 = RangeValue.objects.filter(pair=pair, option=pair.id_option_2, criteria=criterion_2).first()
        range_obj_next_2 = RangeValue.objects.filter(pair=pair, option=pair.id_option_2, value=range_obj_old_2.value + 1).first()

    if (range_obj_next_1 is not None) and (range_obj_next_2 is not None):
        line = str(range_obj_next_1.criteria.number) + '|' + str(range_obj_next_2.criteria.number)
        _write_file(line, path)

    elif result == 1 and (range_obj_next_1 is not None):
        set_1.append(range_obj_next_1.criteria.number)
        new_line = _fill_line_from_list(set_1)
        line = new_line + '|' + set_2_line
        _write_file(line, path)

    elif result == 2 and (range_obj_next_2 is not None):
        set_2.append(range_obj_next_2.criteria.number)
        new_line = _fill_line_from_list(set_2)
        line = set_1_line + '|' + new_line
        _write_file(line, path)

    else:
        if range_obj_next_2 is None:
            _find_winner_in_pair(pair, id_compensable_option, option_2_is_empty=True)
        elif range_obj_next_1 is None:
            _find_winner_in_pair(pair, id_compensable_option, option_1_is_empty=True)
        else:
            _find_winner_in_pair(pair, id_compensable_option)
        return True

    return False


# Заполняем новые варианты
def _fill_new_alternative(criterions: list, perfect_alternative: object, pair: object):
    new_alternative_1 = []
    new_alternative_2 = []

    path = MEDIA_ROOT + '/files/models/' + str(pair.id_model.id) + '/pacom/PAIR' + str(pair.id) + '.txt'
    with open(path) as file:
        [last_line] = deque(file, maxlen=1) or ['']

    set_1 = last_line.split('|')[0]
    set_2 = last_line.split('|')[1].split('=')[0]
    set_1 = set_1.split(';')
    set_2 = set_2.split(';')

    for criterion in criterions:
        already_get_value = False
        for s1 in set_1:
            if criterion.number == int(s1):
                value_1 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_1)
                value_2 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_2)
                already_get_value = True
        for s2 in set_2:
            if criterion.number == int(s2):
                value_1 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_1)
                value_2 = Value.objects.get(id_criterion=criterion, id_option=pair.id_option_2)
                already_get_value = True

        if already_get_value is False:
            try:
                value_1 = ValueOfPerfectAlternativePARK.objects.get(criteria=criterion,
                                                                    perfect_alternative=perfect_alternative)
                value_2 = value_1
            except Exception as e:
                print(e)

        value_1 = value_1.value
        value_2 = value_2.value

        new_alternative_1.append(value_1)
        new_alternative_2.append(value_2)

    return new_alternative_1, new_alternative_2


def _find_winner_in_pair(pair, id_compensable_option, is_not_comparable=False, option_2_is_empty=False, option_1_is_empty=True):
    if is_not_comparable:
        _update_pair_to_not_comparable(pair)

    path = MEDIA_ROOT + '/files/models/' + str(pair.id_model.id) + '/pacom/PAIR' + str(pair.id) + '.txt'

    # Cлучай первый: есть компенсируемая альтернатива, а последний
    result = _is_comparable(pair, id_compensable_option, option_1_is_empty, option_2_is_empty)

    if result == 1:
        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_pacom=pair.id_option_1.quasi_order_pacom + 1)
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_pacom=pair.id_option_2.quasi_order_pacom - 1)
        PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False)
    elif result == 2:
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_pacom=pair.id_option_2.quasi_order_pacom + 1)
        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_pacom=pair.id_option_1.quasi_order_pacom - 1)
        PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False)
    elif result == 0:
        Option.objects.filter(id=pair.id_option_1.id).update(
            quasi_order_pacom=pair.id_option_1.quasi_order_pacom + 1)
        Option.objects.filter(id=pair.id_option_2.id).update(
            quasi_order_pacom=pair.id_option_2.quasi_order_pacom + 1)
        PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False)
    else:
        _update_pair_to_not_comparable(pair)


def _checking_comparable(pair, set_1, set_2, result):
    pair = PairsOfOptionsPARK.objects.get(id=pair.id)
    compensable_option = pair.compensable_option

    if compensable_option == pair.id_option_1:
        if len(set_1) > 1:
            return False

    elif compensable_option == pair.id_option_2:
        if len(set_2) > 1:
            return False

    return True


def _fill_line_from_list(set: list) -> str:
    line = ''
    for s in set:
        if line == '':
            line = str(s)
        else:
            line = line + ';' + str(s)

    return line


def _update_pair_to_not_comparable(pair):
    # Делает пару не сравнимой

    Option.objects.filter(id=pair.id_option_1.id).update(
        quasi_order_pacom=pair.id_option_1.quasi_order_pacom + 1)
    Option.objects.filter(id=pair.id_option_2.id).update(
        quasi_order_pacom=pair.id_option_2.quasi_order_pacom + 1)
    PairsOfOptionsPARK.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=True)


def _get_last_line(path):
    with open(path) as file:
        [last_line] = deque(file, maxlen=1) or ['']
    return last_line


def _is_comparable(pair, id_compensable_option, option_1_is_empty, option_2_is_empty):
    # Проверка что сравнимы
    flag_1 = False
    flag_2 = False

    flag_1_x2 = False   # Дважды встретился ответ
    flag_2_x2 = False

    first_line = False
    flag_1_not_first = False
    flag_2_not_first = False


    path = MEDIA_ROOT + '/files/models/' + str(pair.id_model.id) + '/pacom/PAIR' + str(pair.id) + '.txt'
    f = open(path)
    for line in f.readlines():
        temp_result = int(line.split('|')[1].split('=')[1])
        if temp_result == 1 and flag_1 is False:
            flag_1 = True
            flag_2 = False
            flag_1_not_first = True

        elif temp_result == 1 and flag_1 is True:
            flag_1_x2 = True

        elif temp_result == 2 and flag_2 is False:
            flag_2 = True
            flag_1 = False
            flag_2_not_first = True

        elif temp_result == 2 and flag_2 is True:
            flag_2_x2 = True

        else:
            flag_1 = False
            flag_2 = False

            flag_1_x2 = False
            flag_2_x2 = False

        first_line = True


    if flag_1_x2 and flag_2_x2:
        return 3 # Не сравнимы
    elif flag_2_x2 and id_compensable_option == 2 and flag_1_not_first:
        return 3  # Не сравнимы
    elif flag_1_x2 and id_compensable_option == 1 and flag_2_not_first:
        return 3  # Не сравнимы
    elif flag_1_x2:
        return 1
    elif flag_2_x2:
        return 2
    elif flag_1:
        return 1
    elif flag_2:
        return 1

    else:
        # Остались критерии по которым не проходили
        if option_1_is_empty:
            return 1
        elif option_2_is_empty:
            return 2
        else:
            return 0  # одинаковы


def _write_history(pair, model, last_line, answer):
    if answer == 1:
        answer_to_history_model = 'Альтернатива №1 предпочтительнее'
    elif answer == 2:
        answer_to_history_model = 'Альтернатива №2 предпочтительнее'
    elif answer == 3:
        answer_to_history_model = 'Альтернативы несравнимы'
    else:
        answer_to_history_model = 'Альтернатива одинаково предпочтительны'

    set_1 = last_line.split('|')[0].split(';')
    set_2 = last_line.split('|')[1].split(';')

    left_list_of_values = ''
    right_list_of_values = ''

    for s in set_1:
        criterion = Criterion.objects.filter(number=int(s), id_model=model).first()
        value = Value.objects.filter(id_criterion=criterion, id_option=pair.id_option_1).first()
        left_list_of_values += ' K' + str(criterion.number) + ': ' + str(value.value)

    for s in set_2:
        criterion = Criterion.objects.filter(number=int(s), id_model=model).first()
        value = Value.objects.filter(id_criterion=criterion, id_option=pair.id_option_2).first()
        right_list_of_values += ' K' + str(criterion.number) + ': ' + str(value.value)

    question = left_list_of_values + ' ? ' + right_list_of_values
    HistoryAnswerPACOM.objects.create(question=question, answer=answer_to_history_model, pair=pair, id_model=model)


def _add_1_to_number_of_question(model):
    Model.objects.filter(id=model.id).update(number_of_questions_pacom=model.number_of_questions_pacom + 1)


def get_winners_from_model(model):
    quasi_max_order = Option.objects.filter(id_model=model).aggregate(Max('quasi_order_pacom'))[
        'quasi_order_pacom__max']
    options_with_quasi_max_order = Option.objects.filter(quasi_order_pacom=quasi_max_order,
                                                         id_model=model)
    return {'flag_find_winner': True, 'winner_options': options_with_quasi_max_order}