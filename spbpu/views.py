import csv
import json
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout as django_logout
from django.core.files.storage import FileSystemStorage
from datetime import datetime, timedelta

from django.contrib import auth
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from spbpu.models import Criterion, Option, Value, PairsOfOptions, Model, HistoryAnswer
from services.pairs_of_options import create_files, make_question, write_answer, absolute_value_in_str, data_of_winners
from services.model import create_model, get_model_data


def login(request):
    # Авторизация

    login_error = ""
    if request.POST:
        email = request.POST.get("username").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
                return redirect("index")
            else:
                return redirect("index_recruter")
        else:
            login_error = "Неверный логин или пароль! Повторите попытку."

    return render(request, "spbpu/auth.html", {"login_error": login_error})


@login_required
def logout(request):
    # Выход из системы
    django_logout(request)
    return redirect("index")


@login_required(login_url="login")
def index(request):
    # Главная страница

    return render(request, "spbpu/index.html", {})


@login_required(login_url="login")
def upload(request):
    # Загрузка модели через CSV

    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        path_csv = request.user.username + '/' + uploaded_file.name
        fs.save(path_csv, uploaded_file)
        model = create_model(demo_model=False, path_csv=path_csv)
        if model is False:
            error = 'Возникла ошибка при загрузке файла. Проверьте файл'
            return render(request, "spbpu/upload_model.html", {'error': error})

    return render(request, "spbpu/upload_model.html", {})


@csrf_exempt  # to make true read https://stackoverflow.com/questions/17716624/django-csrf-cookie-not-set
def registration(request):
    if request.method == 'POST':
        json_data: dict = json.loads(request.body)

        try:
            email: str = json_data["email"]
            password: str = json_data["password"]
            User.objects.create_user(email, email, password)
            return JsonResponse({"Message": "Пользователь создан"})

        except Exception as e:
            return JsonResponse({"Message": "Ошибка при создании пользователя"})





def demo_create(request):
    # Создаем демо модель на базе метода ШНУР
    if request.method == 'GET':
        model = create_model(demo_model=True)
        create_files(model)
        message = make_question(model)

        return JsonResponse(message, status=200)


def auto_create(request):
    if request.method == 'GET':
        options_obj_list = []
        model = create_model(demo_model=True)

        with open("api/files/demo.csv", encoding='utf-8') as r_file:
            file_reader = csv.reader(r_file, delimiter=",")
            count = False

            criterion_number = 1
            option_number = 1
            for row in file_reader:
                if count is False:

                    for i in range(2, len(row)):
                        option = Option.objects.create(name=row[i], id_model=model, number=option_number)
                        options_obj_list.append(option)
                        option_number += 1

                    count = True

                else:

                    if row[1] == 'min':
                        direction = False
                    else:
                        direction = True

                    max = float(row[2])
                    for i in range(3, len(row)):
                        if max < float(row[i]):
                            max = float(row[i])

                    criterion = Criterion.objects.create(name=row[0], id_model=model, direction=direction, max=max,
                                                         number=criterion_number)

                    criterion_number += 1

                    for i in range(2, len(row)):
                        value = float(row[i])
                        Value.objects.create(value=value, id_option=options_obj_list[i-2], id_criterion=criterion)

        n = len(options_obj_list)
        k = 1
        for i in range(n):
            for j in range(k, n):
                if i != j:
                    s = PairsOfOptions.objects.create(id_option_1=options_obj_list[i], id_option_2=options_obj_list[j],
                                                      id_model=model)

            k += 1
        create_files(model)
        message = make_question(model)
        i = 1
        while i == 1:
            message = question(message, auto=True)
            flag = message['flag_find_winner']
            if flag == 1:
                break

        response = {'model_id': model.id}
        return JsonResponse(response, status=200)


@csrf_exempt
def question(request, auto=False):
    if auto is True:
        return write_answer(request, auto=True)

    if request.method == 'POST':
        json_data: dict = json.loads(request.body)
        message = write_answer(json_data)
        return JsonResponse(message, status=200)



@csrf_exempt
def get_model(request, id):
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
            img.append({'pair': pair.id_option_1.name + ' и ' + pair.id_option_2.name,
                        'path': 'http://127.0.0.1:8000/media/' + str(model.id) + '/' + str(pair.id) + '.png',
                        'absolute_value': absolute_value})

    model_data, model_header = get_model_data(model.id)
    winners_data, winners_header = data_of_winners(model.id)

    response = {'option_shnur': option_shnur.name, 'option_many': option_many.name, 'history': answers, 'img': img,
                'time_shnur_elapsed': model.time_shnur, 'time_answer_elapsed': model.time_answer_shnur,
                'time_many_elapsed': model.time_many, 'model_data': model_data, 'model_header': model_header,
                'winners_data': winners_data, 'winners_header': winners_header}

    return JsonResponse(response, status=200, safe=False)


@csrf_exempt
def get_models(request):
    response = []
    try:
        models = Model.objects.all().exclude(id_winner_option_shnur=None)

        for model in models:
            response.append({'name': model.name, 'id': model.id})

    except Exception as e:
        print(e)

    return JsonResponse(response, status=200, safe=False)


@csrf_exempt
def demo_park_create(request):
    # Создание модели с демо данными для метода ПАРК
    model = create_model(demo_model=True)

    response = []
    try:
        pair = PairsOfOptions.objects.filter(id_model=model).first()
        criterions = Criterion.objects.filter(id_model=model)
        for criterion in criterions:
            value_1 = Value.objects.get(id_option=pair.id_option_1, id_criterion=criterion)
            value_2 = Value.objects.get(id_option=pair.id_option_2, id_criterion=criterion)
            response.append({'name': criterion.name, 'direction': criterion.direction, 'value_1': value_1.value,
                             'value_2': value_2.value})

    except Exception as e:
        print(e)

    return JsonResponse(response, status=200, safe=False)