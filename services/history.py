from model.models import Model
from services.snod_original import write_original_snod_answer
from Verbal_Decision_Analysis.settings import MEDIA_ROOT


def checking_already_has_answer(request, data, snod_original=False):

    options_1 = data['option_1_line'].split(';')
    options_2 = data['option_2_line'].split(';')
    options_1.sort()
    options_2.sort()

    model_id = data['model']

    if not snod_original:
        path = MEDIA_ROOT + '/files/models/' + str(model_id) + '.txt'
    else:
        path = MEDIA_ROOT + '/files/models/pacom' + str(model_id) + '.txt'

    try:
        with open(path) as f:
            lines = f.readlines()

        for line in lines:
            options_1_in_history = line.split('|')[0].split(';')
            options_2_in_history = line.split('|')[1].split('=')[0].split(';')

            options_1_in_history.remove('')
            options_2_in_history.remove('')
            options_1_in_history.sort()
            options_2_in_history.sort()

            if options_1_in_history == options_1 and options_2_in_history == options_2:
                answer = int(line.split('|=')[1].split('\n')[0])
                break
            elif options_1_in_history == options_2 and options_2_in_history == options_1:
                answer = int(line.split('|=')[1].split('\n')[0])
                if answer == 1:
                    answer = 2
                elif answer == 2:
                    answer = 1
                break
            else: answer = -1

        if answer != -1:
            message = write_original_snod_answer(request, answer, auto=True,
                                                 message=data)
            model = Model.objects.get(id=int(model_id))
            Model.objects.filter(id=model.id).update(number_repeated_questions_snod=
                                                     model.number_repeated_questions_snod+1)

            return message, True

    except Exception as e: pass

    return data, False

