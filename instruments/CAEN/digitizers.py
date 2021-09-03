import time
from PyQt5.QtCore import QObject, QMutex, pyqtSlot, pyqtSignal
from ctypes import c_char, byref, windll, pointer
from ctypes import c_uint32 as c_uint
from ctypes import c_int32 as c_int
import os
import logging
import numpy as np
# from . import definitions
import instruments.CAEN.definitions as definitions
from instruments.CAEN.definitions import AcqMode, IOLevel, TriggerMode, TriggerPolarity
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO)

# Add location of digitizer library to path
os.environ['PATH'] = os.path.dirname(__file__) + os.pathsep + 'lib' + os.pathsep + 'x86_64' ';' + os.environ['PATH']
pathdigilib = Path(__file__).parent / 'lib/x86_64/CAENDigitizer.dll'
_lib = windll.LoadLibrary(str(pathdigilib))


def list_available_devices():
    """
    Lists all devices connected to the computer.

    Returns
    -------
    devices : list
        list of available devices. Each device is described by a tuple
        (usb index, model name)
    """
    devices = []
    for i in range(0, 255):
        handle = c_int(0)
        board_info = definitions.BoardInfo()
        if _lib.CAEN_DGTZ_OpenDigitizer(definitions.ConnectionType.USB.value,
                                        i, 0, 0, byref(handle)) < 0:
            continue
        _lib.CAEN_DGTZ_GetInfo(handle, byref(board_info))
        _lib.CAEN_DGTZ_CloseDigitizer(handle)
        device = DigitizerHandle(i, board_info.ModelName, board_info.SerialNumber)
        devices.append(device)
    return devices


def handle_error(error_code):
    if error_code is not definitions.ErrorCode.Success.value:
        raise definitions.Error(error_code)
    return error_code


class DigitizerHandle:
    def __init__(self, usb_index, model, serial):
        self.usb_index = usb_index
        try:
            self.model = model.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            self.model = model
        self.serial = serial

    def __repr__(self):
        return '<DigitizerHandle {}:{}>'.format(self.model, self.serial)


class Digitizer(DigitizerHandle):

    def __init__(self, digitizer_handle: DigitizerHandle):
        DigitizerHandle.__init__(self, digitizer_handle.usb_index, digitizer_handle.model, digitizer_handle.serial)
        QObject.__init__(self)
        self._handle = c_uint(0)
        self.board_info = None
        self.buffer = None

    @property
    def buffer_size(self):
        return definitions.Buffersize[definitions.ModelNumber[self.model]] \
               - definitions.BufferCorr[definitions.ModelNumber[self.model]]

    @property
    def record_length(self):
        '''record_length is a value between N= 0 and 9, what fraction of the total buffersize will be used to store data.
        This is calculated as buffer_size // (2 ^ (10 - N))'''
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetRecordLength(self._handle, byref(return_value)))
        return return_value.value

    @record_length.setter
    def record_length(self, value):
        # Value is somewhere between 0 and 10
        if value < 0:
            value = 0
            logging.warning('Specified record length too small. '
                            'Set to minimum value: {}'.format(value))
        if value > 10:
            value = 10
            logging.warning('Specified record length too small. '
                            'Set to maximum value: {}'.format(value))
        post_trigger_size = self.post_trigger_size
        buffer_size = self.buffer_size
        record_length = buffer_size // (1 << (10 - value))
        set_value = c_uint(record_length)
        handle_error(_lib.CAEN_DGTZ_SetRecordLength(self._handle, set_value))
        self.post_trigger_size = post_trigger_size

    def manual_record_length(self, value):
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetRecordLength(self._handle, set_value))

    @property
    def post_trigger_size(self):
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetPostTriggerSize(self._handle, byref(return_value)))
        return return_value.value

    @post_trigger_size.setter
    def post_trigger_size(self, value):
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetPostTriggerSize(self._handle, set_value))

    @property
    def max_num_events(self):
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetMaxNumEventsBLT(self._handle, byref(return_value)))
        return return_value.value

    @max_num_events.setter
    def max_num_events(self, value):
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetMaxNumEventsBLT(self._handle, set_value))

    @property
    def number_of_channels(self):
        """"
        Returns the number of channels this digitizer has
        """
        board_info = definitions.BoardInfo()
        _lib.CAEN_DGTZ_GetInfo(self._handle, byref(board_info))
        return board_info.Channels

    @property
    def active_channels(self):
        """
        List of all the active channels
        """
        mask = self.channel_enable_mask[2:]
        active = set()
        for i, x in enumerate(reversed(mask)):
            if int(x):
                active.add(i)
        return active

    @active_channels.setter
    def active_channels(self, channels):
        mask = 0
        for channel in channels:
            mask += 1 << channel
        self.channel_enable_mask = mask

    @property
    def channel_enable_mask(self):
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetChannelEnableMask(self._handle, byref(return_value)))
        return bin(return_value.value)

    @channel_enable_mask.setter
    def channel_enable_mask(self, value):
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetChannelEnableMask(self._handle, set_value))

    def set_channel_gain(self, channel, value):
        address = 0x1028 + 0x100 * channel
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, address, set_value))

    def get_channel_gain(self, channel):
        address = 0x1028 + 0x100 * channel
        value = c_int(0)
        handle_error(_lib.CAEN_DGTZ_ReadRegister(self._handle, address, byref(value)))
        return value.value

    @property
    def acquisition_mode(self):
        """
        Type of acquisition : Enum.

        AcqMode.SW_CONTROLLED           = 0 : Start and stop acquisition is issued by software command.
        AcqMode.S_IN_CONTROLLED         = 1 : Acquisition starts when the external signal on S-IN connector sets high,
                                              while is stopped when it sets low. Instead of S-IN. GPI connector must be
                                              referred in case of Desktop/NIM boards.
        AcqMode.FIRST_TRG_CONTROLLED    = 2 : Start is issued on the first trigger pulse (rising edge) on the TRG-IN
                                              connector. This pulse is not used as a trigger; actual triggers start
                                              from the second pulse on TRG-IN. The Stop acquisition must be SW
                                              controlled. Please refer to the digitizer documentation for details.
        AcqMode.LVDS_CONTROLLED         = 3 : Not in Library Reference #TODO
        """
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetAcquisitionMode(self._handle, byref(return_value)))
        return AcqMode(return_value.value)

    @acquisition_mode.setter
    def acquisition_mode(self, value):
        if isinstance(value, AcqMode):
            value = value.value
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetAcquisitionMode(self._handle, set_value))

    @property
    def software_trigger_mode(self):
        """
        Decides whether the trigger software should only be used to generate the acquisition trigger, only to generate
        the trigger output, or both : Enum.

        TriggerMode.DISABLED        = 0
        TriggerMode.ACQ_ONLY        = 1
        TriggerMode.EXTOUT_ONLY     = 2
        TriggerMode.ACQ_AND_EXTOUT  = 3
        """
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetSWTriggerMode(self._handle, byref(return_value)))
        return TriggerMode(return_value.value)

    @software_trigger_mode.setter
    def software_trigger_mode(self, value):
        if isinstance(value, TriggerMode):
            value = value.value
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetSWTriggerMode(self._handle, set_value))

    @property
    def external_trigger_mode(self):
        """
        Decides whether the external trigger should only be used to generate the acquisition trigger, only to generate
        the trigger output, or both : Enum.

        TriggerMode.DISABLED        = 0
        TriggerMode.ACQ_ONLY        = 1
        TriggerMode.EXTOUT_ONLY     = 2
        TriggerMode.ACQ_AND_EXTOUT  = 3
        """
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetExtTriggerInputMode(self._handle, byref(return_value)))
        return TriggerMode(return_value.value)

    @external_trigger_mode.setter
    def external_trigger_mode(self, value):
        if isinstance(value, TriggerMode):
            value = value.value
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetExtTriggerInputMode(self._handle, set_value))

    @property
    def external_trigger_level(self):
        """
        The IO level of the external trigger to either TTL or NIM : Enum

        IOLevel.NIM = 0
        IOLevel.TTL = 1
        """
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetIOLevel(self._handle, byref(return_value)))
        return IOLevel(return_value.value)

    @external_trigger_level.setter
    def external_trigger_level(self, value):
        """
        Sets the IO level of the external trigger to either TTL or NIM : Enum

        IOLevel.NIM = 0
        IOLevel.TTL = 1
        """
        if isinstance(value, IOLevel):
            value = value.value
        set_value = c_uint(value)
        handle_error(_lib.CAEN_DGTZ_SetIOLevel(self._handle, set_value))

    @property
    def decimation_factor(self):
        """
        The decimation factor of the digitizer
        """
        return_value = c_int(0)
        handle_error(_lib.CAEN_DGTZ_ReadRegister(self._handle, 0x8044, byref(return_value)))
        return return_value.value

    @decimation_factor.setter
    def decimation_factor(self, value):
        # Reduce the record length with the decimation factor to retain the same time per readout
        record_length = self.record_length
        self.manual_record_length(record_length // (1 << value))
        set_value = c_int(value)
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, 0x8044, set_value))

    def get_trigger_threshold(self, channel):
        channel = c_uint(channel)
        threshold = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetChannelTriggerThreshold(self._handle, channel, byref(threshold)))
        return threshold.value

    def set_trigger_threshold(self, channel, threshold):
        channel = c_uint(channel)
        threshold = c_uint(threshold)
        handle_error(_lib.CAEN_DGTZ_SetChannelTriggerThreshold(self._handle, channel, threshold))

    def get_self_trigger(self, channel):
        """
        This function mainly applies to the digitizers running the standard oscilloscope-like firmware for waves
        digitizing, since it manages the global trigger generation and its propagation through
        the TRG-OUT connector.

        Returns
        -------
        TriggerMode : Enum
            TriggerMode.DISABLED        = 0
            TriggerMode.ACQ_ONLY        = 1
            TriggerMode.EXTOUT_ONLY     = 2
            TriggerMode.ACQ_AND_EXTOUT  = 3
        """
        return_value = c_uint(0)
        get_channel = c_uint(channel)
        handle_error(_lib.CAEN_DGTZ_GetChannelSelfTrigger(self._handle, get_channel, byref(return_value)))
        return TriggerMode(return_value.value)

    def set_self_trigger(self, channel, mode):
        """
        This function mainly applies to the digitizers running the standard oscilloscope-like firmware for waves
        digitizing, since it manages the global trigger generation and its propagation through
        the TRG-OUT connector.

        Parameters
        ----------
        channel : int
            Channel to set the self-trigger mode to.
        mode : TriggerMode
            Trigger mode to apply to channel.
            TriggerMode.DISABLED        = 0
            TriggerMode.ACQ_ONLY        = 1
            TriggerMode.EXTOUT_ONLY     = 2
            TriggerMode.ACQ_AND_EXTOUT  = 3
        """
        if isinstance(mode, TriggerMode):
            mode = mode.value
        for i in range(self.number_of_channels):
            set_channel = c_uint(1 << i)
            set_mode = c_uint(definitions.TriggerMode.DISABLED.value)
            handle_error(_lib.CAEN_DGTZ_SetChannelSelfTrigger(self._handle,
                                                              set_mode, set_channel))
        set_mode = c_uint(mode)
        set_channel = c_uint(1 << channel)
        while self.get_self_trigger(channel).value is not mode:
            handle_error(_lib.CAEN_DGTZ_SetChannelSelfTrigger(self._handle, set_mode, set_channel))

    def get_trigger_polarity(self, channel):
        """
        Gets the trigger polarity of a specified channel.

        :param channel: channel to receive polarity from
        :return: TriggerPolarity
        :rtype: Enum
        """
        get_channel = c_uint(channel)
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetTriggerPolarity(self._handle, get_channel, byref(return_value)))
        return TriggerPolarity(return_value.value)

    def set_trigger_polarity(self, channel, polarity):
        """
        Sets the trigger polarity of a specified channel.

        :param channel: channel to set the polarity of.
        :param polarity: desired polarity:
                         TriggerPolarity.ON_RISING_EDGE = 0
                         TriggerPolarity.ON_FALLING_EDGE = 1
        """
        set_channel = c_uint(channel)
        if isinstance(polarity, TriggerPolarity):
            polarity = polarity.value
        set_polarity = c_uint(polarity)
        handle_error(_lib.CAEN_DGTZ_SetTriggerPolarity(self._handle, set_channel, set_polarity))

    def get_pulse_polarity(self, channel):
        """
        Gets the pulse polarity of a specified channel.

        :param channel: channel to receive polarity from
        :return: PulsePolarity
        :rtype: Enum
        """
        get_channel = c_uint(channel)
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetChannelPulsePolarity(self._handle, get_channel, byref(return_value)))
        return TriggerPolarity(return_value.value)

    def set_pulse_polarity(self, channel, polarity):
        """
        Sets the pulse polarity of a specified channel.

        :param channel: channel to set the polarity of.
        :param polarity: desired polarity:
                         TriggerPolarity.ON_RISING_EDGE = 0
                         TriggerPolarity.ON_FALLING_EDGE = 1
        """
        set_channel = c_uint(channel)
        if isinstance(polarity, TriggerPolarity):
            polarity = polarity.value
        set_polarity = c_uint(polarity)
        handle_error(_lib.CAEN_DGTZ_SetChannelPulsePolarity(self._handle, set_channel, set_polarity))

    def get_dc_offset(self, channel):
        """
        Gets the DC offset of a specified channel.

        :param channel: channel to receive DC offset from
        :return: DC offset in percent
        :rtype: int
        """
        get_channel = c_uint(channel)
        return_value = c_uint(0)
        handle_error(_lib.CAEN_DGTZ_GetChannelDCOffset(self._handle, get_channel, byref(return_value)))
        return return_value.value * 100 / 0xFFFF

    def set_dc_offset(self, channel, offset):
        """
        Sets the DC offset (in % of available bits) of a specified channel.

        :param channel: channel to set the DC offset for
        :param offset: desired DC offset in percent
        """
        if offset > 100 or offset < 0:
            raise ValueError('DC offset out of bounds!')
        set_channel = c_uint(channel)
        set_offset = c_uint(offset * 0xFFFF // 100)
        handle_error(_lib.CAEN_DGTZ_SetChannelDCOffset(self._handle, set_channel, set_offset))

    def enable_efficient_readout(self):
        """
        Tries to set the most efficient readout mode with the least overhead based on current settings
        """
        record_length = self.record_length
        buffer_size = self.buffer_size
        self.max_num_events = max([128, buffer_size // record_length])

    def connect_device(self):
        handle_error(_lib.CAEN_DGTZ_OpenDigitizer(definitions.ConnectionType.USB.value,
                                                  self.usb_index, 0, 0, byref(self._handle)))
        # Global reset
        handle_error(_lib.CAEN_DGTZ_Reset(self._handle))
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, 0xEF24, c_uint(0)))
        # Memory reset
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, 0xEF28, c_uint(0)))

        self.board_info = self._hardware_info()
        self.buffer = pointer(c_char())

    def close(self):
        handle_error(_lib.CAEN_DGTZ_Reset(self._handle))
        handle_error(_lib.CAEN_DGTZ_CloseDigitizer(self._handle))

    def _hardware_info(self):
        board_info = definitions.BoardInfo()
        error_code = _lib.CAEN_DGTZ_GetInfo(self._handle, byref(board_info))
        if error_code is not definitions.ErrorCode.Success.value:
            raise definitions.Error(error_code)
        return board_info

    @pyqtSlot()
    def prepare_for_measurement(self):
        buffer_size = c_uint(0)
        # Allocate buffer for measurement
        handle_error(_lib.CAEN_DGTZ_MallocReadoutBuffer(self._handle, byref(self.buffer), byref(buffer_size)))
        # Start measurement
        handle_error(_lib.CAEN_DGTZ_SWStartAcquisition(self._handle))

    @pyqtSlot()
    def read_data(self, readmode=definitions.ReadMode.SLAVE_TERMINATED_READOUT_MBLT):
        """
        Tell the digitizer to start measuring "now"

        :param readmode: type of readmode:
                            SLAVE_TERMINATED_READOUT_MBLT = 0 (default)
                            SLAVE_TERMINATED_READOUT_2eVME = 1
                            SLAVE_TERMINATED_READOUT_2eSST = 2
                            POLLING_MBLT = 3
                            POLLING_2eVME = 4
                            POLLING_2eSST = 5
        :return results: array sized as array[channels][events]
        """
        self.prepare_for_measurement()
        readmode = c_uint(readmode.value)

        buffer = self.buffer
        buffer_size = c_uint(0)
        number_of_events = c_uint(4)
        event = pointer(definitions.UINT16_EVENT())
        record_length = self.record_length
        active_channels = self.active_channels

        # Allocate buffer for measurement
        handle_error(_lib.CAEN_DGTZ_AllocateEvent(self._handle, byref(event)))

        # Collect encoded data from Digitizer in buffer
        buffer_size = c_uint(0)
        while buffer_size.value == 0:
            response = (_lib.CAEN_DGTZ_ReadData(self._handle, readmode, buffer, byref(buffer_size)))
            handle_error(response)
        handle_error(_lib.CAEN_DGTZ_GetNumEvents(self._handle, buffer, buffer_size, byref(number_of_events)))
        # Decode encoded data from buffer
        results = np.full((self.number_of_channels, number_of_events.value, record_length), np.nan)
        for i in range(number_of_events.value):
            event_information = definitions.EventInfo()
            event_pointer = pointer(c_char())
            # Retrieve information about this event and set the pointer
            handle_error(_lib.CAEN_DGTZ_GetEventInfo(self._handle, buffer, buffer_size, i, byref(event_information),
                                                     byref(event_pointer)))
            # Decode the event located at the pointer and store it in 'event'
            handle_error(_lib.CAEN_DGTZ_DecodeEvent(self._handle, event_pointer, byref(event)))
            for channel_num in active_channels:
                results[channel_num][i][0:event.contents.ChSize[channel_num]] = \
                    event.contents.DataChannel[channel_num][0:event.contents.ChSize[channel_num]]
        # Free buffer for next measurement
        handle_error(_lib.CAEN_DGTZ_FreeEvent(self._handle, byref(event)))
        self.finish_measurement()
        return results

    @pyqtSlot()
    def finish_measurement(self):
        # Free buffer for next measurement
        handle_error(_lib.CAEN_DGTZ_SWStopAcquisition(self._handle))
        handle_error(_lib.CAEN_DGTZ_FreeReadoutBuffer(byref(self.buffer)))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        return '<Digitizer {}:{}>'.format(self.model, self.serial)

