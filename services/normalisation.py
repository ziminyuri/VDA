def normalisation_time(delta_time_shnur):
    delta_time_shnur = str(delta_time_shnur)
    print(delta_time_shnur)
    time = delta_time_shnur.split('.')[0]
    result = 'Прошло: '

    if time.split(':')[0] != '0':
        result += time.split(':')[0] + ' ч '

    if time.split(':')[1] != '00':
        if time.split(':')[1][0] != '0':
            result += time.split(':')[1] + ' мин '
        else:
            result += time.split(':')[1][1] + ' мин '

    if time.split(':')[2] != '00':
        if time.split(':')[2][0] != '0':
            result += time.split(':')[2] + ' сек '
        else:
            result += time.split(':')[2][1] + ' сек '

    result += delta_time_shnur.split('.')[1] + ' мкс'

    return result
