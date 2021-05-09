import os
from random import randint

from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import View

from services.model import create_model, get_model_data
from services.pairs_of_options import create_files
from services.services import get_userprofile
from services.statistics import (built_statistics,
                                 built_statistics_number_question,
                                 get_statistics, get_statistics_original_snod,
                                 get_table_context)
from snod.views import CacheMixin
from Verbal_Decision_Analysis.celery import app
from Verbal_Decision_Analysis.settings import MEDIA_ROOT

from .models import Model


class LoginView(View):
    """ Aвторизация """

    def get(self, request):

        return render(request, "auth.html", {"login_error": ''})

    def post(self, request):
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("index")

        else:
            login_error = "Неверный логин или пароль! Повторите попытку."
            return render(request, "auth.html", {"login_error": login_error})


class RegistrationView(View):
    """ Регистрация """

    def get(self, request):
        return render(request, "registration.html", {'error': None})

    def post(self, request):
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        password_2 = request.POST.get("password_2")

        if password != password_2:
            error = 'Пароли не совпадают'
            return render(request, "registration.html", {'error': error})

        user = User.objects.filter(username=email)
        if not user:
            User.objects.create_user(email, email, password)
            auth.authenticate(username=email, password=password)
            return redirect('login')
        else:
            error = 'Пользователь с таким e-mail существует'
            return render(request, "registration.html", {'error': error})


class LogoutView(View):
    """ Выход из системы """

    def get(self, request):
        django_logout(request)
        return redirect("login")


class IndexView(LoginRequiredMixin, CacheMixin, View):
    login_url = 'login'

    def get(self, request):
        return render(request, "index.html", {})


class DemoModelCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        return render(request, "model/demo_choice_number.html", {})

    def post(self, request):
        user_profile = get_userprofile(request)
        number_of_alternatives = int(request.POST['number'])
        create_model.delay(user_profile.id, demo_model=True, number_of_alternatives=number_of_alternatives)
        return redirect('models')


class UploadView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        r_int = str(randint(0, 100))
        path_csv = request.user.username + '/' + r_int + uploaded_file.name
        fs.save(path_csv, uploaded_file)
        model = create_model(demo_model=False, path_csv=path_csv, request=request)
        if model is False:
            error = 'Возникла ошибка при загрузке файла. Проверьте файл'
            return render(request, "upload_model.html", {'error': error})
        create_files(model)
        return redirect('models_id', id=model.id)

    def get(self, request):
        return render(request, "upload_model.html", {})


class DownloadCSVView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        file_path = 'media/demo/demo.csv'
        data = open(file_path, "rb").read()
        response = HttpResponse(data, content_type='application;')
        response['Content-Length'] = os.path.getsize(file_path)
        response['Content-Disposition'] = 'attachment; filename=%s' % 'demo.csv'

        return response


class ModelCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        number_for_select = list(range(1, 11))
        return render(request, "model/choice_number.html", {'number_for_select': number_for_select})

    def post(self, request):
        """ Данные для заполнения таблицы """

        number_of_criterion = request.POST["number_of_criterion"]
        number_of_alternatives = request.POST["number_of_alternatives"]
        number_of_criterion = int(number_of_criterion)
        number_of_alternatives = int(number_of_alternatives)
        number_of_criterion_for_select = list(range(1, number_of_criterion + 1))
        number_of_alternatives_for_select = list(range(1, number_of_alternatives + 1))
        return render(request, "model/input_data.html",
                      {'number_of_criterion_for_select': number_of_criterion_for_select,
                       'number_of_alternatives_for_select': number_of_alternatives_for_select,
                       'number_of_criterion': number_of_criterion,
                       'number_of_alternatives': number_of_alternatives,
                       'error': None})


class ModelListCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request):
        user = get_userprofile(request)
        models = Model.objects.filter(id_user=user).order_by('id')
        return render(request, "model/models.html", {'models': models})

    @staticmethod
    def post(request):
        """ Cоздание модели после ввода данных в таблице """

        response = create_model(demo_model=False, request=request)

        if response is not False:
            create_files(response)  # В response находится обьект модели
            return redirect('models_id', id=response.id)

        else:
            number_of_criterion = request.POST["number_of_criterion"]
            number_of_alternatives = request.POST["number_of_alternatives"]
            number_of_criterion_for_select = list(range(1, int(number_of_criterion) + 1))
            number_of_alternatives_for_select = list(range(1, int(number_of_alternatives) + 1))
            return render(request, "model/input_data.html",
                          {'number_of_criterion_for_select': number_of_criterion_for_select,
                           'number_of_alternatives_for_select': number_of_alternatives_for_select,
                           'error': "Ошибка при заполнении. Повторите попытку ввода"})


class ModelView(LoginRequiredMixin, CacheMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        try:
            model = Model.objects.get(id=id)
            model_data, model_header = get_model_data(model.id)
            return render(request, "model/model.html",
                          {'model_data': model_data,
                           'model_header': model_header,
                           'model': model})
        except:
            return redirect('models')

    @staticmethod
    def post(request, id):
        """ Delete model """
        if request.POST["_method"] == 'DELETE':
            model = Model.objects.get(id=id)

            try:
                import shutil
                path_files = MEDIA_ROOT + '/files/models/' + str(model.id)
                shutil.rmtree(path_files)
                path_img = MEDIA_ROOT + '/' + str(model.id)
                shutil.rmtree(path_img)

            except:
                pass

            model.delete()
            return redirect('models')


class StatisticsView(LoginRequiredMixin, CacheMixin, View):
    login_url = 'login'

    def get(self, request):
        try:
            x_pacom, y_pacom, number_of_alternatives = get_statistics(request)
            path_img = built_statistics(x_pacom, y_pacom)
            context_table_pacom = get_table_context(x_pacom, y_pacom, number_of_alternatives)

            x_snod, y_snod, number_of_alternatives = get_statistics_original_snod(request)
            path_img_snod = built_statistics(x_snod, y_snod)
            context_table_snod = get_table_context(x_snod, y_snod, number_of_alternatives)
            error = False

            number_of_alternatives, number_of_question, number_of_repeted_question, path_img_snod_number_question, path_img_snod_number_of_repeted_question = built_statistics_number_question(
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

        return render(request, "statistics.html", {'path_img': path_img,
                                                   'path_img_snod': path_img_snod,
                                                   'path_img_snod_number_question': path_img_snod_number_question,
                                                   'path_img_snod_number_of_repeted_question': path_img_snod_number_of_repeted_question,
                                                   'context_table_pacom': context_table_pacom,
                                                   'context_table_snod_number_of_question': context_table_snod_number_of_question,
                                                   'context_table_snod': context_table_snod,
                                                   'error': error})


