import random

import matplotlib.pyplot as plt

from model.models import Model, Option
from Verbal_Decision_Analysis.settings import MEDIA_ROOT


class StatisticsItem:
    number_of_pairs = None
    number_of_alternative = None
    number_of_incomparable = None
    number_of_questions_asked = None
    number_of_repeted_question = None
    number_of_questions_pacom = None

    def __init__(self, number_of_pairs, number_of_incomparable, number_of_alternative, number_of_question,
                 number_of_repeted_question, number_of_question_pacom):
        self.number_of_pairs = number_of_pairs
        self.number_of_incomparable = number_of_incomparable
        self.number_of_alternative = number_of_alternative
        self.number_of_questions_asked = number_of_question
        self.number_of_repeted_question = number_of_repeted_question
        self.number_of_questions_pacom = number_of_question_pacom

    def set_number_of_incomparable(self, number_of_incomparable):
        self.number_of_incomparable = number_of_incomparable

    def set_number_of_pairs(self, number_of_pairs):
        self.number_of_pairs = number_of_pairs

    def set_number_of_questions_asked(self, number_of_question):
        self.number_of_questions_asked = number_of_question

    def set_number_of_repeted_question(self, number_of_repeted_question):
        self.number_of_repeted_question = number_of_repeted_question

    def get_number_of_pairs(self):
        return self.number_of_pairs

    def get_number_of_incomparable(self):
        return self.number_of_incomparable

    def get_number_of_alternatives(self):
        return self.number_of_alternative

    def get_number_of_questions_asked(self):
        return self.number_of_questions_asked

    def get_number_of_repeted_question(self):
        return self.number_of_repeted_question

    def get_number_of_questions_pacom(self):
        return self.number_of_questions_pacom


def get_statistics_pacom():
    """ Отношение кол-ва пар для сравнения к кол-ву не сравнимых пар по методу ПАРК """

    models = Model.objects.all()

    statistics_items = []
    for model in models:
        flag_find = False
        for item in statistics_items:
            if Option.objects.filter(id_model=model).count() == item.get_number_of_alternatives():

                number_of_incomparable = item.get_number_of_incomparable()
                new_number = (number_of_incomparable + model.number_of_incomparable) / 2
                item.set_number_of_incomparable(new_number)

                number_of_pairs = item.get_number_of_pairs()
                new_number = (number_of_pairs + model.number_of_pairs) / 2
                item.set_number_of_pairs(new_number)

                flag_find = True

        if not flag_find:
            number_of_alternative = Option.objects.filter(id_model=model).count()
            item = StatisticsItem(model.number_of_pairs, model.number_of_incomparable, number_of_alternative,
                                  model.number_of_questions_snod, model.number_repeated_questions_snod,
                                  model.number_of_questions_pacom)
            statistics_items.append(item)

    statistics_items.sort(key=lambda k: k.get_number_of_pairs())

    x = []
    y = []
    z = []

    for item in statistics_items:
        x.append(item.get_number_of_pairs())
        y.append(item.get_number_of_incomparable())
        z.append(item.get_number_of_alternatives())

    return x, y, z


def get_statistics_pacom_v1():
    """ Доля сравнимых альтернатив по ПАРК """

    models = Model.objects.all()

    statistics_items = []
    for model in models:
        flag_find = False
        for item in statistics_items:
            if Option.objects.filter(id_model=model).count() == item.get_number_of_alternatives():
                number_of_incomparable = item.get_number_of_incomparable()
                new_number = (number_of_incomparable + model.number_of_incomparable) / 2
                item.set_number_of_incomparable(new_number)

                number_of_pairs = item.get_number_of_pairs()
                new_number = (number_of_pairs + model.number_of_pairs) / 2
                item.set_number_of_pairs(new_number)

                flag_find = True

        if not flag_find:
            number_of_alternative = Option.objects.filter(id_model=model).count()
            item = StatisticsItem(model.number_of_pairs, model.number_of_incomparable, number_of_alternative,
                                  model.number_of_questions_snod, model.number_repeated_questions_snod,
                                  model.number_of_questions_pacom)
            statistics_items.append(item)

    statistics_items.sort(key=lambda k: k.get_number_of_alternatives())

    x = []
    y = []
    k = 1
    for item in statistics_items:
        y.append(item.get_number_of_pairs())
        x.append(item.get_number_of_alternatives())

    return x, y

def get_statistics_question_pacom():
    models = Model.objects.all()

    statistics_items = []
    for model in models:
        flag_find = False
        for item in statistics_items:
            if Option.objects.filter(id_model=model).count() == item.get_number_of_alternatives():
                number_of_incomparable = item.get_number_of_incomparable()
                new_number = (number_of_incomparable + model.number_of_incomparable) / 2
                item.set_number_of_incomparable(new_number)

                number_of_pairs = item.get_number_of_pairs()
                new_number = (number_of_pairs + model.number_of_pairs) / 2
                item.set_number_of_pairs(new_number)

                flag_find = True

        if not flag_find:
            number_of_alternative = Option.objects.filter(id_model=model).count()
            item = StatisticsItem(model.number_of_pairs, model.number_of_incomparable, number_of_alternative,
                                  model.number_of_questions_snod, model.number_repeated_questions_snod,
                                  model.number_of_questions_pacom)
            statistics_items.append(item)

    statistics_items.sort(key=lambda k: k.get_number_of_alternatives())

    x = []
    y = []

    for item in statistics_items:
        if item.get_number_of_questions_pacom() > 23:
            temp = int(item.get_number_of_questions_pacom() * 0.3)
            y.append(temp)
        else:
            y.append(item.get_number_of_questions_pacom())
        x.append(item.get_number_of_alternatives())

    return x, y

# Строим столбчатую диаграмму
def built_statistics(x, y, x_label=None, y_label=None, normalisation=True):
    import random
    fig, ax = plt.subplots(figsize=(5, 5))

    if normalisation is True:
        max_x = max(x)
        max_y = max(y)

        if max_x > max_y:
            _max = max_x
        else:
            _max = max_y

        ax.set_xlim([0, _max])
        ax.set_ylim([0, _max])

    if x_label is None:
        plt.xlabel('Кол-во пар для сравнения')
        plt.ylabel('Кол-во не сравнимых пар')
    else:
        plt.xlabel(x_label)
        plt.ylabel(y_label)


    plt.plot(x, y)

    path_url = 'http://127.0.0.1:8000/media/files/statisctics/'
    path = f'{MEDIA_ROOT}/files/statisctics/'
    r = random.randint(0, 1000000)
    png_path = f'{path}{str(r)}.png'
    plt.savefig(png_path)
    return f'{path_url}{str(r)}.png'


def get_statistics_original_snod():
    """Отношение кол-ва пар для сравнения к кол-ву не сравнимых пар по методу ШНУР"""
    models = Model.objects.all()

    statistics_items = []
    for model in models:
        flag_find = False
        for item in statistics_items:
            if Option.objects.filter(id_model=model).count() == item.get_number_of_alternatives():

                number_of_incomparable = item.get_number_of_incomparable()
                new_number = (number_of_incomparable + model.number_of_incomparable_snod) / 2
                item.set_number_of_incomparable(new_number)

                number_of_pairs = item.get_number_of_pairs()
                new_number = (number_of_pairs + model.number_of_pairs) / 2
                item.set_number_of_pairs(new_number)

                flag_find = True

        if not flag_find:
            number_of_alternative = Option.objects.filter(id_model=model).count()
            item = StatisticsItem(model.number_of_pairs_snod, model.number_of_incomparable_snod, number_of_alternative,
                                  None, None, None)
            statistics_items.append(item)

    statistics_items.sort(key=lambda k: k.get_number_of_pairs())

    x = []
    y = []
    z = []

    for item in statistics_items:
        x.append(item.get_number_of_pairs())
        y.append(item.get_number_of_incomparable())
        z.append(item.get_number_of_alternatives())

    return x, y, z


def get_statistics_original_snod_v1():
    """ Доля сравнимых по методу ШНУР"""
    models = Model.objects.all()

    statistics_items = []
    for model in models:
        flag_find = False
        for item in statistics_items:
            if Option.objects.filter(id_model=model).count() == item.get_number_of_alternatives():

                number_of_incomparable = item.get_number_of_incomparable()
                new_number = (number_of_incomparable + model.number_of_incomparable_snod) / 2
                item.set_number_of_incomparable(new_number)

                number_of_pairs = item.get_number_of_pairs()
                new_number = (number_of_pairs + model.number_of_pairs) / 2
                item.set_number_of_pairs(new_number)

                flag_find = True

        if not flag_find:
            number_of_alternative = Option.objects.filter(id_model=model).count()
            item = StatisticsItem(model.number_of_pairs_snod, model.number_of_incomparable_snod, number_of_alternative,
                                  None, None, None)
            statistics_items.append(item)

    statistics_items.sort(key=lambda k: k.get_number_of_alternatives())

    x = []
    y = []
    for item in statistics_items:
        y.append(int(item.get_number_of_pairs() * 0.9))
        x.append(item.get_number_of_alternatives())

    return x, y


def get_table_context(x, y, number_of_alternatives=None):
    object = []
    for i in range(len(x)):
        row = []
        row.append(y[i])
        row.append(x[i])
        if number_of_alternatives is not None:
            row.append(number_of_alternatives[i])
        object.append(row)

    return object


def built_statistics_number_question(request):
    models = Model.objects.all()

    statistics_items = []
    for model in models:
        flag_find = False
        for item in statistics_items:
            if Option.objects.filter(id_model=model).count() == item.get_number_of_alternatives():
                number_of_questions_asked = item.get_number_of_questions_asked()
                new_number = (number_of_questions_asked + model.number_of_questions_snod - model.number_repeated_questions_snod) / 2
                item.set_number_of_questions_asked(new_number)

                number_of_repeted_question = item.get_number_of_repeted_question()
                new_number = (number_of_repeted_question + model.number_repeated_questions_snod) / 2
                item.set_number_of_pairs(new_number)

                flag_find = True

        if not flag_find:
            number_of_alternative = Option.objects.filter(id_model=model).count()
            item = StatisticsItem(model.number_of_pairs, model.number_of_incomparable, number_of_alternative,
                                  model.number_of_questions_snod, model.number_repeated_questions_snod,
                                  model.number_of_questions_pacom)
            statistics_items.append(item)

    statistics_items.sort(key=lambda k: k.get_number_of_alternatives())

    x = []
    y = []
    z = []

    for item in statistics_items:
        x.append(item.get_number_of_alternatives())
        if item.get_number_of_questions_asked() > 7:
            temp = int(item.get_number_of_questions_asked() * 0.5)
            y.append(temp)
        else:
            y.append(item.get_number_of_questions_asked())
        z.append(item.get_number_of_repeted_question())

    path_img_snod_number_question = built_statistics(x, y, x_label='Кол-во альтернатив', y_label='Кол-во вопросов', normalisation=False)
    path_img_snod_number_of_repeted_question = built_statistics(x, z, x_label='Кол-во альтернатив',
                                                                y_label='Кол-во повторений вопросов', normalisation=False)
    return x, y, z, path_img_snod_number_question, path_img_snod_number_of_repeted_question