from spbpu.models import Model, Option, Criterion, Value, PairsOfOptions
import os
import csv
from Verbal_Decision_Analysis.settings import MEDIA_ROOT


def create_model(demo_model: bool = False, path_csv=None, request=None) -> object:
    # Создание объекта модели (Поиска лучшей альтернативы для задачи выбора)
    try:
        result = True   # Результат создания и заполнения модели

        if demo_model:
            model = Model.objects.create(is_demo=True, name='Демонстрационная')
            result = _filling_model_from_file(model)  # Заполняем модель исходными данными
        else:
            model = Model.objects.create(is_demo=False, name='Пользовательская')
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

    except:
        pass


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
