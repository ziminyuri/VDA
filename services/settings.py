from model.models import SettingsOrigianlSNOD, SettingsPACOM
from pacom.forms import SettingsPACOMForm
from snod.forms import SettingsSnodForm


def settingsPACOMCreate(request):
    form = SettingsPACOMForm(request.POST)
    if form.is_valid():
        type = form.cleaned_data['type']

    if type == 'Классический':
        return SettingsPACOM.objects.create()

    elif type == 'Только различные значения критериев':
        return SettingsPACOM.objects.create(larichev_question=False)
    else:
        return SettingsPACOM.objects.create(auto_mode=True)


def settingsOrigianlSnodCreate(request):
    form = SettingsSnodForm(request.POST)
    if form.is_valid():
        type = form.cleaned_data['type']

    if type == 'Классический':
        return SettingsOrigianlSNOD.objects.create()
    else:
        return SettingsOrigianlSNOD.objects.create(auto_mode=True)