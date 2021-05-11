from graphviz import Digraph

from model.models import Option, Model
from snod.models import PairsOfOptionsTrueSNOD
from Verbal_Decision_Analysis.settings import MEDIA_ROOT
from Verbal_Decision_Analysis.celery import app


@app.task(serializer='json')
def get_graph_snod(model_id):
    """Создаем граф для модели ШНУР"""

    model = Model.objects.get(id=model_id)

    try:
        g = Digraph(format='png')
        colors = ['green', 'red']
        pairs = PairsOfOptionsTrueSNOD.objects.filter(id_model=model)
        options = Option.objects.filter(id_model=model).order_by('-quasi_order_original_snod')
        for option in options:
            g.node(option.name, f"{option.name}\nквазиранг:{option.quasi_order_original_snod}")

        for pair in pairs:
            if pair.flag_winner_option == 1:
                g.edge(pair.id_option_1.name, pair.id_option_2.name, color=colors[0])
            elif pair.flag_winner_option == 2:
                g.edge(pair.id_option_2.name, pair.id_option_1.name, color=colors[0])
            elif pair.flag_winner_option == 0:
                g.edge(pair.id_option_2.name, pair.id_option_1.name, color=colors[0])
                g.edge(pair.id_option_1.name, pair.id_option_2.name, color=colors[0])
            elif pair.flag_winner_option == 3:
                g.edge(pair.id_option_2.name, pair.id_option_1.name, color=colors[1])
                g.edge(pair.id_option_1.name, pair.id_option_2.name, color=colors[1])

        path = MEDIA_ROOT + f'/graph/{str(model)}_snod'
        g.render(path, view=False)

    except Exception as e:
        print(e)

    Model.objects.filter(id=model_id).update(graph_snod=f'/graph/{str(model)}_snod.png')

