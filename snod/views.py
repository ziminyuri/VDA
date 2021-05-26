import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.generic import View

from model.models import Model, Option

from services.history import checking_already_has_answer
from services.model import get_model_data
from services.pairs_of_options import (absolute_value_in_str, data_of_winners,
                                       make_question, write_answer)
from services.settings import settingsOrigianlSnodCreate
from services.snod_original import (get_context_history_answer_original_snod,
                                    get_original_snod_question,
                                    get_winners_from_model_original_snod,
                                    write_original_snod_answer)
from VDA.settings import MEDIA_ROOT, DEPLOY

from .models import HistoryAnswer, PairsOfOptions, PairsOfOptionsTrueSNOD
from .services.search import snod_search_auto
from .services.modification import check_comparable_in_result


class SnodSearchView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        model = Model.objects.get(id=id)
        message = make_question(model)
        return render(request, "snod/question.html",
                      {'message': message,
                       'model': model, 'origianl_snod': 0})

    @staticmethod
    def post(request, id):

        answer = request.POST["answer"]
        message = write_answer(request, answer)

        """Проверяем, что нашли лучшую альтернативу в модели"""
        flag_find_winner = message['flag_find_winner']
        if flag_find_winner == 0:
            model = Model.objects.get(id=id)
            return render(request, "snod/question.html",
                          {'message': message,
                           'model': model, 'origianl_snod': 0})
        else:
            return render(request, "snod/result.html",
                          {})


class SnodDetailView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, id):
        model = Model.objects.get(id=id)
        option_shnur = Option.objects.get(id=model.id_winner_option_shnur)
        option_many = Option.objects.get(id=model.id_winner_option_many)

        """ История ответов """
        history_answers = HistoryAnswer.objects.filter(id_model=model)
        answers = []
        for answer_history in history_answers:
            answers.append({'question': answer_history.question, 'answer': answer_history.answer,
                            'pair': answer_history.pair.id_option_1.name + ' и ' + answer_history.pair.id_option_2.name})

        pairs = PairsOfOptions.objects.filter(id_model=id)
        img = []

        for pair in pairs:
            absolute_value = absolute_value_in_str(model.id, pair.id)
            if 'DATABASE_URL' in os.environ:
                img.append({'pair': pair.id_option_1.name + ' и ' + pair.id_option_2.name,
                            'path': MEDIA_ROOT + str(model.id) + '/' + str(pair.id) + '.png',
                            'absolute_value': absolute_value})

            else:
                img.append({'pair': pair.id_option_1.name + ' и ' + pair.id_option_2.name,
                            'path': 'http://127.0.0.1:8000/media/' + str(model.id) + '/' + str(pair.id) + '.png',
                            'absolute_value': absolute_value})

        model_data, model_header = get_model_data(model.id)
        winners_data, winners_header = data_of_winners(model.id)

        response = {'option_shnur': option_shnur.name, 'option_many': option_many.name, 'history': answers, 'img': img,
                    'time_shnur_elapsed': model.time_shnur, 'time_answer_elapsed': model.time_answer_shnur,
                    'time_many_elapsed': model.time_many, 'model_data': model_data, 'model_header': model_header,
                    'winners_data': winners_data, 'winners_header': winners_header}

        return render(request, "snod/result.html",
                      response)


class SettingsOriginalSnodCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        context = {'model': get_object_or_404(Model, id=id), 'mode': ['Классический', 'Автоматический']}
        return render(request, "snod/settings_original_snod.html", context)

    def post(self, request, id, **kwargs):
        settings = settingsOrigianlSnodCreate(request)
        Model.objects.filter(id=id).update(id_settings_original_snod=settings)
        return redirect('snod_original_search', id=id)


class OriginalSnodSearchView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, id):
        model = Model.objects.get(id=id)

        if model.id_settings_original_snod is None:
            return redirect('snod_original_settings_create', id=id)

        if model.id_settings_original_snod.auto_mode is True:
            return self.post(request, id)

        message = get_original_snod_question(model)
        return render(request, "snod/question.html",
                      {'message': message,
                       'model': model, 'original_snod': 1})

    def post(self, request, id):
        model = Model.objects.get(id=id)

        flag_find_winner = 0
        message = get_original_snod_question(model)

        if flag_find_winner == 0 and model.id_settings_original_snod.auto_mode is True:
            Model.objects.filter(id=id).update(is_searching_snod=True)
            snod_search_auto.delay(message)
            return redirect('models')

        if model.id_settings_original_snod.auto_mode is False:
            message = write_original_snod_answer(request.POST["answer"], auto=False, request=request)

        """Проверяем, что нашли лучшую альтернативу в модели"""
        flag_find_winner = message['flag_find_winner']

        if flag_find_winner == 1:
            return redirect('snod_original_result', id=id)

        else:
            message, flag_checking = checking_already_has_answer(message, snod_original=True, request=request)
            while flag_checking:
                flag_find_winner = message['flag_find_winner']
                if flag_find_winner != 1:
                    message, flag_checking = checking_already_has_answer(message, snod_original=True, request=request)

            return render(request, "snod/question.html",
                          {'message': message,
                           'model': model, 'original_snod': 1})


class OriginalSnodDetailView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, id):
        model = Model.objects.get(id=id)
        context = {'response': get_winners_from_model_original_snod(id),
                   'history': get_context_history_answer_original_snod(id),
                   'can_improve_result': check_comparable_in_result(id),
                   'model': model}

        data_from_model = get_model_data(id)
        context['model_data'] = data_from_model[0]
        context['model_header'] = data_from_model[1]

        if DEPLOY:
            context['graph'] = f'{MEDIA_URL}{model.graph_snod}'
            graph_example = [f'{MEDIA_URL}graph/example/1.png',
                             f'{MEDIA_URL}graph/example/2.png',
                             f'{MEDIA_URL}graph/example/3.png']

        else:
            context['graph'] = f'http://127.0.0.1:8000/media{model.graph_snod}'

            graph_example = ['http://127.0.0.1:8000/media/graph/example/1.png',
                             'http://127.0.0.1:8000/media/graph/example/2.png',
                             'http://127.0.0.1:8000/media/graph/example/3.png']

        context['graph_example'] = graph_example

        return render(request, "snod/original_snod_result.html", {'context': context})




