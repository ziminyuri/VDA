from django import forms
from modification.models import ModelModification, CriterionModification
from model.models import Criterion, Model


class ModelModificationForm(forms.ModelForm):

    class Meta:
        model = ModelModification
        fields = ['type', 'model']
        exclude = ('model',)
        widgets = {
            'type': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
        }


class CriterionModificationForm(forms.ModelForm):

    def __init__(self, model_m, *args, **kwargs):
        # Then, let the ModelForm initialize:
        super(CriterionModificationForm, self).__init__(*args, **kwargs)
        model = Model.objects.get(id=model_m.model.id)
        # Finally, access the fields dict that was created by the super().__init__ call
        self.fields['criterion'].queryset = Criterion.objects.filter(id_model=model)

    class Meta:
        model = CriterionModification
        fields = ['name', 'criterion']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),
            'criterion': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
        }
