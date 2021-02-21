from spbpu.models import PairsOfOptionsPARK, Option, Criterion, Value


def get_park_question(model):
    pairs = PairsOfOptionsPARK.objects.filter(id_model=model)
    if not pairs:
        # Впервые пришли к сранению -> Пар сравнения нет
        pair = _create_pair(model, FIRST=True)
        data, option_1, option_2 = _get_range_data(model, pair)
        return {'flag_find_winner': 0, 'flag_range': False, 'pair': pair.id, 'option_1': option_1, 'option_2': option_2,
                'data': data}


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
        line = [criterion.name]
        value = Value.objects.get(id_option=pair.id_option_1, id_criterion=criterion)
        line.append(value.value)
        value = Value.objects.get(id_option=pair.id_option_2, id_criterion=criterion)
        line.append(value.value)
        data.append(line)

    return data, pair.id_option_1.name, pair.id_option_2.name


