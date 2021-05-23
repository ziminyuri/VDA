from modification.models import CriterionModification, ModificationValue, ModificationOption
from model.models import Criterion, Option, Value
from snod.models import PairsOfOptionsTrueSNOD


def init_modificate_criterion_from_base(criterions, model_m):
    """ Инициализируем модифицированные критерии"""

    for criterion in criterions:
        criterion_m = CriterionModification(name=criterion.name, model_m=model_m)
        criterion_m.save()
        criterion_m.criterion.add(criterion)

    return CriterionModification.objects.filter(model_m=model_m)


def add_modification_criterion(request, model_m):
    """Создание нового критерия"""
    name = request.POST['name']
    CriterionModification.objects.create(name=name, model_m=model_m)


def disaggregate_criterion(request, model_m):
    """Дизагрезация критерия (создание модифицированного критерия)"""
    name = request.POST['name']
    id_critation = int(request.POST['criterion'])
    criterion = Criterion.objects.get(id=id_critation)
    criterion_m = CriterionModification(name=name, model_m=model_m)
    criterion_m.save()
    criterion_m.criterion.add(criterion)


def sort_not_disaggregate_and_disaggregate_criterion(model_m):
    """Разделяем дизагрегированные критерии """

    not_disaggregate_criterion, disaggregate_criterion = [], []
    criterions = Criterion.objects.filter(id_model=model_m.model.id)

    for criterion in criterions:
        criterions_m = CriterionModification.objects.filter(model_m=model_m, criterion__in=[criterion])
        if len(criterions_m) == 1:
            not_disaggregate_criterion.append(criterions_m.first())
        else:
            for c in criterions_m:
                disaggregate_criterion.append(c)

    blank_criterions = CriterionModification.objects.filter(model_m=model_m, criterion=None)
    for c in blank_criterions:
        disaggregate_criterion.append(c)

    return not_disaggregate_criterion, disaggregate_criterion


def fill_values_for_not_disaggregate_criterion(not_disaggregate_criterion, model_m):
    """Заполняем значения критериев, которые дизагрегированные"""
    options_m = get_incomparable_options_from_result(model_m)

    for option_m in options_m:
        for criterion in not_disaggregate_criterion:
            value = Value.objects.get(id_option=option_m.parent_option, id_criterion=criterion.criterion.first())
            ModificationValue.objects.create(option=option_m, criterion=criterion, value=value.value)


def get_incomparable_options_from_result(model_m):
    """Получаем список несравнимых альтерантив с финального результата"""
    pairs = PairsOfOptionsTrueSNOD.objects.filter(quasi_level=model_m.model.quasi_max_order_snod,
                                                  flag_winner_option=3, id_model=model_m.model)
    options = []
    for pair in pairs:
        if not (pair.id_option_1 in options):
            options.append(pair.id_option_1)
        if not (pair.id_option_2 in options):
            options.append(pair.id_option_2)
    options = list(set(options))

    for option in options:
        ModificationOption.objects.create(parent_option=option, model_m=model_m)

    option_m = ModificationOption.objects.filter(model_m=model_m)
    return option_m




