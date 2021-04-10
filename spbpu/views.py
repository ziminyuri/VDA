import os
import random
from random import randint

from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as django_logout

from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, View

from services.model import create_model, get_model_data
from services.pairs_of_options import (absolute_value_in_str, create_files,
                                       data_of_winners, make_question,
                                       write_answer)
from services.park import (auto_mode_pacom, get_context_history_answer,
                           get_park_question, get_winners_from_model,
                           write_range_data, write_result_of_compare_pacom)


from services.snod_original import get_original_snod_question, write_original_snod_answer, \
    get_winners_from_model_original_snod, get_context_history_answer_original_snod
from services.settings import settingsPACOMCreate, settingsOrigianlSnodCreate
from spbpu.models import (HistoryAnswer, Model, Option, PairsOfOptions)
from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from services.services import get_userprofile
from services.statistics import get_statistics, built_statistics, get_statistics_original_snod,  get_table_context
from django.contrib.auth.mixins import LoginRequiredMixin

if 'DATABASE_URL' in os.environ:
    path_img = 'glacial-everglades-54891.herokuapp.com'


# Авторизация
class LoginView(View):
    def get(self, request):

        return render(request, "spbpu/auth.html", {"login_error": ''})

    def post(self, request):
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("index")

        else:
            login_error = "Неверный логин или пароль! Повторите попытку."
            return render(request, "spbpu/auth.html", {"login_error": login_error})


# Регистрация
class RegistrationView(View):
    def get(self, request):
        return render(request, "spbpu/registration.html", {'error': None})

    def post(self, request):
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        password_2 = request.POST.get("password_2")

        if password != password_2:
            error = 'Пароли не совпадают'
            return render(request, "spbpu/registration.html", {'error': error})

        user = User.objects.filter(username=email)
        if not user:
            User.objects.create_user(email, email, password)
            auth.authenticate(username=email, password=password)
            return redirect('login')
        else:
            error = 'Пользователь с таким e-mail существует'
            return render(request, "spbpu/registration.html", {'error': error})


# Выход из системы
class LogoutView(View):
    def get(self, request):
        django_logout(request)
        return redirect("login")


class IndexView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        return render(request, "spbpu/index.html", {})


class DemoModelCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        return render(request, "spbpu/model/demo_choice_number.html", {})

    def post(self, request):
        response = create_model(demo_model=True, request=request)

        if response is not False:
            create_files(response)  # В response находится обьект модели

        return redirect('models_id', response.id)


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
            return render(request, "spbpu/upload_model.html", {'error': error})
        create_files(model)
        return redirect('models_id', id=model.id)

    def get(self, request):
        return render(request, "spbpu/upload_model.html", {})


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
        return render(request, "spbpu/model/choice_number.html", {'number_for_select': number_for_select})

    # Данные для заполнения таблицы
    def post(self, request):
        number_of_criterion = request.POST["number_of_criterion"]
        number_of_alternatives = request.POST["number_of_alternatives"]
        number_of_criterion = int(number_of_criterion)
        number_of_alternatives = int(number_of_alternatives)
        number_of_criterion_for_select = list(range(1, number_of_criterion + 1))
        number_of_alternatives_for_select = list(range(1, number_of_alternatives + 1))
        return render(request, "spbpu/model/input_data.html",
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
        models = Model.objects.filter(id_user=user)
        return render(request, "spbpu/model/models.html", {'models': models})

    @staticmethod
    # Cоздание модели после ввода данных в таблице
    def post(request):

        response = create_model(demo_model=False, request=request)

        if response is not False:
            create_files(response)  # В response находится обьект модели
            return redirect('models_id', id=response.id)

        else:
            number_of_criterion = request.POST["number_of_criterion"]
            number_of_alternatives = request.POST["number_of_alternatives"]
            number_of_criterion_for_select = list(range(1, int(number_of_criterion) + 1))
            number_of_alternatives_for_select = list(range(1, int(number_of_alternatives) + 1))
            return render(request, "spbpu/model/input_data.html",
                          {'number_of_criterion_for_select': number_of_criterion_for_select,
                           'number_of_alternatives_for_select': number_of_alternatives_for_select,
                           'error': "Ошибка при заполнении. Повторите попытку ввода"})


class ModelView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        try:
            model = Model.objects.get(id=id)
            model_data, model_header = get_model_data(model.id)
            return render(request, "spbpu/model/model.html",
                          {'model_data': model_data,
                           'model_header': model_header,
                           'model': model})
        except:
            return redirect('models')

    @staticmethod
    # Delete model
    def post(request, id):
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


class SnodSearchView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        model = Model.objects.get(id=id)
        message = make_question(model)
        return render(request, "spbpu/snod/question.html",
                      {'message': message,
                       'model': model, 'origianl_snod': 0})

    @staticmethod
    def post(request, id):

        answer = request.POST["answer"]
        message = write_answer(request, answer)

        # Проверяем, что нашли лучшую альтернативу в модели
        flag_find_winner = message['flag_find_winner']
        if flag_find_winner == 0:
            model = Model.objects.get(id=id)
            return render(request, "spbpu/snod/question.html",
                          {'message': message,
                           'model': model, 'origianl_snod': 0})
        else:
            return render(request, "spbpu/snod/result.html",
                          {})


class SnodDetailView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, id):
        model = Model.objects.get(id=id)
        option_shnur = Option.objects.get(id=model.id_winner_option_shnur)
        option_many = Option.objects.get(id=model.id_winner_option_many)

        # История ответов
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

        return render(request, "spbpu/snod/result.html",
                      response)


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
            return render(request, "spbpu/park/range.html", {'response': response, 'model': model})

        else:
            return render(request, 'spbpu/park/compare_alternative.html', {'response': response, 'model': model})

    def post(self, request, id):
        model = Model.objects.get(id=id)
        try:
            # Флаги после ранжирование
            range = bool(int(request.POST["range"]))

        except:
            # Флаги после сравнения критериев
            range = bool(request.POST["range"])

        compare = bool(int(request.POST["compare"]))

        if range is True and compare is False:
            # Запись данных после ранжирования
            response = write_range_data(request, model)  # TODO Проверить что нет ошибок ранжирования
            response = get_park_question(model)

            return render(request, 'spbpu/park/compare_alternative.html', {'response': response, 'model': model})

        if compare is True:
            # Запись после сравнения критериев
            write_result_of_compare_pacom(request, model)
            response = get_park_question(model)

            if response['flag_find_winner'] is True:
                return redirect('park_result', pk=model.id)

            elif response['flag_range'] is False:
                return render(request, "spbpu/park/range.html", {'response': response, 'model': model})
            else:
                return render(request, 'spbpu/park/compare_alternative.html', {'response': response, 'model': model})


class SettingsPACOMCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        context = {'model': get_object_or_404(Model, id=id)}
        context['mode'] = ['Классический', 'Только различные значения критериев', 'Автоматический']
        return render(request, "spbpu/park/settings.html", context)

    def post(self, request, id, **kwargs):
        settings = settingsPACOMCreate(request)
        Model.objects.filter(id=id).update(id_settings_pacom=settings)
        return redirect('park_search', id=id)


class ParkDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login'

    model = Model
    template_name = 'spbpu/park/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response'] = get_winners_from_model(self.kwargs['pk'])
        context['model_data'], context['model_header'] = get_model_data(self.kwargs['pk'])
        context['history'] = get_context_history_answer(self.kwargs['pk'])

        return context


class StatisticsView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        try:
            x_pacom,y_pacom, number_of_alternatives = get_statistics(request)
            path_img = built_statistics(x_pacom, y_pacom)
            context_table_pacom = get_table_context(x_pacom, y_pacom, number_of_alternatives)

            x_snod, y_snod, number_of_alternatives = get_statistics_original_snod(request)
            path_img_snod = built_statistics(x_snod, y_snod)
            context_table_snod = get_table_context(x_snod, y_snod, number_of_alternatives)
            error = False
        except Exception as e:
            path_img = None
            path_img_snod = None
            context_table_snod = None
            context_table_pacom = None
            error = True

        return render(request, "spbpu/statistics.html", {'path_img': path_img,
                                                         'path_img_snod': path_img_snod,
                                                         'context_table_pacom': context_table_pacom,
                                                         'context_table_snod': context_table_snod,
                                                         'error': error})


class SettingsOriginalSnodCreateView(LoginRequiredMixin, View):
    login_url = 'login'

    @staticmethod
    def get(request, id):
        context = {'model': get_object_or_404(Model, id=id)}
        context['mode'] = ['Классический', 'Автоматический']
        return render(request, "spbpu/snod/settings_original_snod.html", context)

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
        return render(request, "spbpu/snod/question.html",
                      {'message': message,
                       'model': model, 'original_snod': 1})

    def post(self, request, id):
        model = Model.objects.get(id=id)

        flag_find_winner = 0
        message = get_original_snod_question(model)

        while (flag_find_winner == 0 and model.id_settings_original_snod.auto_mode is True):
            answer: int = random.randint(0, 2)
            message = write_original_snod_answer(request, answer, auto=True,
                                       message=message)
            flag_find_winner = message['flag_find_winner']

        if model.id_settings_original_snod.auto_mode is False:
            answer = request.POST["answer"]
            message = write_original_snod_answer(request, answer, auto=False)

        # Проверяем, что нашли лучшую альтернативу в модели
        flag_find_winner = message['flag_find_winner']

        if flag_find_winner == 1:
            return redirect('snod_original_result', id=id)

        else:
            return render(request, "spbpu/snod/question.html",
                          {'message': message,
                           'model': model, 'original_snod': 1})


class OriginalSnodDetailView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, id):
        context = {'response': get_winners_from_model_original_snod(id)}
        context['model_data'], context['model_header'] = get_model_data(id)
        context['history'] = get_context_history_answer_original_snod(id)
        context['model'] = Model.objects.get(id=id)
        return render(request, "spbpu/snod/original_snod_result.html", {'context': context})

