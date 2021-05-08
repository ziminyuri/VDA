from django.shortcuts import redirect, render, get_object_or_404

from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from model.models import Model
from services.model import get_model_data
from services.park import (auto_mode_pacom, get_context_history_answer,
                           get_park_question, get_winners_from_model,
                           write_range_data, write_result_of_compare_pacom)
from services.settings import settingsPACOMCreate
from services.graph import get_graph_pacom
import os


class ParkSearchView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, id):
        model = Model.objects.get(id=id)
        if model.id_settings_pacom is None:
            return redirect('pacom_settings_create', id=id)

        response = get_park_question(model)
        if response['flag_range'] is False and model.id_settings_pacom.auto_mode is True:
            auto_mode_pacom(response, request, model)
            return redirect('park_result', pk=model.id)

        elif response['flag_range'] is False:
            return render(request, "spbpu/../templates/pacom/range.html", {'response': response, 'model': model})

        else:
            return render(request, 'spbpu/../templates/pacom/compare_alternative.html', {'response': response, 'model': model})

    def post(self, request, id):
        model = Model.objects.get(id=id)
        try:
            """ Флаги после ранжирование """
            range = bool(int(request.POST["range"]))

        except:
            """ Флаги после сравнения критериев"""
            range = bool(request.POST["range"])

        compare = bool(int(request.POST["compare"]))

        if range is True and compare is False:
            """Запись данных после ранжирования"""

            response = write_range_data(request, model)  # TODO Проверить что нет ошибок ранжирования
            response = get_park_question(model)

            return render(request, 'spbpu/../templates/pacom/compare_alternative.html', {'response': response, 'model': model})

        if compare is True:
            """ Запись после сравнения критериев """
            write_result_of_compare_pacom(request, model)
            response = get_park_question(model)

            if response['flag_find_winner'] is True:
                return redirect('park_result', pk=model.id)

            elif response['flag_range'] is False:
                return render(request, "spbpu/../templates/pacom/range.html", {'response': response, 'model': model})
            else:
                return render(request, 'spbpu/../templates/pacom/compare_alternative.html', {'response': response, 'model': model})


class SettingsPACOMCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        context = {'model': get_object_or_404(Model, id=id)}
        context['mode'] = ['Классический', 'Только различные значения критериев', 'Автоматический']
        return render(request, "spbpu/../templates/pacom/settings.html", context)

    def post(self, request, id, **kwargs):
        settings = settingsPACOMCreate(request)
        Model.objects.filter(id=id).update(id_settings_pacom=settings)
        return redirect('park_search', id=id)


class ParkDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login'

    model = Model
    template_name = 'spbpu/../templates/pacom/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response'] = get_winners_from_model(self.kwargs['pk'])
        context['model_data'], context['model_header'] = get_model_data(self.kwargs['pk'])
        context['history'] = get_context_history_answer(self.kwargs['pk'])

        if 'DATABASE_URL' in os.environ:
            context['graph'] = get_graph_pacom(self.kwargs['pk'])

        else:
            context['graph'] = 'http://127.0.0.1:8000/media' + get_graph_pacom(self.kwargs['pk'])

        return context
