from django import forms


TYPE_CHOICES = [
    ('Классический', 'Классический'),
    ('Только различные значения критериев', 'Только различные значения критериев'),
    ('Автоматический', 'Автоматический')
]

class SettingsPACOMForm(forms.Form):
    type = forms.ChoiceField(choices=TYPE_CHOICES, label='Режим работы')
