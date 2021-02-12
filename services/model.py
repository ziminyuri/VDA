from api.models import Model, Option, Criterion, Value, PairsOfOptions
import os
import csv


def create_model(demo_model: bool = False) -> object:
    # Создание объекта модели (Поиска лучшей альтернативы для задачи выбора)
    try:
        if demo_model:
            model = Model.objects.create(is_demo=True, name='Демонстрационная')
            filling_model_for_start(model)  # Заполняем модель исходными данными
        else:
            model = Model.objects.create(is_demo=True, name='Пользовательская')

        _create_dir(str(model.id))

        return model

    except:
        pass


def filling_model_for_start(model: object):
    # Заполняем модель стартовыми значениями

    options_obj_list = []
    with open("api/files/demo.csv", encoding='utf-8') as r_file:
        file_reader = csv.reader(r_file, delimiter=",")
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


def _create_dir(dir_name: str) -> None:
    path1 = 'api/files/models/' + dir_name
    path2 = 'media/' + dir_name

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
