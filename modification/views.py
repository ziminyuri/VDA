from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render, redirect
from django.views import View

from model.models import Model, Criterion, Option
from modification.services.disaggregation import init_modificate_criterion_from_base, add_modification_criterion, \
    disaggregate_criterion, sort_not_disaggregate_and_disaggregate_criterion, \
    fill_values_for_not_disaggregate_criterion, get_incomparable_options_from_result
from modification.services.snod.search import get_original_snod_modification_question
from modification.services.values import fill_values
from snod.models import PairsOfOptionsTrueSNOD
from modification.forms import ModelModificationForm, CriterionModificationForm
from modification.models import ModelModification, CriterionModification, ModificationValue, ModificationOption



class PairsIncomparableListView(View):
    def get(self, request, id):
        """Список несравнимых пар + список модифированных моделей"""

        model = Model.objects.filter(id=id).annotate(numbers=Count('model')).order_by('id').first()
        pairs = PairsOfOptionsTrueSNOD.objects.filter(quasi_level=model.quasi_max_order_snod, flag_winner_option=3,
                                                      id_model=model)
        models_m = ModelModification.objects.filter(model=model)
        return render(request, "modification/pairs_incomparable_snod.html", {'pairs': pairs, 'model': model,
                                                                             'models_m': models_m})


class ModificationCreateView(View):
    def get(self, request, id):
        form = ModelModificationForm()
        return render(request, 'modification/create_model.html', {'form': form, 'error': None, 'id': id})

    def post(self, request, id):
        model = Model.objects.get(id=id)
        model_m = ModelModification(model=model)
        form = ModelModificationForm(request.POST, instance=model_m)

        if form.is_valid():
            model_m = form.save()
            return redirect('modification_criterion', id=model_m.id)
        else:
            error = form.errors
            return render(request, 'modification/create_model.html',
                          {'form': form, 'error': error, 'id': id})


class ModificationModelDeleteView(View):
    def post(self, request, id):
        """ Delete model """
        model_m = ModelModification.objects.get(id=id)
        model_m.delete()
        model_id = int(request.POST['model'])
        return redirect('pairs_incomparable', id=model_id)


class ModificationCriterionCreateView(View):
    def get(self, request, id):
        model_m = ModelModification.objects.get(id=id)
        criterions = Criterion.objects.filter(id_model=model_m.model.id)
        criterions_m = CriterionModification.objects.filter(model_m=model_m)
        form = CriterionModificationForm(model_m)

        if not criterions_m:
            criterions_m = init_modificate_criterion_from_base(criterions, model_m)

        if model_m.type.name == 'Агрегация критериев':
            return render(request, 'modification/aggregation.html',
                          {'criterions': criterions, 'id': id, 'criterions_m': criterions_m})
        else:
            return render(request, 'modification/disaggregation.html',
                          {'criterions': criterions, 'id': id, 'criterions_m': criterions_m, 'form': form})

    def post(self, request, id):
        model_m = ModelModification.objects.get(id=id)

        try:
            if request.POST['type'] == 'add':
                add_modification_criterion(request, model_m)
            else:
                disaggregate_criterion(request, model_m)

            return redirect('modification_criterion', id=model_m.id)

        except Exception as e:
            criterions_m = CriterionModification.objects.filter(model_m=model_m)
            form = CriterionModificationForm(model_m)
            return render(request, 'modification/disaggregation.html', {'id': id, 'criterions_m': criterions_m,
                                                                        'form': form})


class ModificationCriterionUpdateView(View):
    def post(self, request, id):
        """Изменяем имя модифицированного критерия"""
        name = request.POST['name']
        CriterionModification.objects.filter(id=id).update(name=name)
        model_m_id = request.POST['model_m']
        return redirect('modification_criterion', id=model_m_id)


class ModificationCriterionDeleteView(View):
    def post(self, request, id):
        """Удаляем модифицированный критерия"""
        criterion_id = CriterionModification.objects.get(id=id)
        criterion_id.delete()
        model_m_id = request.POST['model_m']
        return redirect('modification_criterion', id=model_m_id)


class ModificationValueCreateView(View):
    def get(self, request, id):
        model_m = ModelModification.objects.get(id=id)
        not_disaggregate_criterion, disaggregate_criterion = sort_not_disaggregate_and_disaggregate_criterion(model_m)
        fill_values_for_not_disaggregate_criterion(not_disaggregate_criterion, model_m)
        options = ModificationOption.objects.filter(model_m=model_m)

        return render(request, 'modification/input_values.html', {'number_of_criterion': len(disaggregate_criterion),
                                                                  'number_of_alternatives': len(options),
                                                                  'number_of_criterion_for_select': disaggregate_criterion,
                                                                  'number_of_alternatives_for_select': options,
                                                                  'id': id})

    def post(self, request, id):
        fill_values(request, id)
        return redirect('modification_snod_search', id=id)


class ModificationSnodSearchView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, id):
        model_m = ModelModification.objects.get(id=id)

        message = get_original_snod_modification_question(model_m)
        return render(request, "snod/question.html",
                      {'message': message,
                       'model': model_m, 'original_snod': 1})

    def post(self, request, id):
        model_m = ModelModification.objects.get(id=id)

        message = get_original_snod_modification_question(model_m)

        """Проверяем, что нашли лучшую альтернативу в модели"""
        flag_find_winner = message['flag_find_winner']

        if flag_find_winner == 1:
            return redirect('snod_original_result', id=id)

        return render(request, "snod/question.html",
                      {'message': message,
                       'model': model_m})




