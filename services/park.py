from spbpu.models import PairsOfOptionsPARK, Option, Criterion, Value, PerfectAlternativePARK, \
    ValueOfPerfectAlternativePARK
from services.range_value import create_range_value


def get_park_question(model):
    pairs = PairsOfOptionsPARK.objects.filter(id_model=model)
    if not pairs:
        # Впервые пришли к сранению -> Пар сравнения нет
        pair = _create_pair(model, FIRST=True)
        data, option_1, option_2 = _get_range_data(model, pair)

        _create_perfect_fit(pair, model)   # Создаем идеальный вариант в паре (лучшие значения по критериям)

        return {'flag_find_winner': 0, 'flag_range': False, 'pair': pair.id, 'option_1': option_1, 'option_2': option_2,
                'data': data}


def write_range_data(response, model):
    # Записываем данные о ранжировании критериев в паре
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

    pass


def _create_pair(model, FIRST=False):
    if FIRST:
        options = Option.objects.filter(id_model=model)
        pair = PairsOfOptionsPARK.objects.create(id_option_1=options[0], id_option_2=options[1], id_model=model)
        return pair


def _get_range_data(model, pair):
    # Возвращает данные для ранжирования: 2 модели и значения критериев

    data = []
    criterions = Criterion.objects.filter(id_model=model.id)
    for criterion in criterions:
        value_1 = Value.objects.get(id_option=pair.id_option_1, id_criterion=criterion)
        value_2 = Value.objects.get(id_option=pair.id_option_2, id_criterion=criterion)
        line = {'criterion': criterion.name, 'criterion_id': criterion.id, 'direction': criterion.direction, 'pair': pair.id,
                'option_1': value_1.value, 'option_2': value_2.value}
        data.append(line)

    return data, pair.id_option_1.name, pair.id_option_2.name


def _create_perfect_fit(pair: object, model: object) -> None:
    # Создаем идеальную альтернативу в паре: лучшие значения критериев в паре

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

