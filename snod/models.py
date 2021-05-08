from django.db import models
from model.models import Option, Model



class PairsOfOptions(models.Model):
    """ Пары вариантов и результаты их сравнения по методу ШНУР """

    id_option_1 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_option_1')
    id_option_2 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_option_2')
    winner_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='winner_option', blank=True,
                                      null=True)
    winner_option_many = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='winner_option_many',
                                           blank=True,
                                           null=True)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)

    def __str__(self):
        return f'{str(self.id_option_1)} {str(self.id_option_2)}'


class HistoryAnswer(models.Model):
    """ Хранятся ответы на вопросы к ЛПР по методу ШНУР """

    question = models.TextField(max_length=1000)
    answer = models.CharField(max_length=255)
    pair = models.ForeignKey(PairsOfOptions, on_delete=models.CASCADE, related_name='pair')
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)


class PairsOfOptionsTrueSNOD(models.Model):
    """ Пары вариантов и результаты их сравнения по оригинальному методу ШНУР """

    id_option_1 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_option_1_true_snod')
    id_option_2 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_option_2_true_snod')
    winner_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='winner_option_true_snod', blank=True,
                                      null=True)

    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    already_find_winner = models.BooleanField(default=False)
    is_not_comparable = models.BooleanField(default=False)
    flag_winner_option = models.IntegerField(default=-1)
    flag_not_compared = models.BooleanField(default=True)   # Данные не сравнивались ни разу

    def __str__(self):
        return f'{str(self.id_option_1)} {str(self.id_option_2)}'


class HistoryAnswerTrueSNOD(models.Model):
    """ Хранятся ответы на вопросы к ЛПР по ориганльному методу ШНУР """

    question = models.TextField(max_length=1000)
    answer = models.CharField(max_length=255)
    pair = models.ForeignKey(PairsOfOptionsTrueSNOD, on_delete=models.CASCADE, related_name='pair_true_snod')
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
