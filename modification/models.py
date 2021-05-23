from django.db import models
from model.models import Model, Criterion, Option


class TypeModification(models.Model):
    """Тип модификации """
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class ModelModification(models.Model):
    """Модифицированная модель"""
    type = models.ForeignKey(TypeModification, on_delete=models.CASCADE)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    already_find_winner = models.BooleanField(default=False)


class CriterionModification(models.Model):
    """ Модифицированный критерий """

    name = models.CharField(max_length=200, verbose_name='Название критерия')
    criterion = models.ManyToManyField(Criterion, verbose_name='Исходный критерий', blank=True)
    for_snod = models.BooleanField(default=False)
    for_pacom = models.BooleanField(default=False)
    direction = models.BooleanField(default=True)
    model_m = models.ForeignKey(ModelModification, on_delete=models.CASCADE)

    """ Порядковый номер критерия """
    number = models.IntegerField()


class ModificationOption(models.Model):
    """Модифицированная альтернатива"""

    model_m = models.ForeignKey(ModelModification, on_delete=models.CASCADE)
    parent_option = models.ForeignKey(Option, on_delete=models.CASCADE)
    quasi_order_pacom = models.IntegerField(default=-1)
    quasi_order_original_snod = models.IntegerField(default=-1)



class ModificationValue(models.Model):
    """ Модифицированное значение """

    value = models.FloatField()
    option = models.ForeignKey(ModificationOption, on_delete=models.CASCADE)
    criterion = models.ForeignKey(CriterionModification, on_delete=models.CASCADE)


class ModificationPairsOfOptions(models.Model):
    """ Модифицированная пара вариантов """

    option_1 = models.ForeignKey(ModificationOption, on_delete=models.CASCADE, related_name='id_option_1_modification')
    option_2 = models.ForeignKey(ModificationOption, on_delete=models.CASCADE, related_name='id_option_2_modification')
    model_m = models.ForeignKey(ModelModification, on_delete=models.CASCADE)
    already_find_winner = models.BooleanField(default=False)
    is_not_comparable = models.BooleanField(default=False)
    flag_winner_option = models.IntegerField(default=-1)
    flag_not_compared = models.BooleanField(default=True)   # Данные не сравнивались ни разу
    in_result_and_not_comparable = models.BooleanField(default=False)
    quasi_level = models.PositiveIntegerField(default=0)

    def __str__(self):
        try:
            return f'{str(self.option_1)} {str(self.option_2)} Победитель: {str(self.flag_winner_option)}'
        except:
            return f'{str(self.option_1)} {str(self.option_2)}'
