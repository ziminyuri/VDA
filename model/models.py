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




class SettingsOrigianlSNOD(models.Model):
    auto_mode = models.BooleanField(default=False)

    def create(cls, request):
        if request.POST['mode'] == 'Классический':
            return cls()
        else:
            return cls(auto_mode=True)


class Model(models.Model):
    """ Модель ситуации поиска лучшей альтернативы """
    is_demo = models.BooleanField()
    name = models.CharField(max_length=255)
    id_winner_option_many = models.IntegerField(null=True)  # id победителя по многокриетриальному методу

    """ SNOD """
    id_winner_option_shnur = models.IntegerField(null=True)  # id победителя по методу ШНУР
    time_shnur = models.CharField(max_length=255)
    time_answer_shnur = models.CharField(max_length=255)
    time_many = models.CharField(max_length=255)

    """ PACOM """
    already_find_winner_PACOM = models.BooleanField(default=False)
    time_answer_pacom = models.CharField(max_length=255)
    number_of_questions_pacom = models.IntegerField(default=0)
    number_of_pairs = models.IntegerField(default=0)
    number_of_incomparable = models.IntegerField(default=0)
    id_settings_pacom = models.OneToOneField(SettingsPACOM, null=True, on_delete=models.CASCADE)

    """ True SNOD """
    already_find_winner_SNOD = models.BooleanField(default=False)
    time_answer_snod = models.CharField(max_length=255)
    number_of_questions_snod = models.IntegerField(default=0)
    number_of_pairs_snod = models.IntegerField(default=0)
    number_of_incomparable_snod = models.IntegerField(default=0)
    number_repeated_questions_snod = models.PositiveIntegerField(default=0)   # Кол-во вопросов которые повторились
    id_settings_original_snod = models.OneToOneField(SettingsOrigianlSNOD, null=True, on_delete=models.CASCADE)

    id_user = models.ForeignKey(User, on_delete=models.CASCADE)


class Criterion(models.Model):
    """ Модель критерием """

    number = models.IntegerField()   # Порядковый номер критерия
    name = models.CharField(max_length=200)
    direction = models.BooleanField()  # max (True) or min (False)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    max = models.FloatField(blank=True)

    def __str__(self):
        return self.name


class Option(models.Model):
    """ Модель альтернатив """
    name = models.CharField(max_length=200)
    id_model = models.ForeignKey(Model, on_delete=models.CASCADE)
    number = models.IntegerField()
    quasi_order_pacom = models.IntegerField(default=0)
    quasi_order_original_snod = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Value(models.Model):
    """ Значение варианта у критерия """
    value = models.FloatField()
    id_option = models.ForeignKey(Option, on_delete=models.CASCADE)
    id_criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.value)
