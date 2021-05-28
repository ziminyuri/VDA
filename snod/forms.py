from django import forms


TYPE_CHOICES = [
    ('Классический', 'Классический'),
    ('Автоматический', 'Автоматический')
]

class SettingsSnodForm(forms.Form):
    type = forms.ChoiceField(choices=TYPE_CHOICES, label='Режим работы')