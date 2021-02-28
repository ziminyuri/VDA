from spbpu.models import RangeValue


def create_range_value(pair: object, option: object, criteria: object, value: int) -> None:
    # Создаем объект модели ранжирования в методе ПАРК

    try:
        RangeValue.objects.create(pair=pair, option=option, criteria=criteria, value=value)
    except Exception as e:
        print(e)