from django.db import models

from model.models import Criterion, Model, Option


class PairsOfOptionsPARK(models.Model):
    """ Пары вариантов и результаты их сравнения по методу ПАРК """

    id_option_1 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_park_option_1')
    id_option_2 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_park_option_2')

    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    already_range = models.BooleanField(default=False)
    already_find_winner = models.BooleanField(default=False)
    is_not_comparable = models.BooleanField(default=False)
    init_file = models.BooleanField(default=False)
    compensable_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='park_compensable_option', blank=True,
                                      null=True)
    flag_winner_option = models.IntegerField(default=-1)    # Победитель option_1 = 1, option_2 = 2, option_1=option_2: 0
                                                            # Не сравнимы 3
    quasi_level = models.PositiveIntegerField()

    def __str__(self):
        return str(self.id_option_1) + '' + str(self.id_option_2)


class RangeValue(models.Model):
    """ Ранжирование вариантов """

    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    value = models.IntegerField(null=True)

    def __str__(self):
        return f'Альтернатива: {self.option.name}  РАНГ: {str(self.value)}'


class PerfectAlternativePARK(models.Model):
    """ Идеальная альтернатива для пары альтернатив """

    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.pair.id)


class ValueOfPerfectAlternativePARK(models.Model):
    """ Значения идеальной альтернативы """

    value = models.IntegerField(null=True)
    criteria = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    perfect_alternative = models.ForeignKey(PerfectAlternativePARK, on_delete=models.CASCADE)


class HistoryAnswerPACOM(models.Model):
    """ Хранятся ответы на вопросы к ЛПР по методу ПАРК """

    question = models.TextField(max_length=1000)
    answer = models.CharField(max_length=255)
    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE, related_name='pair_pacom')
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
