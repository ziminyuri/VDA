import csv
import os
import random

from spbpu.models import Criterion, Model, Option, PairsOfOptions, Value
from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from services.services import get_userprofile


# Создание объекта модели (Поиска лучшей альтернативы для задачи выбора)
def create_model(demo_model: bool = False, path_csv=None, request=None) -> object:
    try:
        result = True   # Результат создания и заполнения модели
        user_profile = get_userprofile(request)
        if demo_model:
            model = Model.objects.create(is_demo=True, name='Демонстрационная', id_user=user_profile)
            number_of_alternatives = int(request.POST['number'])
            result = _filling_demo_model(model, number_of_alternatives)  # Заполняем модель исходными данными
        else:

            model = Model.objects.create(is_demo=False, name='Пользовательская', id_user=user_profile)
            if path_csv:
                result = _filling_model_from_file(model, path_csv=path_csv)  # Заполняем модель исходными данными

            elif request:
                # Данные модели из интерфейса система
                result = _filling_custom_model(model, request)

        if result is False:
            model.delete()
            return False

        _create_dir(str(model.id))

        return model

    except Exception as e:
        print(e)


def _filling_custom_model(model: object, request) -> bool:
    try:
        number_of_criterion = int(request.POST["number_of_criterion"])
        number_of_alternatives = int(request.POST["number_of_alternatives"])

        options_obj_list = []
        for alternatives in range(1, number_of_alternatives + 1):
            name = request.POST["alternative_" + str(alternatives)]
            option = Option.objects.create(name=name, id_model=model, number=alternatives)
            options_obj_list.append(option)

        for criterion in range(1, number_of_criterion+1):
            name = request.POST["criteria_"+str(criterion)]
            direction = int(request.POST["direction_"+str(criterion)])
            if direction == 1:
                direction = True
            else:
                direction = False

            max = float (request.POST["value_" + str(criterion)+ "_1"])
            for alternatives in range(1, number_of_alternatives + 1):
                if max < float(request.POST["value_" + str(criterion) + "_" + str(alternatives)]):
                    max = float(request.POST["value_" + str(criterion) + "_" + str(alternatives)])
            c = Criterion.objects.create(name=name, id_model=model, direction=direction, max=max,
                                                 number=criterion)

            for alternatives in range(1, number_of_alternatives + 1):
                value = float(request.POST["value_" + str(criterion) + "_" + str(alternatives)])
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
            path_csv = MEDIA_ROOT + "/" + path_csv
        else:
            # Если пути файла нет, то файл демо модели
            path_csv = MEDIA_ROOT + "/demo/demo.csv"

        with open(path_csv, encoding='utf-8') as r_file:
            file_reader = csv.reader(r_file, delimiter=",")

            # Обрабатыаем 1ю строку с шапкой, где названия критериев
            count = False #

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
            option = Option.objects.create(name='Alternative ' + str(alternative), id_model=model, number=alternative)
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

    except Exception as e:
        return False


def _create_dir(dir_name: str) -> None:
    path1 = MEDIA_ROOT + '/files/models/' + dir_name
    path2 = MEDIA_ROOT + '/' + dir_name

    try:
        os.mkdir(path1)
        os.mkdir(path2)
    except OSError:
        print("Создать директорию %s не удалось" % path2)


def get_model_data(model_id):
    # Возвращает данные модели из файла для отображения
    model = Model.objects.get(id=model_id)
    options = Option.objects.filter(id_model=model)

    header = ['№','Наименование критерия']
    for option in options:
        header.append(option.name)

    data = []
    criterions = Criterion.objects.filter(id_model=model)
    for criterion in criterions:
        line = [criterion.name]
        for option in options:
            value = Value.objects.get(id_option=option, id_criterion=criterion)
            line.append(value.value)
        data.append(line)

    return data, header
