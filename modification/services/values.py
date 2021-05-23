from modification.models import ModelModification, CriterionModification, ModificationValue, ModificationPairsOfOptions, \
    ModificationOption
from modification.services.disaggregation import sort_not_disaggregate_and_disaggregate_criterion


def fill_values(request, id):
    """Заполняем значениями из интерфейса"""
    try:
        model_m = ModelModification.objects.get(id=id)
        not_disaggregate_criterion, disaggregate_criterion = sort_not_disaggregate_and_disaggregate_criterion(model_m)
        options = ModificationOption.objects.filter(model_m=model_m)
        k = 1
        for criterion in disaggregate_criterion:
            direction = int(request.POST[f'direction_{str(k)}'])

            if direction == 1:
                direction = True
            else:
                direction = False

            CriterionModification.objects.filter(id=criterion.id).update(direction=direction)

            a = 1
            for option in options:
                value = float(request.POST[f'value_{str(k)}_{str(a)}'])
                ModificationValue.objects.create(value=value, option=option, criterion=criterion)
                a += 1
            k += 1

    except Exception as e:
        return False