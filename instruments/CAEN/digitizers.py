import time
from PyQt5.QtCore import QObject, QMutex, pyqtSlot, pyqtSignal
from ctypes import c_char, c_char_p, byref, windll, pointer, c_uint32, c_int32
import os
import numpy as np
import instruments.CAEN.definitions as definitions
from instruments.CAEN.definitions import AcqMode, IOLevel, TriggerMode, TriggerPolarity
from pathlib import Path
import logging


# Add location of digitizer dll library to path
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
        handle = c_int32(0)
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
    """ Handle class used for opening the Digitizer connection """
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
    """
    Class controlling the family of CAEN DT57xx Digitizers.

    Wraps CAEN high-level functions from CAENDigitizer.dll, adds minor functionality like a single pulse measurement.

    For more information see library manual CAEN UM1935 and the digitizer specific manuals for general operations and
    register descriptions.
    """
    def __init__(self):
        DigitizerHandle.__init__(self, None, None, None)
        self.logger = logging.getLogger('instrument.digitizer')
        self.logger.info('init digitizer')
        self._handle = c_uint32(0)
        self.board_info = None
        self.buffer = c_char_p()
        self.buffer_size = c_uint32(0)
        self.event = pointer(definitions.UINT16_EVENT())
        self.rl = 0   # parameter only used for enabling wait time in read data function

    @property
    def buffer_size_max(self):
        """ Return the maximum buffer size """
        return definitions.Buffersize[definitions.ModelNumber[self.model]] \
               - definitions.BufferCorr[definitions.ModelNumber[self.model]]

    @property
    def sample_rate(self):
        """ Return sample rate in samples/s """
        return definitions.SampleRate[definitions.ModelNumber[self.model]] * 1e6

    @property
    def record_length(self):
        """ Gets the record length """
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetRecordLength(self._handle, byref(return_value)))
        self.logger.info(f'record length = {return_value.value} samples per channel')
        return return_value.value

    @record_length.setter
    def record_length(self, value):
        """
        Sets the record length by a value between 0 and 10. The record length is determined by the following
        formula: record length = max_buffer_size/2^value. This function also calls the current post trigger size
        and resets the post trigger size to that value after changing the record length. The record length function
        automatically changes the buffer organization internally.

        :param value: between 0 and 10
        """
        if value < 0:
            value = 0
            self.logger.warning(f'specified record length too small. set to minimum value: {value}')
        elif value > 10:
            value = 10
            self.logger.warning(f'specified record length too big, set to maximum value: {value}')
        self.rl = value
        post_trigger_size = self.post_trigger_size
        buffer_size = self.buffer_size_max
        record_length = buffer_size // (1 << (10 - value))
        set_value = c_uint32(record_length)
        handle_error(_lib.CAEN_DGTZ_SetRecordLength(self._handle, set_value))
        self.logger.info(f'set record length to {record_length} samples per channel')
        self.post_trigger_size = post_trigger_size

    def manual_record_length(self, value):
        """ Sets the record length to a manual value """
        set_value = c_uint32(value)
        handle_error(_lib.CAEN_DGTZ_SetRecordLength(self._handle, set_value))
        self.logger.info(f'set record length to manual value of {value} samples')

    @property
    def post_trigger_size(self):
        """ Get/sets the post trigger size """
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetPostTriggerSize(self._handle, byref(return_value)))
        return return_value.value

    @post_trigger_size.setter
    def post_trigger_size(self, value):
        set_value = c_uint32(value)
        handle_error(_lib.CAEN_DGTZ_SetPostTriggerSize(self._handle, set_value))

    @property
    def max_num_events_blt(self):
        """ Get/Sets the maximum number of events per block transfer """
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetMaxNumEventsBLT(self._handle, byref(return_value)))
        self.logger.info(f'Max num events per block transfer = {return_value.value}')
        return return_value.value

    @max_num_events_blt.setter
    def max_num_events_blt(self, value):
        set_value = c_uint32(value)
        handle_error(_lib.CAEN_DGTZ_SetMaxNumEventsBLT(self._handle, set_value))

    @property
    def buffer_organization(self):
        """
            Get/Sets the number of buffers in which the channel memory can be divided. Number of buffers is given by
            Nb = 2^buffer code with buffer code from 0 to 10
        :return:
            Buffer code
        """
        address = 0x800c
        value = c_int32(0)
        handle_error(_lib.CAEN_DGTZ_ReadRegister(self._handle, address, byref(value)))
        self.logger.info(f'Number of buffers per channel memory = {1 << value.value}')
        return 1 << value.value

    @buffer_organization.setter
    def buffer_organization(self, set_value):
        address = 0x800c
        set_value = c_int32(set_value)
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, address, set_value))
        self.logger.info(f'Number of buffers per channel memory set to {1 << set_value.value}')

    @property
    def number_of_channels(self):
        """ Returns the number of channels this digitizer has """

        board_info = definitions.BoardInfo()
        _lib.CAEN_DGTZ_GetInfo(self._handle, byref(board_info))
        return board_info.Channels

    @property
    def adc_number_of_bits(self):
        """ Returns the number of ADC bits """
        board_info = definitions.BoardInfo()
        _lib.CAEN_DGTZ_GetInfo(self._handle, byref(board_info))
        return board_info.ADC_NBits

    @property
    def active_channels(self):
        """ List of all the active channels """

        mask = self.channel_enable_mask[2:]
        active = set()
        for i, x in enumerate(reversed(mask)):
            if int(x):
                active.add(i)
        return active

    @active_channels.setter
    def active_channels(self, channels):
        """
        Sets the active channels
        :param channels: channels to participate in measurement
        :type channels: list
        """
        mask = 0
        for channel in channels:
            mask += 1 << channel
        self.channel_enable_mask = mask

    @property
    def channel_enable_mask(self):
        """
        Get the enabled channel mask. Each enabled channel corresponds to a bit e.g. '1101' or 13 means channels
        0, 2 and 3 enabled
        """
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetChannelEnableMask(self._handle, byref(return_value)))
        return bin(return_value.value)

    @channel_enable_mask.setter
    def channel_enable_mask(self, value):
        """
        Set the enabled channels mask
        :param value: mask (bit per channel -> 13 corresponds to 1101 or channels [0, 2, 3]
        """
        set_value = c_uint32(value)
        handle_error(_lib.CAEN_DGTZ_SetChannelEnableMask(self._handle, set_value))

    def set_channel_gain(self, channel, value):
        address = 0x1028 + 0x100 * channel
        set_value = c_uint32(value)
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, address, set_value))

    def get_channel_gain(self, channel):
        address = 0x1028 + 0x100 * channel
        value = c_int32(0)
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
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetAcquisitionMode(self._handle, byref(return_value)))
        return AcqMode(return_value.value)

    @acquisition_mode.setter
    def acquisition_mode(self, value):
        if isinstance(value, AcqMode):
            value = value.value
        set_value = c_uint32(value)
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
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetSWTriggerMode(self._handle, byref(return_value)))
        return TriggerMode(return_value.value)

    @software_trigger_mode.setter
    def software_trigger_mode(self, value):
        if isinstance(value, TriggerMode):
            value = value.value
        set_value = c_uint32(value)
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
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetExtTriggerInputMode(self._handle, byref(return_value)))
        return TriggerMode(return_value.value)

    @external_trigger_mode.setter
    def external_trigger_mode(self, value):
        if isinstance(value, TriggerMode):
            value = value.value
        set_value = c_uint32(value)
        handle_error(_lib.CAEN_DGTZ_SetExtTriggerInputMode(self._handle, set_value))

    @property
    def external_trigger_level(self):
        """
        The IO level of the external trigger to either TTL or NIM : Enum

        IOLevel.NIM = 0
        IOLevel.TTL = 1
        """
        return_value = c_uint32(0)
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
        set_value = c_uint32(value)
        handle_error(_lib.CAEN_DGTZ_SetIOLevel(self._handle, set_value))

    @property
    def decimation_factor(self):
        """
        Get/Set the decimation factor of the digitizer for recording longer periods of time.

        During the acquisition, the firmware processes the digitized input waveforms calculating an averaged value of
        the “decimated” 2n consecutive samples. The self-trigger is then issued as soon as an averaged value exceeds
        the programmed threshold (see Sec. Self-Trigger). Software trigger and external trigger are not affected by
        decimation option. While the real sampling frequency does not change, the decimation effect is to change the
        data rate written into the digitizer memory. Readout data results at a sampling frequency changed according
        to the formula:

        Fd = Fs/2^decimation factor
        """
        return_value = c_int32(0)
        handle_error(_lib.CAEN_DGTZ_ReadRegister(self._handle, 0x8044, byref(return_value)))
        return return_value.value

    @decimation_factor.setter
    def decimation_factor(self, value):
        """
        Sets the decimation factor and changes record length correspondingly for longer recording times.

        During the acquisition, the firmware processes the digitized input waveforms calculating an averaged value of
        the “decimated” 2n consecutive samples. The self-trigger is then issued as soon as an averaged value exceeds
        the programmed threshold (see Sec. Self-Trigger). Software trigger and external trigger are not affected by
        decimation option. While the real sampling frequency does not change, the decimation effect is to change the
        data rate written into the digitizer memory. Readout data results at a sampling frequency changed according
        to the formula:

        Fd = Fs/2^decimation factor
        :param value: decimation factor (0 - 7)
        """
        value = 0 if value < 0 else value
        value = 7 if value > 7 else value
        record_length = self.record_length
        self.manual_record_length(record_length // (1 << value))
        set_value = c_int32(value)
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, 0x8044, set_value))

    def get_trigger_threshold(self, channel):
        channel = c_uint32(channel)
        threshold = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetChannelTriggerThreshold(self._handle, channel, byref(threshold)))
        return threshold.value

    def set_trigger_threshold(self, channel, threshold):
        channel = c_uint32(channel)
        threshold = c_uint32(threshold)
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
        return_value = c_uint32(0)
        get_channel = c_uint32(channel)
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
            set_channel = c_uint32(1 << i)
            set_mode = c_uint32(definitions.TriggerMode.DISABLED.value)
            handle_error(_lib.CAEN_DGTZ_SetChannelSelfTrigger(self._handle,
                                                              set_mode, set_channel))
        set_mode = c_uint32(mode)
        set_channel = c_uint32(1 << channel)
        while self.get_self_trigger(channel).value is not mode:
            handle_error(_lib.CAEN_DGTZ_SetChannelSelfTrigger(self._handle, set_mode, set_channel))

    def get_trigger_polarity(self, channel):
        """
        Gets the trigger polarity of a specified channel.

        :param channel: channel to receive polarity from
        :return: TriggerPolarity
        :rtype: Enum
        """
        get_channel = c_uint32(channel)
        return_value = c_uint32(0)
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
        set_channel = c_uint32(channel)
        if isinstance(polarity, TriggerPolarity):
            polarity = polarity.value
        set_polarity = c_uint32(polarity)
        handle_error(_lib.CAEN_DGTZ_SetTriggerPolarity(self._handle, set_channel, set_polarity))

    def get_pulse_polarity(self, channel):
        """
        Gets the pulse polarity of a specified channel.

        :param channel: channel to receive polarity from
        :return: PulsePolarity
        :rtype: Enum
        """
        get_channel = c_uint32(channel)
        return_value = c_uint32(0)
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
        set_channel = c_uint32(channel)
        if isinstance(polarity, TriggerPolarity):
            polarity = polarity.value
        set_polarity = c_uint32(polarity)
        handle_error(_lib.CAEN_DGTZ_SetChannelPulsePolarity(self._handle, set_channel, set_polarity))

    def get_dc_offset(self, channel: int):
        """
        Gets the DC offset of a specified channel.

        :param channel: channel to receive DC offset from
        :type channel: int
        :returns: DC offset in percent
        :rtype: int
        """
        get_channel = c_uint32(channel)
        return_value = c_uint32(0)
        handle_error(_lib.CAEN_DGTZ_GetChannelDCOffset(self._handle, get_channel, byref(return_value)))
        return return_value.value * 100 / 0xFFFF

    def set_dc_offset(self, channel, offset):
        """
        Sets the DC offset (in % of available bits) of a specified channel.

        :param channel: channel to set the DC offset for
        :type channel: int
        :param offset: desired DC offset in percent
        :type offset: int
        """
        if offset > 100 or offset < 0:
            raise ValueError('DC offset out of bounds!')
        set_channel = c_uint32(channel)
        set_offset = c_uint32(offset * 0xFFFF // 100)
        handle_error(_lib.CAEN_DGTZ_SetChannelDCOffset(self._handle, set_channel, set_offset))

    def enable_efficient_readout(self):
        """
        Set the most efficient readout mode with the least overhead based on current settings

        .. note:: Only works with multiple event measurement.
        """
        record_length = self.record_length
        buffer_size = self.buffer_size_max
        self.max_num_events_blt = max([128, buffer_size // record_length])

    def connect_device(self):
        """ Open the connection to the Digitizer. """

        handle = list_available_devices()[0]
        DigitizerHandle.__init__(self, handle.usb_index, handle.model, handle.serial)

        handle_error(_lib.CAEN_DGTZ_OpenDigitizer(definitions.ConnectionType.USB.value,
                                                  self.usb_index, 0, 0, byref(self._handle)))
        # Global reset
        handle_error(_lib.CAEN_DGTZ_Reset(self._handle))
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, 0xEF24, c_uint32(0)))
        # Memory reset
        handle_error(_lib.CAEN_DGTZ_WriteRegister(self._handle, 0xEF28, c_uint32(0)))

        self.board_info = self._hardware_info()
        self.buffer = pointer(c_char())

    def close(self):
        """ Close the Digitizer connection. """
        handle_error(_lib.CAEN_DGTZ_Reset(self._handle))
        handle_error(_lib.CAEN_DGTZ_CloseDigitizer(self._handle))

    def _hardware_info(self):
        """ Read information about the digitizer. """
        board_info = definitions.BoardInfo()
        error_code = _lib.CAEN_DGTZ_GetInfo(self._handle, byref(board_info))
        if error_code is not definitions.ErrorCode.Success.value:
            raise definitions.Error(error_code)
        return board_info

    def free_event(self):
        """ Release the event memory buffer allocated by either the DecodeEvent or AllocateEvent function. """

        self.logger.info('CAEN DT57xx frees event')
        handle_error(_lib.CAEN_DGTZ_FreeEvent(self._handle, byref(self.event)))

    def free_readout_buffer(self):
        """ Free memory allocated by the MallocReadoutBuffer function. """

        self.logger.debug('CAEN DT57xx frees memory allocated by the MallocReadoutBuffer function')
        handle_error(_lib.CAEN_DGTZ_FreeReadoutBuffer(byref(self.buffer)))

    def send_sw_trigger(self):
        """
        This function sends a Software trigger to the Digitizer. The SW trigger can be used to save an acquisition
        window on all channels at the same time and/or to generate a pulse on the Trigger Output of the board,
        according to the SW trigger mode set by the “Set” function of the Set / GetSWTriggerMode.
        """
        self.logger.info('CAEN DT57xx software trigger sent')
        handle_error(_lib.CAEN_DGTZ_SendSWtrigger(self._handle))

    def start_measurement(self):
        self.buffer_size = c_uint32(0)
        self.malloc_readout_buffer()
        self.allocate_event()
        self.sw_start_acquisition()
        time.sleep(0.001)

    @pyqtSlot()
    def finish_measurement(self):
        """ This function finishes up the measurement by stopping the acquisition and freeing all buffers. """
        self.logger.debug("finishing measurement")
        self.sw_stop_acquisition()
        self.free_event()
        self.free_readout_buffer()

    def allocate_event(self):
        """
        This function allocates the memory buffer for the decoded event data. The size of the buffer is calculated
        in order to keep the maximum event size.
        """
        self.logger.info('CAEN DT57xx allocates event')
        self.event.value = None
        handle_error(_lib.CAEN_DGTZ_AllocateEvent(self._handle, byref(self.event)))

    def get_num_events(self):
        """
        This function scans the readout buffer and gets the number of events contained in the data block previously
        read by the ReadData function. The number of events is returned in the parameter numEvents.
        """
        self.logger.debug('CAEN DT57xx scans the readout buffer and gets the number of events')
        num_events = c_int32(0)
        _lib.CAEN_DGTZ_GetNumEvents(self._handle, self.buffer, self.buffer_size, byref(num_events))
        return num_events.value

    def get_event_info(self, event_index):
        """
        This function retrieves the information (trigger time stamp, event number, channel mask, etc.) associated
        to one event contained in the readout buffer. This function reads the header of the numEvent event in the
        buffer, fills the eventInfo structure and set the data pointer EventPtr to the first word of the event
        data in the readout buffer. This pointer will be passed to the DecodeEvent function described below.

        :param event_index: index to the event, 1 for first event in buffer
        :return: evtptr: pointer to event, event_info: info about event
        """
        # self.info_stream('CAEN DT57xx retrieves event information')
        event_info = definitions.EventInfo()
        evtptr = c_char_p()
        handle_error(_lib.CAEN_DGTZ_GetEventInfo(self._handle, self.buffer, self.buffer_size, event_index,
                                                 byref(event_info), byref(evtptr)))

        return evtptr, event_info

    def decode_event(self, evtptr):
        """
        Decode an event into data.

        :param evtptr: Pointer to the event to be decoded, is returned from GetEventInfo
        :return: measurement data as [channels][samples]
        """

        self.logger.debug(f'Decode Event {evtptr}')
        handle_error(_lib.CAEN_DGTZ_DecodeEvent(self._handle, evtptr, byref(self.event)))
        number_of_channels = len(self.active_channels)
        self.logger.debug(f'digitzier decode active channels = {self.active_channels}')

        channel_size = 0
        for channel in self.active_channels:
            channel_size = self.event.contents.ChSize[channel]
            if channel_size > 0:
                break

        self.logger.debug(f'digitizer channel size = {channel_size}')
        data = np.zeros((number_of_channels, channel_size))

        for count, channel in enumerate(self.active_channels):
            data[count] = self.event.contents.DataChannel[channel][0:channel_size]
        return data

    def decode_only(self, ptr):
        handle_error(_lib.CAEN_DGTZ_DecodeEvent(self._handle, ptr, byref(self.event)))

    def read_data(self, readoutmode=definitions.ReadMode.POLLING_MBLT.value):
        """
        This function performs a block transfer of data from the digitizer to the computer. The size of the block
        to be transferred is determined by the function according to parameters set and the mode of readout.
        The block can contain one or more events. The data is transferred into the buffer memory previously
        allocated by MallocReadoutBuffer function. The function returns in bufferSize the size of the data block
        read from the card, expressed in bytes.
        """
        self.logger.debug('CAEN DT57xx Read data')
        self.buffer_size = c_uint32(0)
        readmode = c_uint32(readoutmode)
        # not pretty but without this wait for longer record lengths the readout will crash
        if 7 < self.rl < 10:
            time.sleep(0.2)
        elif self.rl == 10:
            time.sleep(0.5)
        _lib.CAEN_DGTZ_ReadData(self._handle, readmode, self.buffer, byref(self.buffer_size))
        self.logger.debug(f"ReadData self.buffersizesize.value : {self.buffer_size}")
        return self.buffer_size.value

    def read_readout_status(self):
        """
            Read the Readout Status register.
        """
        self.logger.info('Read CAEN DT57xx Acquisition Status Register')
        address = 0xEF04
        status = c_int32(0)
        handle_error(_lib.CAEN_DGTZ_ReadRegister(self._handle, address, byref(status)))
        return status.value

    def malloc_readout_buffer(self):
        """
        This function allocates the memory buffer for the data block transfer from the digitizer to the PC.
        The size of the buffer allocated is calculated by the function according to the size of the event,
        the number of enabled channels and the maximum number of events transferred by each block transfer
        (see previous function). For this reason, the function must be called after having programmed the
        digitizer, if the parameters that determine the size of the buffer change, it is necessary to free it
        by calling the FreeReadoutBuffer function and then reallocated.
        """
        self.logger.debug('CAEN DT57xx allocates memory buffer for the data block transfer')
        size = c_uint32(0)
        self.buffer.value = None  # NULL pointer
        handle_error(_lib.CAEN_DGTZ_MallocReadoutBuffer(self._handle, byref(self.buffer), byref(size)))
        pass

    def clear_data(self):
        """"
        This function clears the data stored in the buffers of the Digitizer.

        Note: generally, it is not necessary to call this function, because the digitizer automatically runs a clear
        cycle when an acquisition starts. The function can be used during an acquisition when aware that the data
        stored in memory are not interesting and not going to be read.
        """
        self.logger.info('CAEN DT57xx clearing all data in the digitizer')
        handle_error(_lib.CAEN_DGTZ_ClearData(self._handle))

    def events_stored(self):
        """
        This register contains the number of events currently stored in the Output Buffer.
        NOTE: the value of this register cannot exceed the maximum number of available buffers according to the
        register address 0x800C (max num events BLT).
        """
        self.logger.info('Read CAEN DT57xx Events Stored Register')
        address = 0x812C
        events = c_int32(0)
        handle_error(_lib.CAEN_DGTZ_ReadRegister(self._handle, address, byref(events)))
        return events.value

    def sw_start_acquisition(self):
        """
        This function starts the acquisition in a board using a software command. When the acquisition starts, the
        relevant RUN LED on the front panel lights up. It is worth noticing that in case of multiple board systems,
        the software start doesn’t allow the digitizer to start synchronously. For this purpose, it is necessary
        to use to start the acquisition using aphysical signal, such as the S-IN or GPI as well as the
        TRG-IN-TRG-OUT Daisy chain. Please refer to Digitizer manual for more details on this issue.
        """
        self.logger.debug('DT57XX Started acquisition with software command')
        handle_error(_lib.CAEN_DGTZ_SWStartAcquisition(self._handle))

    def sw_stop_acquisition(self):
        """ This function stops the acquisition in a board using a software command. """

        self.logger.debug('DT57XX Stopped acquisition with software command')
        handle_error(_lib.CAEN_DGTZ_SWStopAcquisition(self._handle))

    def measurement_single_event(self):
        """
        Perform a measurement of a single event. Steps involved: Allocate memory, start acquisition,
        check for data, read data, decode data, stop acquisition, free memory.

        :return: data [channels][samples]
        """

        self.start_measurement()
        # check if data is present, otherwise wait
        while self.read_readout_status() & 1 == 0:
            time.sleep(0.001)
        # not pretty but necessary wait for longer record times to prevent digitizer from crashing (only for DT5724)
        if 7 < self.rl < 10:
            time.sleep(0.2)
        elif self.rl == 10:
            time.sleep(0.4)
        self.read_data(definitions.ReadMode.POLLING_MBLT.value)
        evtptr, _ = self.get_event_info(0)
        data = self.decode_event(evtptr)
        self.finish_measurement()

        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        return f'<Digitizer {self.model}:{self.serial}>'


if __name__ == '__main__':
    import yaml
    import logging.config
    pathlogging = Path(__file__).parent.parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
