from model.models import Model
from services.park import auto_mode_range, write_range_data, auto_mode_compare, write_result_of_compare_pacom, \
    get_park_question
from Verbal_Decision_Analysis.celery import app


@app.task(serializer='json')
def auto_mode_pacom(input_data, request, model_id):

    model = Model.objects.get(id=model_id)
    Model.objects.filter(id=model_id).update(is_searching_pacom=True)

    try:
        while input_data['flag_find_winner'] == 0:
            if input_data['flag_range'] is False:
                try:
                    try:
                        data = auto_mode_range(input_data, request)
                    except Exception as e:
                        print(e)
                        print(123)
                    try:
                        write_range_data(data, model, auto_mode=True)
                    except Exception as e:
                        print(e)
                        print(124)
                except Exception as e:
                    print(1)

            else:
                try:
                    try:
                        data = auto_mode_compare(input_data, auto_mode=True)
                    except Exception as e:
                        print(12)
                        print(e)

                    try:
                        write_result_of_compare_pacom(data, model, auto_mode=True)
                    except Exception as e:
                        print(13)
                        print(e)

                except Exception as e:
                    print(e)
                    print(2)
            try:
                input_data = get_park_question(model)
            except Exception as e:
                print(e)
                print(3)

    except Exception as e:
        print(e)
        print(4)
        return False
    return True