from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class SettingsPACOM(models.Model):
    auto_mode = models.BooleanField(default=False)
    larichev_question = models.BooleanField(default=True)

    def create(cls, request):
        if request.POST['mode'] == 'Классический':
            return cls()
        elif request.POST['mode'] == 'Только различные значения критериев':
            return cls(larichev_question=False)
        else:
            return cls(auto_mode=True)


# Модель ситуации поиска лучшей альтернативы
class Model(models.Model):
    is_demo = models.BooleanField()
    name = models.CharField(max_length=255)
    id_winner_option_many = models.IntegerField(null=True)  # id победителя по многокриетриальному методу

    # SNOD
    id_winner_option_shnur = models.IntegerField(null=True)  # id победителя по методу ШНУР
    time_shnur = models.CharField(max_length=255)
    time_answer_shnur = models.CharField(max_length=255)
    time_many = models.CharField(max_length=255)

    # PACOM
    already_find_winner_PACOM = models.BooleanField(default=False)  # id победителя по методу ПАРК
    time_answer_pacom = models.CharField(max_length=255)
    number_of_questions_pacom = models.IntegerField(default=0)
    number_of_pairs = models.IntegerField(default=0)
    number_of_incomparable = models.IntegerField(default=0)
    id_settings_pacom = models.OneToOneField(SettingsPACOM, null=True, on_delete=models.CASCADE)

    id_user = models.ForeignKey(User, on_delete=models.CASCADE)


# Модель критерием
class Criterion(models.Model):
    number = models.IntegerField()   # Порядковый номер критерия
    name = models.CharField(max_length=200)
    direction = models.BooleanField()  # max (True) or min (False)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    max = models.FloatField(blank=True)

    def __str__(self):
        return self.name


# Модель альтернатив
class Option(models.Model):
    name = models.CharField(max_length=200)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    number = models.IntegerField()
    quasi_order_pacom = models.IntegerField(default=0)

    def __str__(self):
        return self.name


# Значение варианта у критерия
class Value(models.Model):
    value = models.FloatField()
    id_option = models.ForeignKey(Option, on_delete=models.CASCADE)
    id_criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.value)


# Пары вариантов и результаты их сравнения по методу ШНУР
class PairsOfOptions(models.Model):
    id_option_1 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_option_1')
    id_option_2 = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='id_option_2')
    winner_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='winner_option', blank=True,
                                      null=True)
    winner_option_many = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='winner_option_many',
                                           blank=True,
                                           null=True)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id_option_1) + '' + str(self.id_option_2)


# Хранятся ответы на вопросы к ЛПР по методу ШНУР
class HistoryAnswer(models.Model):
    question = models.TextField(max_length=1000)
    answer = models.CharField(max_length=255)
    pair = models.ForeignKey(PairsOfOptions, on_delete=models.CASCADE, related_name='pair')
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)


# Пары вариантов и результаты их сравнения по методу ПАРК
class PairsOfOptionsPARK(models.Model):
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

    def __str__(self):
        return str(self.id_option_1) + '' + str(self.id_option_2)


# Ранжирование вариантов
class RangeValue(models.Model):
    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    value = models.IntegerField(null=True)

    def __str__(self):
        return 'Альтернатива: ' + self.option.name + ' РАНГ: ' + str(self.value)


# Идеальная альтернатива для пары альтернатив
class PerfectAlternativePARK(models.Model):
    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.pair.id)


# Значения идеальной альтернативы
class ValueOfPerfectAlternativePARK(models.Model):
    value = models.IntegerField(null=True)
    criteria = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    perfect_alternative = models.ForeignKey(PerfectAlternativePARK, on_delete=models.CASCADE)


# Хранятся ответы на вопросы к ЛПР по методу ПАРК
class HistoryAnswerPACOM(models.Model):
    question = models.TextField(max_length=1000)
    answer = models.CharField(max_length=255)
    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE, related_name='pair_pacom')
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
