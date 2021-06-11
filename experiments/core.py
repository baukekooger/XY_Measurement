from transitions import Machine, State
import time
import yaml

def timed(func):
    def wrapper(self, *args, **kwargs):
        t1 = time.time()
        result = func(self, *args, **kwargs)
        t2 = time.time()
        self.measurement_duration += t2 - t1
        return result

    return wrapper


class Experiment(Machine):
    """
    Base class for pyXY experiments. Contains a statemachine and generators to run the experiment
    """
    def __init__(self, configfile='config.yml'):
        self.instruments = []
        self.name = 'Experiment'
        initial_state = State('waiting', on_enter=['_statechange', '_finalize'])
        states = [
            State('parsing configuration', on_enter='_parse_config'),
            State('opening file', on_enter='_open_file'),
            State('measuring', on_enter='_measure'),
            State('preparing', on_enter='_prepare'),
            State('processing data', on_enter='_process_data'),
            State('writing to file', on_enter='_write_file'),
            State('calculating progress', on_enter='_calculate_progress')
        ]
        transitions = [
            {'trigger': 'parse_config', 'source': 'waiting',
             'dest': 'parsing configuration'},
            {'trigger': 'open_file', 'source': 'parsing configuration',
             'dest': 'opening file'},
            {'trigger': 'prepare', 'source': ['opening file', 'writing to file'],
             'dest': 'preparing', 'unless': 'is_done'},
            {'trigger': 'measure', 'source': 'preparing',
             'dest': 'measuring', 'unless': 'is_done'},
            {'trigger': 'process_data', 'source': 'measuring',
             'dest': 'processing data', 'unless': 'is_done'},
            {'trigger': 'write_file', 'source': '*',
             'dest': 'writing to file'},
            {'trigger': 'calculate_progress', 'source': '*',
             'dest': 'calculating progress', 'unless': 'is_done'},
            {'trigger': 'finalize', 'source': '*',
             'dest': 'waiting'}]
        for state in states:
            state.on_enter.insert(0, '_statechange')
        states.append(initial_state)
        super().__init__(states=states, initial='waiting', queued=True)
        for transition in transitions:
            try:
                self.add_transition(transition['trigger'], transition['source'], transition['dest'],
                                            unless=transition['unless'])
            except KeyError:
                self.add_transition(transition['trigger'], transition['source'], transition['dest'])
        self.measurement_duration = 0
        self.done = True
        self.configfile = configfile
        self.measurement_params = {}
        self.startingtime = time.time()

    def _parse_config(self):
        pass

    def _finalize(self):
        """Stops all measurements and disconnects all Instruments
        """
        for instrument in self.instruments:
            instrument.measuring = False
            instrument.close()

    def run(self):
        while not self.done:
            self.next_state()
        self.finalize()
