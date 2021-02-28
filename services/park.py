from spbpu.models import PairsOfOptionsPARK, Option, Criterion, Value, PerfectAlternativePARK, \
    ValueOfPerfectAlternativePARK, HistoryAnswerPARK, ValueOfSetOfOptions, SetOfOptions, RangeValue
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

    # Пары для сравнения существуют
    pair = PairsOfOptionsPARK.objects.filter(id_model=model).filter(winner_option=None).first()

    history_of_answer_of_pair = HistoryAnswerPARK.objects.filter(id_model=model).filter(pair=pair)
    if not history_of_answer_of_pair:
        history_of_answer_of_pair = _create_history_of_answer_of_pair(model, pair)

    perfect_alternative = PerfectAlternativePARK.objects.get(pair=pair)
    criterions = Criterion.objects.filter(id_model=model.id)

    new_alternative_1, new_alternative_2 = _fill_new_alternative(criterions, perfect_alternative,
                                                                 history_of_answer_of_pair)

    return {'flag_range': True, 'alternative_1': new_alternative_1, 'alternative_2': new_alternative_2}


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


def _create_pair(model, FIRST=False):
    if FIRST:
        options = Option.objects.filter(id_model=model)
        pair = PairsOfOptionsPARK.objects.create(id_option_1=options[0], id_option_2=options[1], id_model=model)
        return pair


# Возвращает данные для ранжирования: 2 модели и значения критериев
def _get_range_data(model, pair):


    data = []
    criterions = Criterion.objects.filter(id_model=model.id)
    for criterion in criterions:
        value_1 = Value.objects.get(id_option=pair.id_option_1, id_criterion=criterion)
        value_2 = Value.objects.get(id_option=pair.id_option_2, id_criterion=criterion)
        line = {'criterion': criterion.name, 'criterion_id': criterion.id, 'direction': criterion.direction, 'pair': pair.id,
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
def _create_history_of_answer_of_pair(model: object, pair: object, first: bool = False) -> object:
    set_1 = SetOfOptions.objects.create(option=pair.id_option_1)
    set_2 = SetOfOptions.objects.create(option=pair.id_option_2)
    history_of_answer_of_pair = HistoryAnswerPARK.objects.create(set_option_1=set_1, set_option_2=set_2,
                                                                 id_model=model, pair=pair)

    if first is True:
        range_1 = RangeValue.objects.filter(pair=pair).filter(option=pair.id_option_1).filter(value=1).first()
        range_2 = RangeValue.objects.filter(pair=pair).filter(option=pair.id_option_2).filter(value=1).first()

        value_1 = Value.objects.filter(id_option=pair.id_option_1).filter(id_criterion=range_1.criteria).first()
        value_2 = Value.objects.filter(id_option=pair.id_option_2).filter(id_criterion=range_2.criteria).first()

        ValueOfSetOfOptions.objects.create(set_option=set_1, value=value_1)
        ValueOfSetOfOptions.objects.create(set_option=set_2, value=value_2)


    return history_of_answer_of_pair


# Заполняем новые варианты
def _fill_new_alternative(criterions: list, perfect_alternative: object, history_of_answer_of_pair: object):
    new_alternative_1 = []
    new_alternative_2 = []

    value_of_set_1 = ValueOfSetOfOptions.objects.filter(set_option=history_of_answer_of_pair.set_option_1)
    value_of_set_2 = ValueOfSetOfOptions.objects.filter(set_option=history_of_answer_of_pair.set_option_2)

    for criterion in criterions:
        for v in value_of_set_1:
            if v.value.id_criterion == criterion:
                pass


    return new_alternative_1, new_alternative_2


