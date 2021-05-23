import os

import cv2
import numpy as np
from PIL.Image import Image
from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import ImageFont
from django.db.models import Max

from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from modification.models import ModificationPairsOfOptions, ModificationOption, CriterionModification, ModificationValue, ModelModification
from services.pairs_of_options import _sort, _write_file
from services.snod_original import get_data_from_meaage


def get_original_snod_modification_question(model_m):
    """Получение вопроса"""
    pair = ModificationPairsOfOptions.objects.filter(model_m=model_m).filter(already_find_winner=False).first()

    if pair:
        """ Пары для сравнения существуют """
        pair = ModificationPairsOfOptions.objects.filter(model_m=model_m, already_find_winner=False,
                                                         flag_not_compared=True).first()

        if pair:
            """ Есть пара без найденого победителя, получаем вопрос """
            return get_first_question_snod(model_m, pair, original_snod=True)

    else:
        """ Пары для сравнения не существуют """
        pair = ModificationPairsOfOptions.objects.filter(model_m=model_m)

        if not pair:
            """ Получаем самую первую пару для сравнения"""
            _create_dirs(model_m)
            pair = _create_pair(model_m, 0, FIRST=True)
            return get_first_question_snod(model_m, pair, original_snod=True)

        """ Первая пара уже создана. Работаем с квазипорядками"""
        quasi_max_order = ModificationOption.objects.filter(model_m=model_m).aggregate(Max('quasi_order_original_snod'))[
            'quasi_order_original_snod__max']
        options_with_quasi_max_order = ModificationOption.objects.filter(quasi_order_original_snod=quasi_max_order, model_m=model_m)
        options_with_quasi_first = ModificationOption.objects.filter(quasi_order_original_snod=-1, model_m=model_m).first()

        if options_with_quasi_first:
            """ Есть альтернативы с квазипорядком равным -1 (Начальный квазипорядок)"""
            for option in options_with_quasi_max_order:
                """ Создаем пары с максимальным квазипорядоком и минимальным квазипорядком (-1) """
                pair = _create_pair(model_m, quasi_max_order, option_1=option, option_2=options_with_quasi_first)

            return get_first_question_snod(model_m, pair, original_snod=True)

        else:
            """Нашли победителей"""
            ModelModification.objects.filter(id=model_m.id).update(already_find_winner=True)
            return {'flag_find_winner': 1}


def get_first_question_snod(model_m, pair, original_snod: bool = False) -> dict:
    """ Получаем первый вопрос """
    data, delimeter_line, n = _read_file(model_m, pair)

    if delimeter_line + 1 == n:
        """ Данные не разу не сравнивались """
        line_first = data[0]
        line_end = data[delimeter_line - 1]

        if float(line_first[1]) > 0 and float(line_end[1]) < 0:
            criteria_number = int(line_first[0])
            criteria_1 = CriterionModification.objects.filter(model_m=model_m).get(number=criteria_number)
            name_1 = criteria_1.name

            criteria_number = int(line_end[0])
            criteria_2 = CriterionModification.objects.filter(model_m=model_m).get(number=criteria_number)
            name_2 = criteria_2.name
            question = f'Преимущество по критерию: "{name_1}" важнее чем преимущество по критерию: "{name_2}" ?'

            return {'question': question, 'option_1': pair.id_option_1.id, 'option_2': pair.id_option_2.id,
                       'option_1_line': str(0), 'option_2_line': str(delimeter_line - 1), 'model': model_m.id,
                       'flag_find_winner': 0}
        else:
            """ Сошлись к центру """
            flag_new_pair, message, trash_1, trash_2, trash_3, trash_4 = converged_to_the_center(model_m, pair,
                                                                                                 line_first, line_end)
            return message


def _create_pair(model_m, quasi_max_order, FIRST=False, option_1=None, option_2=None):
    if FIRST:
        options = ModificationOption.objects.filter(model_m=model_m)
        pair = ModificationPairsOfOptions.objects.create(option_1=options[0], option_2=options[1], model_m=model_m)

    else:
        pair = ModificationPairsOfOptions.objects.create(option_1=option_1, option_2=option_2, model_m=model_m,
                                                     quasi_level=quasi_max_order+1)

    rows = make_snd(model_m, pair)
    rows = _sort(rows)  # Сортируем штобы привести к шкале и нормализуем под проценты
    _init_file(rows, pair, model_m)
    _create_image_for_pair(rows, model_m, pair)

    return pair


def make_snd(model_m, pair):
    """ Получение ШНР """
    criterions = CriterionModification.objects.filter(model_m=model_m)
    rows = []

    for criterion in criterions:

        a1 = ModificationValue.objects.get(option=pair.option_1, criterion=criterion)
        a2 = ModificationValue.objects.get(option=pair.option_2, criterion=criterion)

        a12 = (a1.value + a2.value) / 2

        # is max
        if criterion.direction is True:
            a1 = a1.value / a12
            a2 = a2.value / a12

        # is min
        else:
            a1 = 2 - (a1.value / a12)
            a2 = 2 - (a2.value / a12)

        d = a1 - a2  # Разность

        col = [criterion.number, d]
        rows.append(col)

    return rows


def _create_dirs(model_m,):
    path1 = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/'
    path2 = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/{str(model_m.id)}'
    path3 = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/{str(model_m.id)}/images'

    try:
        os.mkdir(path1)
        os.mkdir(path2)
        os.mkdir(path3)
    except Exception as e:
        pass


def _init_file(data: list, pair: str, model_m: str) -> None:
    path = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/{str(model_m.id)}/{str(pair.id)}.txt'
    pair_file = open(path, 'w')

    for row in data:
        line = ';'.join([str(i) for i in row])
        pair_file.write(line)
        pair_file.write('\n')

    pair_file.write('#####\n')
    pair_file.close()


def _create_image_for_pair(rows, model_m, pair):
    length = len(rows)
    if length > 10:
        return

    w, h = 480, 480
    distance = 30
    interval = int((w-distance) / (length+3)) # Интервал между стрелок

    if abs(float(rows[0][1])) > abs(float(rows[length-1][1])):
        max = float(rows[0][1])

    else:
        max = float(rows[length-1][1])

    min_value = str(round(rows[-1][1], 2))

    h_scale = h - 80  # ДЛя графиков чтобы оставить место подписи

    for row in rows:
        if (max < 0 and float(row[1]) > 0):
            row[1] = int((float(row[1])) * (h_scale/2 - 10) / max * (-1))
        elif (max < 0 and float(row[1]) < 0):
            row[1] = int((float(row[1])) * (h_scale / 2 - 10) / max * (-1))
        else:
            row[1] = int((float(row[1])) * (h_scale / 2 - 10) / max)

    im = Image.new('RGB', (w, h), (195, 197, 200))
    na = np.array(im)

    h_begin = int(h_scale/ 2)
    # Оси
    na = cv2.arrowedLine(na, (3, h_begin), (w - 5, h_begin), (0, 0, 0), 4)
    na = cv2.arrowedLine(na, (distance, h-50), (distance, 5), (0, 0, 0), 4)

    h_end = int(h_scale / 2 - (rows[-1][1]))
    na = cv2.line(na, (15, h_end), (45, h_end), (0, 0, 0), 4)

    distance += interval * 2
    for row in rows:

        h_end = int(h_scale/2 - (row[1]))
        na = cv2.arrowedLine(na, (distance, h_begin), (distance, h_end), (0, 0, 0), 4)
        distance += interval

    path = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/{str(model_m.id)}/images/{str(pair.id)}.png'
    Image.fromarray(na).save(path)

    # Делаем подписи
    img = Image.open(path)
    idraw = ImageDraw.Draw(img)
    path_font = f'{MEDIA_ROOT}/fonts/9041.ttf'
    font = ImageFont.truetype(path_font, size=18)

    distance = 30
    distance += interval * 2
    for row in rows:
        text = str((row[0])+1)
        if float(row[1]) > 0:
            idraw.text((distance, int(h_scale / 2 + 50)), text, font=font, fill='#000000')
        elif float(row[1]) == 0:
            idraw.ellipse([distance-10, h_begin-10, distance+10, h_begin+10], fill='#000000')
            idraw.text((distance, int(h_scale / 2 - 50)), text, font=font, fill='#000000')
        else:
            idraw.text((distance, int(h_scale / 2 - 50)), text, font=font, fill='#000000')
        distance += interval

    text = pair.option_1.name
    length = len(text) * 9
    idraw.text((w-15-length, h-40), pair.option_2.name, font=font, fill='#000000')
    idraw.text((15, h-40), text, font=font, fill='#000000')

    idraw.text((w-45, h/2), 'Ox', font=font, fill='#000000')
    idraw.text((60, 15), 'Oy', font=font, fill='#000000')

    # Подписываем риски
    h_end = int(h_scale / 2 - (rows[-1][1]))

    idraw.text((45, h_end), min_value, font=font, fill='#000000')

    img.save(path)


def converged_to_the_center(model_m, pair, line_begin, line_end):
    """Сошлись к центру"""

    if (float(line_end[1]) < 0) and (float(line_begin[1]) <= 0):
        _find_winner(model_m, pair, empty_option_1=True)
    elif (float(line_end[1]) >= 0) and (float(line_begin[1]) > 0):
        _find_winner(model_m, pair, empty_option_2=True)
    else:
        _find_winner(model_m, pair)

    message = get_original_snod_modification_question(model_m)
    flag_new_pair = True
    return flag_new_pair, message, '', '', None, None


def _find_winner(model_m: object, pair: object, empty_option_1=False, empty_option_2=False) -> None:
    pair = ModificationPairsOfOptions.objects.get(id=pair.id)
    if pair.flag_winner_option != -1:
        return

    path = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/{str(model_m.id)}/{str(pair.id)}.txt'
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
    return ModificationPairsOfOptions.objects.get(id=pair.id)


def _read_file(model_m, pair):
    path = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/{str(model_m.id)}/{str(pair.id)}.txt'

    data = []

    with open(path) as f:
        lines = f.readlines()

    # Данные в файле представлены как сначала исходные данные
    # потом cтрока разделитель #####
    # потом данные которые получены в ходе выполнения опросов

    delimeter_line = 0

    n = len(lines)
    for i in range(n):
        if lines[i] == '#####\n':
            delimeter_line = i
            break

        else:
            l = lines[i].split(';')
            l[1] = l[1].split('\n')[0]
            data.append(l)

    return data, delimeter_line, n


def _update_quasi_order_snod_for_pair(pair, result):
    """ Обновляем квазипорядок для альтерантив в паре """

    max_quasi_order_original_snod = pair.quasi_level

    if pair.option_1.quasi_order_original_snod == -1 and pair.option_2.quasi_order_original_snod == -1:
        lose = 0
    elif pair.option_1.quasi_order_original_snod > pair.option_2.quasi_order_original_snod:
        lose = pair.option_1.quasi_order_original_snod
    else:
        lose = pair.option_1.quasi_order_original_snod

    if result == 1:

        ModificationOption.objects.filter(id=pair.option_1.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)
        ModificationOption.objects.filter(id=pair.option_2.id).update(
            quasi_order_original_snod=lose)
        ModificationPairsOfOptions.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                                 flag_winner_option=1)
    elif result == 2:
        ModificationOption.objects.filter(id=pair.option_2.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)
        ModificationOption.objects.filter(id=pair.option_1.id).update(
            quasi_order_original_snod=lose)
        ModificationPairsOfOptions.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                                 flag_winner_option=2)
    else:
        ModificationOption.objects.filter(id=pair.option_1.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)
        ModificationOption.objects.filter(id=pair.option_2.id).update(
            quasi_order_original_snod=max_quasi_order_original_snod)

        if result == 0:
            ModificationPairsOfOptions.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=False,
                                                                     flag_winner_option=0)
        else:
            ModificationPairsOfOptions.objects.filter(id=pair.id).update(already_find_winner=True, is_not_comparable=True,
                                                                     flag_winner_option=3)


def write_snod_modification_answer(answer, message=None):
    answer, option_1, option_2, option_1_line, option_2_line, model_id, question = get_data_from_meaage(answer, message)
    model_m = ModelModification.objects.get(id=model_id)
    pair = ModificationPairsOfOptions.objects.filter(option_1=option_1, option_2=option_2).first()

    data, delimeter_line, n = _read_file(model_m, pair)

    path = f'{MEDIA_ROOT}/files/models/{str(model_m.model.id)}/original_snod/modification/{str(model_m.id)}/{str(pair.id)}.txt'
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
                flag_new_pair, message, name_1, name_2, trash_1, trash_2 = converged_to_the_center(model_m, pair, line_begin, line_end)

            else:
                """К центру не сошлись, формируем name_1 и name_2 для вопроса"""
                flag_new_pair = False
                criteria_number = int(line_begin[0])
                criteria_1 = CriterionModification.objects.filter(model_m=model_m).get(number=criteria_number)
                name_1 = f'"{criteria_1.name}"'

                first_line = True
                for row in list_2:
                    if row == '-1':
                        """ ? """
                        _find_winner(model_m, pair)
                        message =  get_original_snod_modification_question(model_m)
                        flag_new_pair = True
                    else:
                        criteria_number = data[int(row[0])][0]
                        criteria_2 = CriterionModification.objects.filter(model_m=model_m).get(number=criteria_number)
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
                name_1, name_2 = _get_name_1_and_name_2(model_m, line_end, line_begin)

    elif answer == 0:
        """Равноценны"""
        flag_new_pair, message, name_1, name_2, option_1_line, option_2_line = _take_one_criterion_for_each_alternative(option_1_line, option_2_line,
                                                                                          path, data, model_m, pair)

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
                flag_new_pair, message, name_1, name_2, trash_1, trash_2 = converged_to_the_center(model_m, pair, line_begin, line_end)

            else:
                """К центру не сошлись, формируем name_1 и name_2 для вопроса"""
                flag_new_pair = False
                criteria_number = int(line_end[0])
                criteria_2 = CriterionModification.objects.filter(model=model_m).get(number=criteria_number)
                name_2 = criteria_2.name

                first_line = True
                for row in list_1:
                    if row == '-1':
                        """ ? """
                        _find_winner(model_m, pair)
                        message = get_original_snod_modification_question(model_m)
                        flag_new_pair = True
                    else:
                        criteria_number = data[int(row[0])][0]
                        criteria_1 = CriterionModification.objects.filter(id_model=model_m).get(number=criteria_number)
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
                name_1, name_2 = _get_name_1_and_name_2(model_m, line_end, line_begin)

    try:
        if message['flag_find_winner'] == 1:
            """ Был найден победитель"""

            quasi_max_order = ModificationOption.objects.filter(model_m=model_m).aggregate(Max('quasi_order_original_snod'))[
                'quasi_order_original_snod__max']
            ModelModification.objects.filter(id=model_id).update(quasi_max_order_snod=quasi_max_order)
            # fix_quasi_order_snod(model_id)
            # get_graph_snod.delay(model_id)
            return message
    except: pass

    if name_1 == '' or name_2 == '':
        _find_winner(model_m, pair)
        message = get_original_snod_modification_question(model_m)

    elif flag_new_pair is False:

        question = f'Преимущество по критерию: {name_1} важнее чем преимущество по критерию: {name_2} ?'
        message = {'question': question, 'option_1': option_1, 'option_2': option_2,
                   'option_1_line': option_1_line, 'option_2_line': option_2_line, 'model': model_m.id,
                   'flag_find_winner': 0}

    elif message is None:
        message = get_original_snod_modification_question(model_m)

    return message


def _get_name_1_and_name_2(model_m, line_end, line_begin):
    """Получаем name_1 и name_2, состоящие из одного критерия"""
    criteria_number = int(line_end[0])
    criteria_2 = CriterionModification.objects.filter(model_m=model_m).get(number=criteria_number)
    name_2 = f'"{criteria_2.name}"'

    criteria_number = int(line_begin[0])
    criteria_1 = CriterionModification.objects.filter(model_m=model_m).get(number=criteria_number)
    name_1 = f'"{criteria_1.name}"'

    return name_1, name_2


def _take_one_criterion_for_each_alternative(option_1_line, option_2_line, path, data, model_m, pair):
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
        return converged_to_the_center(model_m, pair, line_begin, line_end)

    else:
        option_2_line = str(new_line_2 - 1)
        option_1_line = str(new_line_1 + 1)
        name_1, name_2 = _get_name_1_and_name_2(model_m, line_end, line_begin)
        return False, None, name_1, name_2, option_1_line, option_2_line
