import serial
import serial.tools.list_ports
import logging
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot


class QShutterControl(QObject):
    """
    VISA-control class for the Thorlabs SC10 shutter as a QObject
    """
    shutter_status = pyqtSignal(bool)

    def __init__(self, parent=None, port=None, timeout=10, polltime=0.1):
        super().__init__(parent=parent)
        self.logger = logging.getLogger('Qinstrument.QShutterControl')
        self.logger.info('init QShutterControl')
        self.sc = None  # serial handle to the actual shuttercontroller
        # Shuttercontrol status
        self.mutex = QMutex(QMutex.Recursive)
        self.connected = False
        self.prompt = '> '
        self.timeout = timeout
        self.polltime = polltime
        self.port = port
        self.measuring = False

    def connect(self, name=None):
        """ Connect the shuttercontroller. """
        try:
            self.logger.info('Attempting to connect the shuttercontroller.')
            if not name:
                name = self.get_port('THORLABS SC10')
            self.sc = serial.Serial(name, 9600, parity=serial.PARITY_NONE, timeout=0.1)
            self.connected = True
        except NameError as e:
            self.logger.error('Could not connect to Thorlabs SC10 shuttercontroller')
            raise ConnectionError('Could not connect to Thorlabs SC10 shuttercontroller')

    def disconnect(self):
        """ Disconnect the shuttercontroller. """
        if not self.connected:
            self.logger.info('Shuttercontroller already disconnected')
            return
        self.logger.info('Disconnecting shuttercontroller')
        self.sc.close()
        self.connected = False

    def enable(self):
        """ Open the shutter. """
        self.logger.info('Enabling shutter unless already open')
        with(QMutexLocker(self.mutex)):
            if not int(self.query_value('ens')):
                self.write_value('ens')

    def measure(self):
        """ Measure the shutter status. """
        self.logger.info('measuring shutter status')
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            # returns true is shutter is enabled
            if self.query_value('ens') == 1:
                self.shutter_status.emit(True)
            else:
                self.shutter_status.emit(False)
            self.measuring = False

    def disable(self):
        """ Close the shutter """
        self.logger.info('disabling shutter')
        with(QMutexLocker(self.mutex)):
            if int(self.query_value('ens')):
                self.write_value('ens')

    def get_port(self, modelname):
        """
        Retrieve the first port the selected modelname is connected to.
        Code adapted from https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
        and https://stackoverflow.com/questions/16811807/how-to-find-all-serial-devices-com .

        Args:
            modelname (str): name of the desired device

        Returns:
            str: COM port name the desired device is connected to

        Raises:
            NameError: if the desired device cannot be found
        """
        self.logger.info('Retrieving shuttercontrol port. ')
        ports = [p.device for p in serial.tools.list_ports_windows.comports()]
        for port in ports:
            try:
                s = serial.Serial(port, timeout=0.1)
                s.write('{}?\r'.format('id').encode())
                id = s.readline().decode().split('\r')[-2]
                s.close()
                if modelname in id:
                    return port
            except (OSError, serial.SerialException, IndexError):
                pass
        raise NameError('{} could not be found!'.format(modelname))

    def query_value(self, command):
        """ Query the shuttercontroller. """
        self.logger.debug(f'Querying the shuttercontroller with command {command}')
        if not self.connected:
            raise ConnectionError('Shuttercontrol not connected, please connect first')
        self.sc.write('{}?\r'.format(command).encode())
        v = self.sc.readline().decode().split('\r')
        if not v[-1] == self.prompt:
            raise ConnectionError('Shuttercontrol did not return correct prompt')
        return int(v[-2])

    def write_value(self, command, value=None):
        """ Write a value to the shuttercontroller. """
        self.logger.info(f'Attempting to write to the shuttercontroller, command = {command}, value = {value}')
        if not self.connected:
            self.logger.error('Shuttercontrol not connected')
            raise ConnectionError('Shuttercontrol not connected, please connect first')
        if not value:
            self.sc.write('{}\r'.format(command).encode())
        else:
            self.sc.write('{}={}\r'.format(command, value).encode())


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)