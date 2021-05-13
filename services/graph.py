from graphviz import Digraph

from model.models import Option
from pacom.models import PairsOfOptionsPARK
from Verbal_Decision_Analysis.settings import MEDIA_ROOT


def get_graph_pacom(model):
    #Создаем граф для модели парка
    try:
        g = Digraph(format='png')
        colors = ['green', 'red']
        pairs = PairsOfOptionsPARK.objects.filter(id_model=model)
        options = Option.objects.filter(id_model=model).order_by('-quasi_order_pacom')
        for option in options:
            g.node(option.name, f"{option.name}\nквазиранг:{option.quasi_order_pacom}")

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

        path = MEDIA_ROOT + '/graph/' + str(model) + '_pacom'
        g.render(path, view=False)

    except Exception as e:
        print(e)

    return '/graph/' + str(model) + '_pacom.png'


def generate_exapmle_graph():
    """Гененрируем примеры графов"""

    try:
        g = Digraph(format='png')
        colors = ['green', 'red']

        g.node('Альтернатива 1', f"Альтернатива 1\nквазиранг:{1}")
        g.node('Альтернатива 2', f"Альтернатива 2\nквазиранг:{0}")

        g.edge('Альтернатива 1', 'Альтернатива 2', color=colors[0])

        path = f'{MEDIA_ROOT}/graph/example/1'
        g.render(path, view=False)

        g = Digraph(format='png')
        colors = ['green', 'red']

        g.node('Альтернатива 1', f"Альтернатива 1\nквазиранг:{1}")
        g.node('Альтернатива 2', f"Альтернатива 2\nквазиранг:{1}")

        g.edge('Альтернатива 1', 'Альтернатива 2', color=colors[0])
        g.edge('Альтернатива 2', 'Альтернатива 1', color=colors[0])

        path = f'{MEDIA_ROOT}/graph/example/2'
        g.render(path, view=False)

        g = Digraph(format='png')
        colors = ['green', 'red']

        g.node('Альтернатива 1', f"Альтернатива 1\nквазиранг:{1}")
        g.node('Альтернатива 2', f"Альтернатива 2\nквазиранг:{1}")

        g.edge('Альтернатива 1', 'Альтернатива 2', color=colors[1])
        g.edge('Альтернатива 2', 'Альтернатива 1', color=colors[1])

        path = f'{MEDIA_ROOT}/graph/example/3'
        g.render(path, view=False)

    except Exception as e:
        print(e)

