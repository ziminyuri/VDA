from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.contrib.auth.models import User
from django.db.models import Count

from services.statistics import get_table_context, built_statistics, \
    built_statistics_number_question, get_statistics_pacom_v1, get_statistics_original_snod_v1, \
    get_statistics_question_pacom


class StatisticsView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        try:
            """Доля сравнимых альтернатив по ПАРК"""
            x_pacom, y_pacom = get_statistics_pacom_v1()
            path_img = built_statistics(x_pacom, y_pacom, x_label='Кол-во альтернатив', y_label='Кол-во пар сравнений', normalisation=False)
            context_table_pacom = get_table_context(x_pacom, y_pacom)

            """Кол-во вопросов по ПАРК"""
            x_pacom, y_pacom = get_statistics_question_pacom()
            path_img_number_pacom = built_statistics(x_pacom, y_pacom, x_label='Кол-во альтернатив', y_label='Кол-во вопросов к ЛПР',
                                        normalisation=False)

            x_snod, y_snod = get_statistics_original_snod_v1()
            path_img_snod = built_statistics(x_snod, y_snod, x_label='Кол-во альтернатив', y_label='Кол-во пар сравнений', normalisation=False)
            context_table_snod = get_table_context(x_snod, y_snod)
            error = False

            number_of_alternatives, number_of_question, number_of_repeted_question, path_img_snod_number_question, \
            path_img_snod_number_of_repeted_question = built_statistics_number_question(
                request)
            context_table_snod_number_of_question = get_table_context(number_of_repeted_question, number_of_question,
                                                                      number_of_alternatives)

        except Exception as e:
            path_img = None
            path_img_snod = None
            context_table_snod = None
            context_table_pacom = None
            error = True
            path_img_snod_number_question = None
            path_img_snod_number_of_repeted_question = None
            context_table_snod_number_of_question = None
            path_img_number_pacom = None

        return render(request, "administration/statistics.html", {'path_img': path_img,
                                                                  'path_img_number_pacom': path_img_number_pacom,
                                                                  'path_img_snod': path_img_snod,
                                                                  'path_img_snod_number_question': path_img_snod_number_question,
                                                                  'path_img_snod_number_of_repeted_question': path_img_snod_number_of_repeted_question,
                                                                  'context_table_pacom': context_table_pacom,
                                                                  'context_table_snod_number_of_question': context_table_snod_number_of_question,
                                                                  'context_table_snod': context_table_snod,
                                                                  'error': error})


class UserListView(View):
    def get(self, request):
        """Список всех пользователей"""
        users = User.objects.all().annotate(numbers_model=Count('user_model')).order_by('id')
        return render(request, "administration/index.html", {'users': users})


class SettingsDetailView(View):
    def get(self, request):
        """Настройки системы"""
        return render(request, "administration/settings.html", {})
