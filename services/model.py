import csv
import os
import random

from model.models import Criterion, Model, Option, Value
from services.pairs_of_options import create_files
from snod.models import PairsOfOptions
from VDA.settings import MEDIA_ROOT
from VDA.celery import app
from model.models import User
from django.db.models import Max


@app.task(serializer='json')
def create_model(user_id, demo_model: bool = False, path_csv=None, request=None, number_of_alternatives=None, demo_vkr=False) -> object:
    """ Создание объекта модели (Поиска лучшей альтернативы для задачи выбора) """

    try:
        result = True   # Результат создания и заполнения модели

        if demo_model:
            model = Model.objects.create(is_demo=True, name='Демонстрационная', id_user=User.objects.get(id=user_id))
            if demo_vkr:
                """Выбор 1комнатной квартиры"""
                result = _filling_demo_model_vkr(model)
            else:
                result = _filling_demo_model(model, number_of_alternatives)  # Заполняем модель исходными данными
        else:

            model = Model.objects.create(is_demo=False, name='Пользовательская', id_user=User.objects.get(id=user_id))
            if path_csv:
                result = _filling_model_from_file(model, path_csv=path_csv)  # Заполняем модель исходными данными

            elif request:
                """Данные модели из интерфейса система"""
                result = _filling_custom_model(model, request)

        if result is False:
            model.delete()
            return False

        _create_dir(str(model.id))
        create_files(model)
        Model.objects.filter(id=model.id).update(is_done=True)
        return model

    except Exception as e:
        pass


def _filling_custom_model(model: object, request) -> bool:
    try:
        number_of_criterion = int(request.POST["number_of_criterion"])
        number_of_alternatives = int(request.POST["number_of_alternatives"])

        options_obj_list = []
        for alternatives in range(1, number_of_alternatives + 1):
            name = request.POST[f'alternative_{str(alternatives)}']
            option = Option.objects.create(name=name, id_model=model, number=alternatives)
            options_obj_list.append(option)

        for criterion in range(1, number_of_criterion+1):
            name = request.POST[f'criteria_{str(criterion)}']
            direction = int(request.POST[f'direction_{str(criterion)}'])
            if direction == 1:
                direction = True
            else:
                direction = False

            max = float(request.POST[f'value_{str(criterion)}_1'])
            for alternatives in range(1, number_of_alternatives + 1):
                if max < float(request.POST[f'value_{str(criterion)}_{str(alternatives)}']):
                    max = float(request.POST[f'value_{str(criterion)}_{str(alternatives)}'])
            c = Criterion.objects.create(name=name, id_model=model, direction=direction, max=max,
                                                 number=criterion)

            for alternatives in range(1, number_of_alternatives + 1):
                value = float(request.POST[f'value_{str(criterion)}_{str(alternatives)}'])
                Value.objects.create(value=value, id_option=options_obj_list[alternatives-1], id_criterion=c)

        n = len(options_obj_list)
        k = 1
        for i in range(n):
            for j in range(k, n):
                if i != j:
                    PairsOfOptions.objects.create(id_option_1=options_obj_list[i], id_option_2=options_obj_list[j],
                                                  id_model=model)
            k += 1

    except Exception as e:
        return False


def _filling_model_from_file(model: object, path_csv=None) -> bool:
    # Заполняем модель стартовыми значениями из файла

    options_obj_list = []
    try:
        if path_csv:
            path_csv = f'{MEDIA_ROOT}/{path_csv}'
        else:
            # Если пути файла нет, то файл демо модели
            path_csv = f'{MEDIA_ROOT}/demo/demo.csv'

        with open(path_csv, encoding='utf-8') as r_file:
            file_reader = csv.reader(r_file, delimiter=",")

            # Обрабатыаем 1ю строку с шапкой, где названия критериев
            count = False

            criterion_number = 1
            option_number = 1
            for row in file_reader:
                if count is False:

                    for i in range(2, len(row)):
                        option = Option.objects.create(name=row[i], id_model=model, number=option_number)
                        options_obj_list.append(option)
                        option_number += 1

                    count = True
                    # Обработка шапки закончена

                else:

                    if row[1] == 'min':
                        direction = False
                    else:
                        direction = True

                    max = float(row[2])
                    for i in range(3, len(row)):
                        if max < float(row[i]):
                            max = float(row[i])

                    criterion = Criterion.objects.create(name=row[0], id_model=model, direction=direction, max=max,
                                                         number=criterion_number)

                    criterion_number += 1

                    for i in range(2, len(row)):
                        value = float(row[i])
                        Value.objects.create(value=value, id_option=options_obj_list[i - 2], id_criterion=criterion)

        n = len(options_obj_list)
        k = 1
        for i in range(n):
            for j in range(k, n):
                if i != j:
                    PairsOfOptions.objects.create(id_option_1=options_obj_list[i], id_option_2=options_obj_list[j],
                                                  id_model=model)

            k += 1
    except Exception as e:
        # Если произошли ошибки
        return False

    return True


def _filling_demo_model(model: object, number_of_alternatives: int):
    try:
        options_obj_list = []
        for alternative in range(1, number_of_alternatives + 1):
            option = Option.objects.create(name=f'Alternative { str(alternative)}', id_model=model, number=alternative)
            options_obj_list.append(option)

        criterions_name = ['Количество мест для парковки машин', 'Наличие поблизости конкурентов', 'Плотность населения',
                           'Стоимость участка', 'Поток общественного транспорта', 'Видимость магазина с главной улицы',
                           'Инфраструктура']
        criterions_directions = [True, False, True, False, True, True, True]
        criterions_quality = [0, 1, 0, 1, 1, 1, 1]

        n = len(criterions_name)
        for i in range(n):
            criterion = Criterion.objects.create(name=criterions_name[i], id_model=model, direction=criterions_directions[i], number=i,
                                     max=0)

            for alternative in options_obj_list:
                if criterions_quality[i] == 0:
                    value = random.randint(1, 7)
                else:
                    value = random.randint(100, 4000)
                Value.objects.create(value=value, id_option=alternative, id_criterion=criterion)
            Criterion.objects.filter(id=criterion.id).update(max=value)

        n = len(options_obj_list)
        k = 1
        for i in range(n):
            for j in range(k, n):
                if i != j:
                    PairsOfOptions.objects.create(id_option_1=options_obj_list[i], id_option_2=options_obj_list[j],
                                                  id_model=model)
            k += 1

    except Exception as e:
        return False


def _filling_demo_model_vkr(model: object):
    try:
        options_obj_list = []
        for alternative in range(1, 5):
            option = Option.objects.create(name=f'Alternative { str(alternative)}', id_model=model, number=alternative)
            options_obj_list.append(option)

        criterions_name = ['Тип жилья', 'Площадь', 'Расстояние до метро',
                           'Стоимость', 'Год постройки', 'Санузел',
                           'Расстояние до центра']
        criterions_directions = [True, True, False, False, True, True, False]

        alternative_1 = [1, 36.5, 5, 6000000, 2020, 1, 7]
        alternative_2 = [2, 43, 1, 10300000, 2022, 1, 5]
        alternative_3 = [1, 30, 7, 4900000, 1964, 2, 3]
        alternative_4 = [1, 34, 3, 4580000, 2017, 1, 9]

        """Данные для качественных критериев"""
        alternative_1_name =['Вторичное', '', '7 мин. на транспорте', '', '', 'Совмещенный', 'ст. Комменданский проспект']
        alternative_2_name =['Ноовостройка', '', '17 мин. пешком', '', '', 'Совмещенный', 'ст. Лесная']
        alternative_3_name =['Вторичное', '', '10 мин. на транспорте', '', '', 'Раздельный', 'ст. Парк Победы']
        alternative_4_name =['Вторичное', '', '5 мин. на транспорте', '', '', 'Совмещенный', 'ст. Шушары']

        n = len(criterions_name)

        for i in range(n):
            Criterion.objects.create(name=criterions_name[i], id_model=model, direction=criterions_directions[i],
                                     number=i, max=0)

        criterions = Criterion.objects.filter(id_model=model)
        k = 0

        for alternative in options_obj_list:
            i = 0
            for criterion in criterions:
                if k == 0:
                    Value.objects.create(value=alternative_1[i], id_option=alternative, id_criterion=criterion,
                                         name=alternative_1_name[i])
                elif k == 1:
                    Value.objects.create(value=alternative_2[i], id_option=alternative, id_criterion=criterion,
                                         name=alternative_2_name[i])
                elif k == 2:
                    Value.objects.create(value=alternative_3[i], id_option=alternative, id_criterion=criterion,
                                         name=alternative_3_name[i])
                elif k == 3:
                    Value.objects.create(value=alternative_4[i], id_option=alternative, id_criterion=criterion,
                                         name=alternative_4_name[i])
                i += 1

            k +=1

        for criterion in criterions:
            max_value = Value.objects.filter(id_criterion=criterion).aggregate(Max('value'))['value__max']
            Criterion.objects.filter(id=criterion.id).update(max=max_value)


        n = len(options_obj_list)
        k = 1
        for i in range(n):
            for j in range(k, n):
                if i != j:
                    PairsOfOptions.objects.create(id_option_1=options_obj_list[i], id_option_2=options_obj_list[j],
                                                  id_model=model)
            k += 1

    except Exception as e:
        return False


def _create_dir(dir_name: str) -> None:
    path1 = f'{MEDIA_ROOT}/files/models/{dir_name}'
    path2 = f'{MEDIA_ROOT}/files/models/{dir_name}/original_snod'
    path3 = f'{MEDIA_ROOT}/{dir_name}'

    try:
        os.mkdir(path1)
        os.mkdir(path2)
        os.mkdir(path3)
    except OSError:
        print("Создать директорию %s не удалось" % path2)


def get_model_data(model_id):
    # Возвращает данные модели из файла для отображения
    model = Model.objects.get(id=model_id)
    options = Option.objects.filter(id_model=model)

    header = ['№','Наименование критерия', 'Направление']
    for option in options:
        header.append(option.name)

    data = []
    criterions = Criterion.objects.filter(id_model=model)
    for criterion in criterions:
        line = [criterion.name]
        if criterion.direction:
            line.append('Max')
        else:
            line.append('Min')
        for option in options:
            value = Value.objects.get(id_option=option, id_criterion=criterion)
            if value.name != '':
                line.append(f'{value.value} – ({value.name})')
            else:
                line.append(value.value)
        data.append(line)

    return data, header
