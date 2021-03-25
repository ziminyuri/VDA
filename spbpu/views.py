import os
from random import randint

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.models import User

from spbpu.models import Option, PairsOfOptions, Model, HistoryAnswer, UserProfile, SettingsPACOM
from services.pairs_of_options import create_files, make_question, write_answer, absolute_value_in_str, data_of_winners
from services.model import create_model, get_model_data
from services.park import get_park_question, write_range_data, write_result_of_compare_pacom, get_winners_from_model, \
    get_context_history_answer
from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from django.views.generic import View, DetailView, CreateView
from django.shortcuts import get_object_or_404

if 'DATABASE_URL' in os.environ:
    path_img = 'glacial-everglades-54891.herokuapp.com'


def login_view(request):
    # Авторизация
    login_error = ""
    if request.POST:
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("index")

        else:
            login_error = "Неверный логин или пароль! Повторите попытку."

    return render(request, "spbpu/auth.html", {"login_error": login_error})


def registration_view(request, *args, **kwargs):
    # Регистрация
    if request.POST:
        context = kwargs
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        password_2 = request.POST.get("password_2")

        if password != password_2:
            error = 'Пароли не совпадают'
            return render(request, "spbpu/registration.html", {'error': error})

        user = UserProfile.objects.filter(username=email)
        if not user:
            User.objects.create_user(email, email, password)
            user = auth.authenticate(username=email, password=password)
            UserProfile.objects.create(
                user=user,
                username=email,
            )
            return redirect('login')
        else:
            error = 'Пользователь с таким e-mail существует'
            return render(request, "spbpu/registration.html", {'error': error})

    else:
        return render(request, "spbpu/registration.html", {'error': None})


@login_required
def logout_view(request):
    # Выход из системы
    django_logout(request)
    return redirect("index")


@login_required(login_url="login")
def index_view(request):
    # Главная страница
    return render(request, "spbpu/index.html", {})


@login_required(login_url="login")
def upload_view(request):
    # Загрузка модели через CSV

    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        r_int = str(randint(0, 100))
        path_csv = request.user.username + '/' + r_int + uploaded_file.name
        fs.save(path_csv, uploaded_file)
        model = create_model(demo_model=False, path_csv=path_csv)
        if model is False:
            error = 'Возникла ошибка при загрузке файла. Проверьте файл'
            return render(request, "spbpu/upload_model.html", {'error': error})
        create_files(model)
        return redirect('models_id', id=model.id)

    return render(request, "spbpu/upload_model.html", {})


@login_required(login_url="login")
def download_view(request):
    if request.method == 'POST':
        file_path = 'media/demo/demo.csv'
        data = open(file_path, "rb").read()
        response = HttpResponse(data, content_type='application;')
        response['Content-Length'] = os.path.getsize(file_path)
        response['Content-Disposition'] = 'attachment; filename=%s' % 'demo.csv'

        return response


@login_required(login_url="login")
def create_model_view(request):
    if request.method == 'POST':
        # Данные для заполнения таблицы
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

    # Данные для задания нужного кол-ва альтернатив и кол-ва критериев в пользовательской модели
    number_for_select = list(range(1, 11))
    return render(request, "spbpu/model/choice_number.html", {'number_for_select': number_for_select})


@login_required(login_url="login")
def models_view(request):
    # По GET список всех моделей, по POST создание модели после ввода данных в таблице
    if request.method == 'POST':
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

    elif request.method == 'GET':
        # Тут надо выводить только модели
        models = Model.objects.all()

        return render(request, "spbpu/model/models.html", {'models': models})


@login_required(login_url="login")
def models_view_id(request, id):
    # Просмотр информации о модели по GET, удаление модели по DELETE
    if request.method == 'POST':
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
            return redirect(models_view)

    try:
        model = Model.objects.get(id=id)
        model_data, model_header = get_model_data(model.id)
        return render(request, "spbpu/model/model.html",
                      {'model_data': model_data,
                       'model_header': model_header,
                       'model': model})
    except:
        return redirect(models_view)


class SnodSearchView(View):
    @staticmethod
    def get(request, id):
        model = Model.objects.get(id=id)
        message = make_question(model)
        return render(request, "spbpu/snod/question.html",
                      {'message': message,
                       'model': model})

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
                           'model': model})
        else:
            return render(request, "spbpu/snod/result.html",
                          {})


#TODO переписать на класс
@login_required(login_url="login")
def snod_result(request, id):
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
    if len(pairs) < 10:
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


class ParkSearchView(View):
    def get(self, request, id):
        model = Model.objects.get(id=id)
        if model.id_settings_pacom is None:
            return redirect('pacom_settings_create', id=id)

        response = get_park_question(model)
        if response['flag_range'] is False:
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

        elif compare is True:
            # Запись после сравнения критериев
            write_result_of_compare_pacom(request, model)
            response = get_park_question(model)

            if response['flag_find_winner'] is True:
                return redirect('park_result', id=model.id)

            elif response['flag_range'] is False:
                return render(request, "spbpu/park/range.html", {'response': response, 'model': model})
            else:
                return render(request, 'spbpu/park/compare_alternative.html', {'response': response, 'model': model})


class SettingsPACOMCreateView(View):
    @staticmethod
    def get(request, id):
        context = {'model': get_object_or_404(Model, id=id)}
        return render(request, "spbpu/park/settings.html", context)

    def post(self, request, id, **kwargs):
        settings = SettingsPACOM.objects.create(**kwargs)
        Model.objects.filter(id=id).update(id_settings_pacom=settings)
        return redirect('park_search', id=id)


class ParkDetailView(DetailView):
    model = Model
    template_name = 'spbpu/park/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response'] = get_winners_from_model(self.kwargs['pk'])
        context['model_data'], context['model_header'] = get_model_data(self.kwargs['pk'])
        context['history'] = get_context_history_answer(self.kwargs['pk'])

        return context
