from transitions.extensions import HierarchicalGraphMachine
import logging
import io
from PIL import Image

logging.basicConfig(level=logging.INFO)


class Nestedmachine:
    """ Plot nested states"""

    states = ['A', 'B', {'name': 'C', 'children': [{'name': '1', 'children': ['a', 'b', 'c'], 'initial': 'a',
                                                    'transitions': [['go', 'a', 'b']]},
                                                   {'name': '2', 'children': ['x', 'y', 'z'], 'initial': 'z'}],
                         'transitions': [['go_x', '2_z', '2_x']]}]

    transitions = [['reset', 'C_1_b', 'B']]

    def __init__(self):
        self.sm = HierarchicalGraphMachine(states=self.states, transitions=self.transitions, initial='A')

    def show_statemachine(self, **kwargs):
        # use kwarg show_roi = True to show statechart for current state only
        stream = io.BytesIO()
        self.sm.get_graph(**kwargs).draw(stream, prog='dot', format='png')
        image = Image.open(stream)
        image.show()






