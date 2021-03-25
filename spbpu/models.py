from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfile(models.Model):
    # Модель пользователя расширяет стандартную модель пользователя Django

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.username


class SettingsPACOM(models.Model):
    auto_mode = models.BooleanField(default=False)
    larichev_question = models.BooleanField(default=True)

    def create(cls, **kwargs):
        if kwargs.get('larichev') == 'on':
            return cls()
        elif kwargs.get('custom_question') == 'on':
            return cls(larichev_question=False)
        else:
            return cls(auto_mode=True)


class Model(models.Model):
    # Модель ситуации поиска лучшей альтернативы

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




class Criterion(models.Model):
    # Модель критерием

    number = models.IntegerField()   # Порядковый номер критерия
    name = models.CharField(max_length=200)
    direction = models.BooleanField()  # max (True) or min (False)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    max = models.FloatField()

    def __str__(self):
        return self.name


class Option(models.Model):
    # Модель альтернатив

    name = models.CharField(max_length=200)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    number = models.IntegerField()
    quasi_order_pacom = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Value(models.Model):
    # Значение варианта у критерия

    value = models.FloatField()
    id_option = models.ForeignKey(Option, on_delete=models.CASCADE)
    id_criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.value)


class PairsOfOptions(models.Model):
    # Пары вариантов и результаты их сравнения по методу ШНУР

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


class HistoryAnswer(models.Model):
    # Хранятся ответы на вопросы к ЛПР по методу ШНУР

    question = models.TextField(max_length=1000)
    answer = models.CharField(max_length=255)
    pair = models.ForeignKey(PairsOfOptions, on_delete=models.CASCADE, related_name='pair')
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)


class PairsOfOptionsPARK(models.Model):
    # Пары вариантов и результаты их сравнения по методу ПАРК

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


class RangeValue(models.Model):
    # Ранжирование вариантов

    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    value = models.IntegerField(null=True)

    def __str__(self):
        return 'Альтернатива: ' + self.option.name + ' РАНГ: ' + str(self.value)


class PerfectAlternativePARK(models.Model):
    # Идеальная альтернатива для пары альтернатив

    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.pair.id)


class ValueOfPerfectAlternativePARK(models.Model):
    # Значения идеальной альтернативы

    value = models.IntegerField(null=True)
    criteria = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    perfect_alternative = models.ForeignKey(PerfectAlternativePARK, on_delete=models.CASCADE)


class HistoryAnswerPACOM(models.Model):
    # Хранятся ответы на вопросы к ЛПР по методу ПАРК

    question = models.TextField(max_length=1000)
    answer = models.CharField(max_length=255)
    pair = models.ForeignKey(PairsOfOptionsPARK, on_delete=models.CASCADE, related_name='pair_pacom')
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
