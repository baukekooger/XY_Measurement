import serial
import serial.tools.list_ports
import logging
from enum import IntEnum


# Constants
class Mode(IntEnum):
    MANUAL = 1
    AUTO = 2
    SINGLE = 3
    REPEAT = 4
    EXTERNAL_GATE = 5


class SC10(serial.Serial):
    """ 
        Serial-control class for the Thorlabs SC10 shutter
    """
    def __init__(self, port=None, timeout=0.1):
        super().__init__()

        # Serial __init__ methods
        self.baudrate = 9600
        self.timeout = timeout
        self.parity = serial.PARITY_NONE
        self.port = port

        self.prompt = '> '
        self.connect(port)

    @property
    def connected(self):
        return self.is_open

    @property
    def model(self):
        """
            Returns the model number and firmware revision
        """
        identifier = self._query_value('id')
        return identifier[1]

    @property
    def enabled(self):
        return int(self._query_value('ens')[-2]) == 1

    @property
    def mode(self):
        return Mode(int(self._query_value('mode')[-2]))

    @mode.setter
    def mode(self, value):
        self._write_value('mode', value=value)
        
    def connect(self, port=None):
        """ 
            Connects to Thorlabs Shuttercontroller SC10 
        """
        # Connect to port. If port is None, iterate over all available COM ports.
        if not port:
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                if p.description == 'n/a':
                    continue
                try:
                    self.port = p.device
                    self.open()
                    if 'SC10' not in self.model:
                        self.disconnect()
                        self.port = None
                    else:
                        break
                except serial.SerialException:
                    logging.debug('Cannot connect to Serial Device on port: {}'.format(self.port))
                except ConnectionError as e:
                    logging.debug('{}: {}'.format(p.device, e))
        else:
            try:
                self.port = port
                self.open()
            except serial.SerialException:
                raise ConnectionError('Cannot connect to SC10 on port: {}'.format(self.port))
            
    def disconnect(self):
        """ 
            Disconnects the Thorlabs Shuttercontroller SC10 
        """
        self.close()

    def enable(self):
        """ 
            Opens the shutter
        """
        if not self.enabled:
            self._write_value('ens')

    def disable(self):
        """ 
            Closes the shutter
        """
        if self.enabled:
            self._write_value('ens')
    
    def _query_value(self, command):
        self.write('{}?\r'.format(command).encode())
        v = self.readline().decode().split('\r')
        if not v[-1] == self.prompt:
            raise ConnectionError('Shuttercontrol did not return correct prompt')
        return v
        
    def _write_value(self, command, value=None):
        if not value:
            self.write('{}\r'.format(command).encode())
        else:
            self.write('{}={}\r'.format(command, value).encode())

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __repr__(self):
        return '<Thorlabs Shuttercontroller SC10 : {}>'.format(self.model)
