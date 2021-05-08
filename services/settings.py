from model.models import SettingsPACOM, SettingsOrigianlSNOD


def settingsPACOMCreate(request):
    if request.POST['mode'] == 'Классический':
        return SettingsPACOM.objects.create()

    elif request.POST['mode'] == 'Только различные значения критериев':
        return SettingsPACOM.objects.create(larichev_question=False)
    else:
        return SettingsPACOM.objects.create(auto_mode=True)


def settingsOrigianlSnodCreate(request):
    if request.POST['mode'] == 'Классический':
        return SettingsOrigianlSNOD.objects.create()
    else:
        return SettingsOrigianlSNOD.objects.create(auto_mode=True)