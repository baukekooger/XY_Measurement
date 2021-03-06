from transitions.extensions import HierarchicalGraphMachine as Machine
from yaml import safe_load as yaml_safe_load
import io
from PIL import Image
from pathlib import Path
# provide path to the main configuration file
pathconfigstate = Path(__file__).parent / 'config_statemachine.yaml'


class PlotStateMachine:
    """
    Plot statemachine for the minimal experiment.
    """

    def __init__(self):
        with pathconfigstate.open() as f:
            self.stateconfig = yaml_safe_load(f)
        self.stateconfig['model'] = self
        self.machine = Machine(**self.stateconfig)
        self.is_done = False

    def show_statemachine(self, **kwargs):
        # use kwarg show_roi = True to show statechart for current state only
        stream = io.BytesIO()
        self.machine.get_graph(**kwargs).draw(stream, prog='dot', format='png')
        image = Image.open(stream)
        image.show()

    def _from_state(self, *args):
        print(f'from: {self.state}')

    def _in_state(self, *args):
        print(f'in: {self.state}')

    def _start(self):
        pass

    def _define_experiment(self, page):
        print(page)
        pass

    def _finalize(self):
        pass

    def _align(self):
        pass

    def _stop_align(self):
        pass

    def _parse_config(self):
        pass

    def _connect_all(self):
        pass

    def _open_file(self):
        pass

    def _measure(self):
        pass

    def _prepare(self):
        pass

    def _process_data(self):
        pass

    def _write_file(self):
        pass

    def _calculate_progress(self):
        pass

    def _load_configuration(self):
        pass

    def _save_configuration(self):
        pass

    def _experiment_aborted(self):
        pass

    def _abort(self):
        pass

    def _completed(self):
        pass

    def _prepare_measurement(self):
        pass

    def _define_triggers(self):
        pass

    def _start_calibration(self):
        pass

    def _continue_calibration(self):
        pass

    def _parse_calibration(self):
        pass

    def _prepare_measurement_calibration(self):
        pass

    def _measure_calibration(self):
        pass

    def _write_data_calibration(self):
        pass

    def _calculate_progress_calibration(self):
        pass

    def _calibration_notify_user(self):
        pass

    def _calibration_aborted(self):
        pass

    def _calibration_completed(self):
        pass

    def _emit_shit(self):
        pass

    def _connect_signals_experiment(self):
        pass

    def _disconnect_signals_experiment(self):
        pass

    def _measurement_aborted(self):
        pass

    def _measurement_completed(self):
        pass
