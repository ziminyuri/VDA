from Verbal_Decision_Analysis.celery import app
from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from .models import Model


@app.task(serializer='json')
def delete_model(id):
    """Удаление модели"""

    model = Model.objects.get(id=id)

    try:
        import shutil
        path_files = MEDIA_ROOT + '/files/models/' + str(model.id)
        shutil.rmtree(path_files)
        path_img = MEDIA_ROOT + '/' + str(model.id)
        shutil.rmtree(path_img)

    except:
        pass

    model.delete()