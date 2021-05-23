from snod.models import PairsOfOptionsTrueSNOD
from model.models import Model


def check_comparable_in_result(id):
    """Проверяем есть ли несравнимые альтернативы в результате"""
    model = Model.objects.get(id=id)
    pairs = PairsOfOptionsTrueSNOD.objects.filter(quasi_level=model.quasi_max_order_snod, flag_winner_option=3)
    if pairs:
        return True
    else:
        return False
