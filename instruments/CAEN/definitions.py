from ctypes import *
from enum import Enum
import unicodedata

MAX_UINT16_CHANNEL_SIZE = 64
MAX_UINT8_CHANNEL_SIZE = 8


# /******************************************************************************
# * 
# * CAEN SpA - Computing Division
# * Via Vetraia, 11 - 55049 - Viareggio ITALY
# * +390594388398 - www.caen.it
# *
# ***************************************************************************//**
# * \note TERMS OF USE:
# * This program is free software; you can redistribute it and/or modify it under
# * the terms of the GNU General Public License as published by the Free Software
# * Foundation. This program is distributed in the hope that it will be useful, 
# * but WITHOUT ANY WARRANTY; without even the implied warranty of 
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. The user relies on the 
# * software, documentation and results solely at his own risk.
# *
# * \file     CAENDigitizerType.h
# * \brief    CAEN - Digitizer Library types definition
# * \author   Alberto Lucchesi, Giovanni Bianchi (support.computing@caen.it)
# *
# * This library provide functions, structures and definitions for the CAEN
# * digitizer family
# ******************************************************************************/



class UINT16_EVENT(Structure):
    _fields_ = [
        ("ChSize", c_uint * MAX_UINT16_CHANNEL_SIZE),  # the number of samples stored in DataChannel array
        ("DataChannel", POINTER(c_ushort) * MAX_UINT16_CHANNEL_SIZE)]  # the array of ChSize samples


class EventInfo(Structure):
    _fields_ = [
        ("EventSize", c_uint),
        ("BoardId", c_uint),
        ("Pattern", c_uint),
        ("ChannelMask", c_uint),
        ("EventCounter", c_uint),
        ("TriggerTimeTag", c_uint)]


# ConnectionType
class ConnectionType(Enum):
    USB = 0
    OpticalLink = 1


class ModelNumber(Enum):
    V1724 = 0  # !< \brief The board is V1724  */
    V1721 = 1  # !< \brief The board is V1721  */
    V1731 = 2  # !< \brief The board is V1731  */
    V1720 = 3  # !< \brief The board is V1720  */
    V1740 = 4  # !< \brief The board is V1740  */
    V1751 = 5  # !< \brief The board is V1751  */
    DT5724F = 6  # !< \brief The board is DT5724 */
    DT5721 = 7  # !< \brief The board is DT5721 */
    DT5731 = 8  # !< \brief The board is DT5731 */
    DT5720 = 9  # !< \brief The board is DT5720 */
    DT5740 = 10  # !< \brief The board is DT5740 */
    DT5751 = 11  # !< \brief The board is DT5751 */
    N6724 = 12  # !< \brief The board is N6724  */
    N6721 = 13  # !< \brief The board is N6721  */
    N6731 = 14  # !< \brief The board is N6731  */
    N6720 = 15  # !< \brief The board is N6720  */
    N6740 = 16  # !< \brief The board is N6740  */
    N6751 = 17  # !< \brief The board is N6751  */
    DT5742 = 18  # !< \brief The board is DT5742 */
    N6742 = 19  # !< \brief The board is N6742  */
    V1742 = 20  # !< \brief The board is V1742  */
    DT5780 = 21  # !< \brief The board is DT5780 */
    N6780 = 22  # !< \brief The board is N6780  */
    V1780 = 23  # !< \brief The board is V1780  */
    DT5761 = 24  # !< \brief The board is DT5761 */
    N6761 = 25  # !< \brief The board is N6761  */
    V1761 = 26  # !< \brief The board is V1761  */
    DT5743 = 27  # !< \brief The board is DT5743 */
    N6743 = 28  # !< \brief The board is N6743  */
    V1743 = 29  # !< \brief The board is V1743  */
    DT5730 = 30  # !< \brief The board is DT5730 */
    N6730 = 31  # !< \brief The board is N6730  */
    V1730 = 32  # !< \brief The board is V1730  */
    DT5790 = 33  # !< \brief The board is DT5790 */
    N6790 = 34  # !< \brief The board is N6790  */
    V1790 = 35  # !< \brief The board is V1790  */
    DT5781 = 36  # !< \brief The board is DT5781 */
    N6781 = 37  # !< \brief The board is N6781  */
    V1781 = 38  # !< \brief The board is V1781  */
    DT5725 = 39  # !< \brief The board is DT5725 */
    N6725 = 40  # !< \brief The board is N6725  */
    V1725 = 41  # !< \brief The board is V1725  */


Buffersize = {ModelNumber.DT5724F: 4096000,
              ModelNumber.DT5730: 655360,
              ModelNumber.DT5761: 7168000}

BufferCorr = {ModelNumber.DT5724F: 0,
              ModelNumber.DT5730: 10,
              ModelNumber.DT5761: 0}

SampleRate = {ModelNumber.DT5724F: 100,
              ModelNumber.DT5730: 500,
              ModelNumber.DT5761: 4000}

mu = unicodedata.lookup('greek small letter mu')

TIMERANGES = {'DT5724F': [f'40 {mu}s', f'80 {mu}s', f'160 {mu}s', f'320 {mu}s', f'640 {mu}s', f'1280 {mu}s', '2.5 ms',
                          '5 ms', '10 ms', '20 ms', '40 ms'],
              'DT5730': [f'1.2 {mu}s', f'2.4 {mu}s', f'5 {mu}s', f'10 {mu}s', f'20 {mu}s', f'40 {mu}s', f'80 {mu}s',
                         f'160 {mu}s', f'320 {mu}s', f'640 {mu}s', '1.2 ms']}

COMPRESSIONFACTORS = {'DT5724F': {'50 ns': 5, '100 ns': 10, '200 ns': 20, '500 ns': 50, f'1 {mu}s': 100,
                                  f'2 {mu}s': 200, f'5{mu}s': 500, f'10 {mu}s': 1000, f'20 {mu}s': 2000,
                                  f'40 {mu}s': 4000},
                      'DT5730': {'8 ns': 4, '16 ns': 8, '32 ns': 16, '64 ns': 32, '128 ns': 64, '256 ns': 128,
                                 '640 ns': 320, f'1.2 {mu}s': 640}}


class ModelInfo:
    ModelName = ""
    Model = 0
    nChannels = 0
    sampleRate = 0
    ADC_NBits = 0
    bufferSize = 0
    bufferCorr = 0

    def __str__(self):
        info = ["\n\tModel name  \t\t: {}\n".format(self.ModelName),
                "\tModel number\t\t: {}\n".format(self.Model),
                "\tNumber of Channels\t: {}\n".format(self.nChannels),
                "\tSample Rate  \t\t: {}[MHz]\n".format(self.sampleRate),
                "\tBuffer size  \t\t: {}\n".format(self.bufferSize),
                "\tNumber of ADC bits\t: {}".format(self.ADC_NBits)]

        return ''.join(info)


class BoardInfo(Structure):
    _fields_ = [
        ("ModelName", c_char * 12),
        ("Model", c_uint32),
        ("Channels", c_uint32),
        ("FormFactor", c_uint32),
        ("FamilyCode", c_uint32),
        ("ROC_FirmwareRel", c_char * 20),
        ("AMC_FirmwareRel", c_char * 40),
        ("SerialNumber", c_uint32),
        ("MezzanineSerNum", c_char * 32),
        ("PCB_Revision", c_uint32),
        ('ADC_NBits', c_uint32),
        ('SAMCorrectionDataLoaded', c_uint32),
        ("CommHandle", c_int),
        ("VMEHandle", c_int),
        ("License", c_char * 17)]

    def __str__(self):
        info = ["Model name\t\t: {}\n".format(self.ModelName),
                "Model number\t\t: {}\n".format(self.Model),
                "Number of Channels\t: {}\n".format(self.Channels),
                "SerialNumber\t\t: {}\n".format(self.SerialNumber),
                "Number of ADC bits\t: {}".format(self.ADC_NBits)]

        return ''.join(info)


class ErrorCode(Enum):
    Success = 0  # Operation completed successfully             */
    CommError = -1  # Communication error                          */
    GenericError = -2  # Unspecified error                            */
    InvalidParam = -3  # Invalid parameter                            */
    InvalidLinkType = -4  # Invalid Link Type                            */
    InvalidHandle = -5  # Invalid device handle                        */
    MaxDevicesError = -6  # Maximum number of devices exceeded           */
    BadBoardType = -7  # The operation is not allowed on this type of board           */
    BadInterruptLev = -8  # The interrupt level is not allowed            */
    BadEventNumber = -9  # The event number is bad                          */
    ReadDeviceRegisterFail = -10  # Unable to read the registry                     */
    WriteDeviceRegisterFail = -11  # Unable to write into the registry                */
    InvalidChannelNumber = -13  # The channel number is invalid                 */
    ChannelBusy = -14  # The Channel is busy                               */
    FPIOModeInvalid = -15  # Invalid FPIO Mode                                */
    WrongAcqMode = -16  # Wrong acquisition mode                        */
    FunctionNotAllowed = -17  # This function is not allowed for this module    */
    Timeout = -18  # Communication Timeout                            */
    InvalidBuffer = -19  # The buffer is invalid                         */
    EventNotFound = -20  # The event is not found                        */
    InvalidEvent = -21  # The event is invalid                            */
    OutOfMemory = -22  # Out of memory                                    */
    CalibrationError = -23  # Unable to calibrate the board                    */
    DigitizerNotFound = -24  # Unable to open the digitizer                    */
    DigitizerAlreadyOpen = -25  # The Digitizer is already open                    */
    DigitizerNotReady = -26  # The Digitizer is not ready to operate            */
    InterruptNotConfigured = -27  # The Digitizer has not the IRQ configured            */
    DigitizerMemoryCorrupted = -28  # The digitizer flash memory is corrupted        */
    DPPFirmwareNotSupported = -29  # The digitizer dpp firmware is not supported in this lib version */
    InvalidLicense = -30  # Invalid Firmware License */
    InvalidDigitizerStatus = -31  # The digitizer is found in a corrupted status */
    UnsupportedTrace = -32  # The given trace is not supported by the digitizer */
    InvalidProbe = -33  # The given probe is not supported for the given digitizer's trace */
    UnsupportedBaseAddress = -34  # The Base Address is not supported, it's a Desktop device?        */

    NotYetImplemented = -99  # The function is not yet implemented            */


class Error(Exception):
    """Exception raised for errors caused within digitizer communication

        Attributes:
            errorcode -- error code provided by digitizer
    """
    msg = ["Operation completed successfully",
           "Communication error",
           "Unspecified error",
           "Invalid parameter",
           "Invalid Link Type",
           "Invalid device handle",
           "Maximum number of devices exceeded",
           "The operation is not allowed on this type of board",
           "The interrupt level is not allowed",
           "The event number is bad",
           "Unable to read the registry ",
           "Unable to write into the registry",
           "The channel number is invalid",
           "The Channel is busy",
           "Invalid FPIO Mode",
           "Wrong acquisition mode",
           "This function is not allowed for this module",
           "Communication Timeout",
           "The buffer is invalid",
           "The event is not found",
           "The event is invalid",
           "Out of memory",
           "Unable to calibrate the board ",
           "Unable to open the digitizer",
           "The Digitizer is already open",
           "The Digitizer is not ready to operate",
           "The Digitizer has not the IRQ configured",
           "The digitizer flash memory is corrupted",
           "The digitizer dpp firmware is not supported in this lib version",
           "Invalid Firmware License",
           "The digitizer is found in a corrupted status",
           "The given trace is not supported by the digitizer",
           "The given probe is not supported for the given digitizer's trace",
           "The Base Address is not supported, it's a Desktop device?"]

    def __init__(self, index):
        self.index = index
        Exception.__init__(self, self.msg[abs(index)])

    def message(self):
        return self.msg[abs(self.index)]


class AcqMode(Enum):
    SW_CONTROLLED = 0
    S_IN_CONTROLLED = 1
    FIRST_TRG_CONTROLLED = 2
    LVDS_CONTROLLED = 3


class Triggersource(Enum):
    EXTERNAL = 0
    SELF = 1
    SOFTWARE = 2


class TriggerMode(Enum):
    DISABLED = 0
    EXTOUT_ONLY = 2
    ACQ_ONLY = 1
    ACQ_AND_EXTOUT = 3


class TriggerPolarity(Enum):
    ON_RISING_EDGE = 0
    ON_FALLING_EDGE = 1


class PulsePolarity(Enum):
    POSITIVE = 0
    NEGATIVE = 1


class ReadMode(Enum):
    SLAVE_TERMINATED_READOUT_MBLT = 0
    SLAVE_TERMINATED_READOUT_2eVME = 1
    SLAVE_TERMINATED_READOUT_2eSST = 2
    POLLING_MBLT = 3
    POLLING_2eVME = 4
    POLLING_2eSST = 5


class IOLevel(Enum):
    NIM = 0
    TTL = 1
# } CAEN_DGTZ_IOLevel_t;
# 
# MAX_UINT16_CHANNEL_SIZE = 64
# MAX_UINT8_CHANNEL_SIZE  =  8
# MAX_DT5743_GROUP_SIZE   =  4
# MAX_LICENSE_DIGITS      =  8
# MAX_LICENSE_LENGTH      = (MAX_LICENSE_DIGITS * 2 + 1) 
# 
# 
# /******************************************************************************
# * Digitizer Registers Address Map 
# ******************************************************************************/
# 
#   CAEN_DGTZ_MULTI_EVENT_BUFFER                            (0x0000)
#   CAEN_DGTZ_SAM_EEPROM_ACCESS                             (0x100C)
#   CAEN_DGTZ_CHANNEL_ZS_THRESHOLD_BASE_ADDRESS             (0x1024)
#   CAEN_DGTZ_CHANNEL_ZS_NSAMPLE_BASE_ADDRESS               (0x1028)
#   CAEN_DGTZ_CHANNEL_THRESHOLD_BASE_ADDRESS                (0x1080)
#   CAEN_DGTZ_CHANNEL_OV_UND_TRSH_BASE_ADDRESS              (0x1084)
#   CAEN_DGTZ_CHANNEL_STATUS_BASE_ADDRESS                   (0x1088)
#   CAEN_DGTZ_CHANNEL_AMC_FPGA_FW_BASE_ADDRESS              (0x108C)
#   CAEN_DGTZ_CHANNEL_BUFFER_OCC_BASE_ADDRESS               (0x1094)
#   CAEN_DGTZ_CHANNEL_DAC_BASE_ADDRESS                      (0x1098)
#   CAEN_DGTZ_CHANNEL_GROUP_V1740_BASE_ADDRESS              (0x10A8)
#   CAEN_DGTZ_GROUP_FASTTRG_THR_V1742_BASE_ADDRESS          (0x10D4)
#   CAEN_DGTZ_GROUP_FASTTRG_DCOFFSET_V1742_BASE_ADDRESS     (0x10DC)
#   CAEN_DGTZ_DRS4_FREQUENCY_REG                            (0x10D8)
# 
#   CAEN_DGTZ_SAM_ENABLE_PULSE_REG                          (0x102C)
#   CAEN_DGTZ_SAM_TRIGGER_GATE_REG                          (0x1038)
#   CAEN_DGTZ_SAM_FREQUENCY_REG                             (0x1040)
#   CAEN_DGTZ_SAM_CHARGE_TRESHOLD_CH0                       (0x1048)
#   CAEN_DGTZ_SAM_CHARGE_TRESHOLD_CH1                       (0x104C)
#   CAEN_DGTZ_SAM_TRIGGER_REG_ADD                           (0x103C)
#   CAEN_DGTZ_SAM_FREQUENCY_REG_WRITE                       (0x1040)
#   CAEN_DGTZ_SAM_CHARGE_LENGTH_CH0                         (0x1080)
#   CAEN_DGTZ_SAM_CHARGE_LENGTH_CH1                         (0x10A0)
#   CAEN_DGTZ_SAM_REG_ADD                                   (0x1084)
#   CAEN_DGTZ_SAM_REG_VALUE                                 (0x1028)
#   CAEN_DGTZ_SAM_DAC_SPI_DATA_ADD                          (0x1054)
#   CAEN_DGTZ_SAM_START_CELL_CH0                            (0x1058)
#   CAEN_DGTZ_SAM_START_CELL_CH1                            (0x10A4)
#   CAEN_DGTZ_SAM_CTRL_ADD                                  (0x1070)
#   CAEN_DGTZ_SAM_EEPROM_WP_ADD                             (0x1078)
#   CAEN_DGTZ_SAM_START_ACQ_ADD                             (0x1018)
#   CAEN_DGTZ_SAM_RESET_ACQ_ADD                             (0x105C)
#   CAEN_DGTZ_SAM_NB_OF_COLS_2_READ_ADD                     (0x1044)
#   CAEN_DGTZ_SAM_POST_TRIGGER_ADD                          (0x1030)
#   CAEN_DGTZ_SAM_PULSE_PATTERN_ADD                         (0x1034) 
#   CAEN_DGTZ_SAM_RATE_COUNTERS_CH0                         (0x106C)
#   CAEN_DGTZ_SAM_RATE_COUNTERS_CH1                         (0x1094)
# 
#   CAEN_DGTZ_BROAD_CH_CTRL_ADD                             (0x8000)
#   CAEN_DGTZ_BROAD_CH_CONFIGBIT_SET_ADD                    (0x8004)
#   CAEN_DGTZ_BROAD_CH_CLEAR_CTRL_ADD                       (0x8008)
#   CAEN_DGTZ_BROAD_NUM_BLOCK_ADD                           (0x800C)
#   CAEN_DGTZ_CUSTOM_SIZE_REG                               (0x8020)
#   CAEN_DGTZ_DPP_NUM_EVENTS_PER_AGGREGATE                  (0x8034)
#   CAEN_DGTZ_DRS4_FREQUENCY_REG_WRITE                      (0x80D8)
#   CAEN_DGTZ_SAM_BROAD_FREQUENCY_REG_WRITE                 (0x8040)
#   CAEN_DGTZ_SAM_BROAD_REG_ADD                             (0x8084)
#   CAEN_DGTZ_SAM_BROAD_REG_VALUE                           (0x8028)
#   CAEN_DGTZ_SAM_BROAD_DAC_SPI_DATA_ADD                    (0x8054)
#   CAEN_DGTZ_SAM_BROAD_CTRL_ADD                            (0x8070)
#   CAEN_DGTZ_SAM_BROAD_PRETRIGGER_ADD                      (0x8074) 
#   CAEN_DGTZ_SAM_BROAD_START_ACQ_ADD                       (0x8018)
#   CAEN_DGTZ_SAM_BROAD_RESET_ACQ_ADD                       (0x805C)
#   CAEN_DGTZ_DECIMATION_ADD				                (0x8044)
#   CAEN_DGTZ_SAM_BROAD_NB_OF_COLS_2_READ_ADD               (0x8044)
#   CAEN_DGTZ_SAM_BROAD_POST_TRIGGER_ADD                    (0x8030)
#   CAEN_DGTZ_SAM_BROAD_PBK_RESET                           (0x8010)
#   CAEN_DGTZ_SAM_BROAD_PULSE_CHANNELS                      (0x801C)
#   CAEN_DGTZ_SAM_START_RATE_COUNTERS                       (0x8020)
#   CAEN_DGTZ_SAM_BROAD_CHIP_RESET                          (0x807C)
# 
# 
#   CAEN_DGTZ_ACQ_CONTROL_ADD                               (0x8100)
#   CAEN_DGTZ_ACQ_STATUS_ADD                                (0x8104)
#   CAEN_DGTZ_SW_TRIGGER_ADD                                (0x8108)
#   CAEN_DGTZ_TRIGGER_SRC_ENABLE_ADD                        (0x810C)
#   CAEN_DGTZ_FP_TRIGGER_OUT_ENABLE_ADD                     (0x8110)
#   CAEN_DGTZ_POST_TRIG_ADD                                 (0x8114)               
#   CAEN_DGTZ_FRONT_PANEL_IO_ADD                            (0x8118)
#   CAEN_DGTZ_FRONT_PANEL_IO_CTRL_ADD                       (0x811C)       
#   CAEN_DGTZ_CH_ENABLE_ADD                                 (0x8120)            
#   CAEN_DGTZ_FW_REV_ADD                                    (0x8124)           
#   CAEN_DGTZ_DOWNSAMPLE_FACT_ADD                           (0x8128)               
#   CAEN_DGTZ_EVENT_STORED_ADD                              (0x812C)        
#   CAEN_DGTZ_MON_SET_ADD                                   (0x8138)
#   CAEN_DGTZ_SYNC_CMD                                      (0x813C)
#   CAEN_DGTZ_BOARD_INFO_ADD                                (0x8140)
#   CAEN_DTGZ_EVENT_SIZE_ADD                                (0x814C)
#   CAEN_DGTZ_MON_MODE_ADD                                  (0x8144)
#   CAEN_DGTZ_ANALOG_MON_ADD                                (0x8150)
#   CAEN_DGTZ_TRIGGER_VETO_ADD                              (0x817C)
# 
#   CAEN_DGTZ_VME_CONTROL_ADD                               (0xEF00)                
#   CAEN_DGTZ_VME_STATUS_ADD                                (0xEF04)
#   CAEN_DGTZ_BOARD_ID_ADD                                  (0xEF08)
#   CAEN_DGTZ_MCST_CBLT_ADD_CTRL_ADD                        (0xEF0C)
#   CAEN_DGTZ_RELOCATION_ADDRESS_ADD                        (0xEF10)
#   CAEN_DGTZ_INT_STATUS_ID_ADD                             (0xEF14)
#   CAEN_DGTZ_INT_EVENT_NUM_ADD                             (0xEF18)
#   CAEN_DGTZ_BLT_EVENT_NUM_ADD                             (0xEF1C)
#   CAEN_DGTZ_SCRATCH_ADD                                   (0xEF20)
#   CAEN_DGTZ_SW_RESET_ADD                                  (0xEF24)
#   CAEN_DGTZ_SW_CLEAR_ADD                                  (0xEF28)
#   CAEN_DGTZ_FLASH_EN_ADD                                  (0xEF2C)
#   CAEN_DGTZ_FLASH_DATA_ADD                                (0xEF30)
#   CAEN_DGTZ_RELOAD_CONFIG_ADD                             (0xEF34)
# 
#   CAEN_DGTZ_ROM_CHKSUM_ADD                                (0xF000)
#   CAEN_DGTZ_ROM_CHKSUM_LEN_2_ADD                          (0xF004)
#   CAEN_DGTZ_ROM_CHKSUM_LEN_1_ADD                          (0xF008)
#   CAEN_DGTZ_ROM_CHKSUM_LEN_0_ADD                          (0xF00C)
#   CAEN_DGTZ_ROM_CONST_2_ADD                               (0xF010)
#   CAEN_DGTZ_ROM_CONST_1_ADD                               (0xF014)
#   CAEN_DGTZ_ROM_CONST_0_ADD                               (0xF018)
#   CAEN_DGTZ_ROM_C_CODE_ADD                                (0xF01C)
#   CAEN_DGTZ_ROM_R_CODE_ADD                                (0xF020)
#   CAEN_DGTZ_ROM_OUI_2_ADD                                 (0xF024)
#   CAEN_DGTZ_ROM_OUI_1_ADD                                 (0xF028)
#   CAEN_DGTZ_ROM_OUI_0_ADD                                 (0xF02C)
#   CAEN_DGTZ_ROM_VERSION_ADD                               (0xF030)
#   CAEN_DGTZ_ROM_BOARD_ID_2_ADD                            (0xF034)
#   CAEN_DGTZ_ROM_BOARD_ID_1_ADD                            (0xF038)
#   CAEN_DGTZ_ROM_BOARD_ID_0_ADD                            (0xF03C)
#   CAEN_DGTZ_ROM_REVISION_3_ADD                            (0xF040)
#   CAEN_DGTZ_ROM_REVISION_2_ADD                            (0xF044)
#   CAEN_DGTZ_ROM_REVISION_1_ADD                            (0xF048)
#   CAEN_DGTZ_ROM_REVISION_0_ADD                            (0xF04C)
#   CAEN_DGTZ_ROM_SERIAL_1_ADD                              (0xF080)
#   CAEN_DGTZ_ROM_SERIAL_0_ADD                              (0xF084)
#   CAEN_DGTZ_ROM_VCXO_TYPE_ADD                             (0xF088)
# 
# 
# // INDIVIDUAL CHANNEL ADDRESSING
#   CAEN_DGTZ_InputDCOffsetReg_Ch(x)      (0x1098 | ((x)<<8)) ///< Input DC offset adjust Register Indiv. Address 
#   CAEN_DGTZ_ChannelFWRevisionReg_Ch(x)  (0x108C | ((x)<<8)) ///< Channel FW Revision Register Indiv. Address 
#   CAEN_DGTZ_DPP1Reg_Ch(x)               (0x1024 | ((x)<<8)) ///< DPP1 Param Register Indiv. Address
#   CAEN_DGTZ_DPP2Reg_Ch(x)               (0x1028 | ((x)<<8)) ///< DPP2 Param Register Indiv. Address
#   CAEN_DGTZ_DPP3Reg_Ch(x)               (0x102C | ((x)<<8)) ///< DPP3 Param Register Indiv. Address
# 
# // FIRMWARE CODES
#   STANDARD_FW_CODE      (0x00)    // The code for the Standard Firmware
#   V1724_DPP_PHA_CODE    (0x80)    // The code for the DPP-PHA for x724 boards
#   V1720_DPP_CI_CODE     (0x82)    // The code for the DPP-CI for x720 boards
#   V1720_DPP_PSD_CODE    (0x83)    // The code for the DPP-PSD for x720 boards
#   V1751_DPP_PSD_CODE    (0x84)    // The code for the DPP-PSD for x751 boards
#   V1751_DPP_ZLE_CODE    (0x85)    // The code for the DPP-ZLE for x751 boards
#   V1743_DPP_CI_CODE     (0x86)    // The code for the DPP-PSD for x743 boards
#   V1740_DPP_QDC_CODE    (0x87)    // The code for the DPP-QDC for x740 boards
#   V1730_DPP_PSD_CODE    (0x88)    // The code for the DPP-PSD for x730 boards
#   V1730_DPP_PHA_CODE    (0x8B)    // The code for the DPP-PHA for x730 boards
#   V1730_DPP_ZLE_CODE    (0x8C)    // The code for the DPP-ZLE for x730 boards
#   V1730_DPP_DAW_CODE    (0x8D)    // The code for the DPP-DAW for x730 boards
# 
# /*###########################################################################*/
# /*
# ** ErrorCode
# */
# /*###########################################################################*/
# typedef enum CAEN_DGTZ_ErrorCode {
# CAEN_DGTZ_Success                       = 0L,    /* Operation completed successfully             */
# CAEN_DGTZ_CommError                     = -1L,    /* Communication error                          */
# CAEN_DGTZ_GenericError                  = -2L,    /* Unspecified error                            */
# CAEN_DGTZ_InvalidParam                  = -3L,    /* Invalid parameter                            */
# CAEN_DGTZ_InvalidLinkType               = -4L,    /* Invalid Link Type                            */
# CAEN_DGTZ_InvalidHandle                 = -5L,    /* Invalid device handle                        */
# CAEN_DGTZ_MaxDevicesError               = -6L,    /* Maximum number of devices exceeded           */
# CAEN_DGTZ_BadBoardType                  = -7L,    /* The operation is not allowed on this type of board           */
# CAEN_DGTZ_BadInterruptLev               = -8L,    /* The interrupt level is not allowed            */
# CAEN_DGTZ_BadEventNumber                = -9L,    /* The event number is bad                          */
# CAEN_DGTZ_ReadDeviceRegisterFail        = -10L,   /* Unable to read the registry                     */
# CAEN_DGTZ_WriteDeviceRegisterFail       = -11L,   /* Unable to write into the registry                */
# CAEN_DGTZ_InvalidChannelNumber          = -13L,   /* The channel number is invalid                 */
# CAEN_DGTZ_ChannelBusy                   = -14L,   /* The Channel is busy                               */
# CAEN_DGTZ_FPIOModeInvalid               = -15L,   /* Invalid FPIO Mode                                */
# CAEN_DGTZ_WrongAcqMode                  = -16L,   /* Wrong acquisition mode                        */
# CAEN_DGTZ_FunctionNotAllowed            = -17L,   /* This function is not allowed for this module    */
# CAEN_DGTZ_Timeout                       = -18L,   /* Communication Timeout                            */
# CAEN_DGTZ_InvalidBuffer                 = -19L,   /* The buffer is invalid                         */
# CAEN_DGTZ_EventNotFound                 = -20L,   /* The event is not found                        */
# CAEN_DGTZ_InvalidEvent                  = -21L,   /* The vent is invalid                            */
# CAEN_DGTZ_OutOfMemory                   = -22L,   /* Out of memory                                    */
# CAEN_DGTZ_CalibrationError              = -23L,   /* Unable to calibrate the board                    */
# CAEN_DGTZ_DigitizerNotFound             = -24L,   /* Unable to open the digitizer                    */
# CAEN_DGTZ_DigitizerAlreadyOpen          = -25L,   /* The Digitizer is already open                    */    
# CAEN_DGTZ_DigitizerNotReady             = -26L,   /* The Digitizer is not ready to operate            */    
# CAEN_DGTZ_InterruptNotConfigured        = -27L,   /* The Digitizer has not the IRQ configured            */
# CAEN_DGTZ_DigitizerMemoryCorrupted      = -28L,   /* The digitizer flash memory is corrupted        */
# CAEN_DGTZ_DPPFirmwareNotSupported       = -29L,   /* The digitizer dpp firmware is not supported in this lib version */
# CAEN_DGTZ_InvalidLicense                = -30L,   /* Invalid Firmware License */
# CAEN_DGTZ_InvalidDigitizerStatus        = -31L,   /* The digitizer is found in a corrupted status */
# CAEN_DGTZ_UnsupportedTrace              = -32L,   /* The given trace is not supported by the digitizer */
# CAEN_DGTZ_InvalidProbe                  = -33L,   /* The given probe is not supported for the given digitizer's trace */
# CAEN_DGTZ_UnsupportedBaseAddress		= -34L,   /*  The Base Address is not supported, it's a Desktop device?		*/ 
# 
# CAEN_DGTZ_NotYetImplemented             = -99L,   /* The function is not yet implemented            */
# 
# }CAEN_DGTZ_ErrorCode; 
# 
#   CAEN_DGTZ_MAX_CHANNEL   MAX_V1730_CHANNEL_SIZE  /*!< \brief The number of channels */
# 
# 
# 
# 
# /* Digitizers Model */
# typedef enum
# {
#     CAEN_DGTZ_V1724     =0L,    /*!< \brief The board is V1724  */
#     CAEN_DGTZ_V1721     =1L,    /*!< \brief The board is V1721  */
#     CAEN_DGTZ_V1731     =2L,    /*!< \brief The board is V1731  */
#     CAEN_DGTZ_V1720     =3L,    /*!< \brief The board is V1720  */
#     CAEN_DGTZ_V1740     =4L,    /*!< \brief The board is V1740  */
#     CAEN_DGTZ_V1751     =5L,    /*!< \brief The board is V1751  */
#     CAEN_DGTZ_DT5724    =6L,    /*!< \brief The board is DT5724 */
#     CAEN_DGTZ_DT5721    =7L,    /*!< \brief The board is DT5721 */
#     CAEN_DGTZ_DT5731    =8L,    /*!< \brief The board is DT5731 */
#     CAEN_DGTZ_DT5720    =9L,    /*!< \brief The board is DT5720 */
#     CAEN_DGTZ_DT5740    =10L,   /*!< \brief The board is DT5740 */
#     CAEN_DGTZ_DT5751    =11L,   /*!< \brief The board is DT5751 */
#     CAEN_DGTZ_N6724     =12L,   /*!< \brief The board is N6724  */
#     CAEN_DGTZ_N6721     =13L,   /*!< \brief The board is N6721  */
#     CAEN_DGTZ_N6731     =14L,   /*!< \brief The board is N6731  */
#     CAEN_DGTZ_N6720     =15L,   /*!< \brief The board is N6720  */
#     CAEN_DGTZ_N6740     =16L,   /*!< \brief The board is N6740  */
#     CAEN_DGTZ_N6751     =17L,   /*!< \brief The board is N6751  */
#     CAEN_DGTZ_DT5742    =18L,   /*!< \brief The board is DT5742 */
#     CAEN_DGTZ_N6742     =19L,   /*!< \brief The board is N6742  */
#     CAEN_DGTZ_V1742     =20L,   /*!< \brief The board is V1742  */
#     CAEN_DGTZ_DT5780    =21L,   /*!< \brief The board is DT5780 */
#     CAEN_DGTZ_N6780     =22L,   /*!< \brief The board is N6780  */
#     CAEN_DGTZ_V1780     =23L,   /*!< \brief The board is V1780  */
#     CAEN_DGTZ_DT5761    =24L,   /*!< \brief The board is DT5761 */
#     CAEN_DGTZ_N6761     =25L,   /*!< \brief The board is N6761  */
#     CAEN_DGTZ_V1761     =26L,   /*!< \brief The board is V1761  */
#     CAEN_DGTZ_DT5743    =27L,   /*!< \brief The board is DT5743 */
#     CAEN_DGTZ_N6743     =28L,   /*!< \brief The board is N6743  */
#     CAEN_DGTZ_V1743     =29L,   /*!< \brief The board is V1743  */
#     CAEN_DGTZ_DT5730    =30L,   /*!< \brief The board is DT5730 */
#     CAEN_DGTZ_N6730     =31L,   /*!< \brief The board is N6730  */
#     CAEN_DGTZ_V1730     =32L,   /*!< \brief The board is V1730  */
#     CAEN_DGTZ_DT5790    =33L,   /*!< \brief The board is DT5790 */
#     CAEN_DGTZ_N6790     =34L,   /*!< \brief The board is N6790  */
#     CAEN_DGTZ_V1790     =35L,   /*!< \brief The board is V1790  */
#     CAEN_DGTZ_DT5781    =36L,   /*!< \brief The board is DT5781 */
#     CAEN_DGTZ_N6781     =37L,   /*!< \brief The board is N6781  */
#     CAEN_DGTZ_V1781     =38L,   /*!< \brief The board is V1781  */
#     CAEN_DGTZ_DT5725    =39L,   /*!< \brief The board is DT5725 */
#     CAEN_DGTZ_N6725     =40L,   /*!< \brief The board is N6725  */
#     CAEN_DGTZ_V1725     =41L,   /*!< \brief The board is V1725  */
#     
# } CAEN_DGTZ_BoardModel_t;
# 
# typedef enum {
#     CAEN_DGTZ_VME64_FORM_FACTOR   = 0L,
#     CAEN_DGTZ_VME64X_FORM_FACTOR  = 1L,
#     CAEN_DGTZ_DESKTOP_FORM_FACTOR = 2L,
#     CAEN_DGTZ_NIM_FORM_FACTOR     = 3L,
# } CAEN_DGTZ_BoardFormFactor_t;
# 
# typedef enum {
#     CAEN_DGTZ_XX724_FAMILY_CODE  = 0L,
#     CAEN_DGTZ_XX721_FAMILY_CODE  = 1L,
#     CAEN_DGTZ_XX731_FAMILY_CODE  = 2L,
#     CAEN_DGTZ_XX720_FAMILY_CODE  = 3L,
#     CAEN_DGTZ_XX740_FAMILY_CODE  = 4L,
#     CAEN_DGTZ_XX751_FAMILY_CODE  = 5L,
#     CAEN_DGTZ_XX742_FAMILY_CODE  = 6L, 
#     CAEN_DGTZ_XX780_FAMILY_CODE  = 7L,
#     CAEN_DGTZ_XX761_FAMILY_CODE  = 8L,
#     CAEN_DGTZ_XX743_FAMILY_CODE  = 9L,
#     // NOTE: 10 is skipped because maps family models DT55xx
#     CAEN_DGTZ_XX730_FAMILY_CODE  = 11L,
#     CAEN_DGTZ_XX790_FAMILY_CODE  = 12L,
#     CAEN_DGTZ_XX781_FAMILY_CODE  = 13L,
#     CAEN_DGTZ_XX725_FAMILY_CODE  = 14L,
# } CAEN_DGTZ_BoardFamilyCode_t;
# 
# typedef enum CAEN_DGTZ_DPP_PARAMETER
# {
#     CAEN_DGTZ_DPP_Param_m                = 0L,
#     CAEN_DGTZ_DPP_Param_M                = 1L,
#     CAEN_DGTZ_DPP_Param_Delta1            = 2L,
#     CAEN_DGTZ_DPP_Param_a                = 3L,
#     CAEN_DGTZ_DPP_Param_b                = 4L,
#     CAEN_DGTZ_DPP_Param_NSBaseline        = 5L,
#     CAEN_DGTZ_DPP_Param_shf                = 6L,
#     CAEN_DGTZ_DPP_Param_k                = 7L,
#     CAEN_DGTZ_DPP_Param_NSPeakMean        = 8L,
#     CAEN_DGTZ_DPP_Param_FlatTopDelay    = 9L,
#     CAEN_DGTZ_DPP_Param_Decimation        = 10L,
#     CAEN_DGTZ_DPP_Param_TrgThreshold    = 11L,
#     CAEN_DGTZ_DPP_Param_TrgWinOffset    = 12L,
#     CAEN_DGTZ_DPP_Param_TrgWinWidth        = 13L,
#     CAEN_DGTZ_DPP_Param_DigitalGain        = 14L,
#     CAEN_DGTZ_DPP_Param_GateWidth        = 15L,
#     CAEN_DGTZ_DPP_Param_PreGate            = 16L,
#     CAEN_DGTZ_DPP_Param_HoldOffTime        = 17L,
#     CAEN_DGTZ_DPP_Param_BslThreshold    = 18L,
#     CAEN_DGTZ_DPP_Param_NoFlatTime        = 19L,
#     CAEN_DGTZ_DPP_Param_GateMode        = 20L,
#     CAEN_DGTZ_DPP_Param_InvertInput        = 21L,
# } CAEN_DGTZ_DPP_PARAMETER_t;
# 
# typedef enum
# {
#     CAEN_DGTZ_FPIO_MODES_GPIO            = 0L,            /*!< General purpose IO */
#     CAEN_DGTZ_FPIO_MODES_PROGIO            = 1L,            /*!< Programmed IO */
#     CAEN_DGTZ_FPIO_MODES_PATTERN        = 2L,            /*!< Pattern mode */
# } CAEN_DGTZ_FrontPanelIOModes;
# 
# typedef enum
# {
#     CAEN_DGTZ_TRGMODE_DISABLED                = 0L,
#     CAEN_DGTZ_TRGMODE_EXTOUT_ONLY            = 2L,
#     CAEN_DGTZ_TRGMODE_ACQ_ONLY                = 1L,
#     CAEN_DGTZ_TRGMODE_ACQ_AND_EXTOUT        = 3L,
# }CAEN_DGTZ_TriggerMode_t;
# 
# typedef enum {
#     CAEN_DGTZ_TRIGGER                     = 0L,
#     CAEN_DGTZ_FASTTRG_ALL                 = 1L,
#     CAEN_DGTZ_FASTTRG_ACCEPTED              = 2L,
#     CAEN_DGTZ_BUSY                         = 3L,
#     CAEN_DGTZ_CLK_OUT                     = 4L,
#     CAEN_DGTZ_RUN                         = 5L,
#     CAEN_DGTZ_TRGPULSE                     = 6L,    
#     CAEN_DGTZ_OVERTHRESHOLD                 = 7L,                    
# } CAEN_DGTZ_OutputSignalMode_t;
# 
# typedef enum
# {
#     CAEN_DGTZ_ZS_NO                        = 0L,
#     CAEN_DGTZ_ZS_INT                    = 1L,
#     CAEN_DGTZ_ZS_ZLE                    = 2L,
#     CAEN_DGTZ_ZS_AMP                    = 3L,
# } CAEN_DGTZ_ZS_Mode_t;
# 
# typedef enum
# {
#     CAEN_DGTZ_ENABLE                    = 1L,
#     CAEN_DGTZ_DISABLE                    = 0L,
# } CAEN_DGTZ_EnaDis_t;
# 
# typedef enum 
# {
#     CAEN_DGTZ_ZS_FINE                    = 0L,
#     CAEN_DGTZ_ZS_COARSE                  = 1L,
# }CAEN_DGTZ_ThresholdWeight_t;            
# 
# 
# typedef enum
# {
#     CAEN_DGTZ_SW_CONTROLLED             = 0L,
#     CAEN_DGTZ_S_IN_CONTROLLED           = 1L,
#     CAEN_DGTZ_FIRST_TRG_CONTROLLED      = 2L,
# 	CAEN_DGTZ_LVDS_CONTROLLED           = 3L,
# }CAEN_DGTZ_AcqMode_t;
# 
# typedef enum
# {
#     CAEN_DGTZ_AM_TRIGGER_MAJORITY        = 0L,
#     CAEN_DGTZ_AM_TEST                    = 1L,
#     CAEN_DGTZ_AM_ANALOG_INSPECTION        = 2L,
#     CAEN_DGTZ_AM_BUFFER_OCCUPANCY        = 3L,
#     CAEN_DGTZ_AM_VOLTAGE_LEVEL            = 4L,
# }CAEN_DGTZ_AnalogMonitorOutputMode_t;
# 
# typedef enum 
# {
#     CAEN_DGTZ_AM_MAGNIFY_1X                = 0L,
#     CAEN_DGTZ_AM_MAGNIFY_2X                = 1L,
#     CAEN_DGTZ_AM_MAGNIFY_4X                = 2L,
#     CAEN_DGTZ_AM_MAGNIFY_8X                = 3L,
# }CAEN_DGTZ_AnalogMonitorMagnify_t;            
# 
# 
# typedef enum 
# {
#     CAEN_DGTZ_AM_INSPECTORINVERTER_P_1X     = 0L,
#     CAEN_DGTZ_AM_INSPECTORINVERTER_N_1X  = 1L,
# }CAEN_DGTZ_AnalogMonitorInspectorInverter_t;
# 
# typedef enum 
# {
#     CAEN_DGTZ_IRQ_MODE_RORA                 = 0L,
#     CAEN_DGTZ_IRQ_MODE_ROAK                 = 1L,
# }CAEN_DGTZ_IRQMode_t;
# 
# typedef enum
# {
#     CAEN_DGTZ_IRQ_DISABLED                = 0L,
#     CAEN_DGTZ_IRQ_ENABLED_OPTICAL        = 1L,
#     CAEN_DGTZ_IRQ_ENABLED_VME_RORA        = 1L,
#     CAEN_DGTZ_IRQ_ENABLED_VME_ROAK        = 2L,
# } CAEN_DGTZ_IRQState_t;
# 
# typedef enum 
# {
#     CAEN_DGTZ_SLAVE_TERMINATED_READOUT_MBLT        = 0L,
#     CAEN_DGTZ_SLAVE_TERMINATED_READOUT_2eVME     = 1L,
#     CAEN_DGTZ_SLAVE_TERMINATED_READOUT_2eSST     = 2L,
#     CAEN_DGTZ_POLLING_MBLT                         = 3L,
#     CAEN_DGTZ_POLLING_2eVME                        = 4L,
#     CAEN_DGTZ_POLLING_2eSST                        = 5L,
# } CAEN_DGTZ_ReadMode_t;
# 
# typedef enum
# {
#     CAEN_DGTZ_DPP_ACQ_MODE_Oscilloscope            = 0L,
#     CAEN_DGTZ_DPP_ACQ_MODE_List                    = 1L,
#     CAEN_DGTZ_DPP_ACQ_MODE_Mixed                = 2L,
# } CAEN_DGTZ_DPP_AcqMode_t;
# 
# typedef enum
# {
#     CAEN_DGTZ_DPP_CI_GPO_Gate                = 0L,
#     CAEN_DGTZ_DPP_CI_GPO_Discri                = 1L,
#     CAEN_DGTZ_DPP_CI_GPO_Coincidence        = 2L,
# } CAEN_DGTZ_DPP_CI_GPO_SEL_t;
# 
# typedef enum {
#     CAEN_DGTZ_DPP_Channel_0                    = 0L,
#     CAEN_DGTZ_DPP_Channel_1                    = 1L,
#     CAEN_DGTZ_DPP_Channel_2                    = 2L,
#     CAEN_DGTZ_DPP_Channel_3                    = 3L,
#     CAEN_DGTZ_DPP_Channel_4                    = 4L,
#     CAEN_DGTZ_DPP_Channel_5                    = 5L,
#     CAEN_DGTZ_DPP_Channel_6                    = 6L,
#     CAEN_DGTZ_DPP_Channel_7                    = 7L,
#     CAEN_DGTZ_DPP_Channel_ALL                  = 255L,
# } CAEN_DGTZ_DPP_Channel_t;
# 
# /*! 
#  * \brief Defines whether to include an additional virtual analog probe in the readout data
#  *        at the cost of halving the resolution of the first
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_VIRTUALPROBE_SINGLE        = 0L,
#     CAEN_DGTZ_DPP_VIRTUALPROBE_DUAL          = 1L,
# } CAEN_DGTZ_DPP_VirtualProbe_t;
# 
# /*! 
#  * \brief Defines the digital signals that can be carried by the digital probe
#  *        in the readout data of the DPP-PHA
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_trgWin      = 0L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_Armed       = 1L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_PkRun       = 2L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_PURFlag     = 3L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_Peaking     = 4L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_TVAW        = 5L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_BLHoldoff   = 6L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_TRGHoldoff  = 7L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_TRGVal      = 8L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_ACQVeto     = 9L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_BFMVeto     = 10L,
#     CAEN_DGTZ_DPP_PHA_DIGITAL_PROBE_ExtTRG      = 11L,
# } CAEN_DGTZ_DPP_PHA_DigitalProbe_t;
# 
# /*! 
#  * \brief Defines the signals that can be carried by the virtual analog probe 1
#  *        in the readout data of the DPP-PHA
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE1_Input        = 0L,
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE1_Delta        = 1L,
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE1_Delta2       = 2L,
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE1_trapezoid    = 3L,
# } CAEN_DGTZ_DPP_PHA_VirtualProbe1_t;
#   
# /*! 
#  * \brief Defines the signals that can be carried by the virtual analog probe 2
#  *        in the readout data of the DPP-PHA
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE2_Input           = 0L,
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE2_S3              = 1L,
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE2_DigitalCombo    = 2L,
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE2_trapBaseline    = 3L,
#     CAEN_DGTZ_DPP_PHA_VIRTUALPROBE2_None            = 4L,
# } CAEN_DGTZ_DPP_PHA_VirtualProbe2_t;
# 
# 
# /*! 
#  * \brief Defines the signals that can be carried by the virtual analog probe
#  *        in the readout data of the DPP-CI version 2
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_CI_VIRTUALPROBE_Baseline = 0L,
# } CAEN_DGTZ_DPP_CI_VirtualProbe_t;
# 
# /*! 
#  * \brief Defines the signals that can be carried by the digital probe 1
#  *        in the readout data of the DPP-CI version 2
#  */
# typedef enum
# {
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-CI  *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL <= 130.20                      *
#     *  For newer firmwares, use the values marked with 'R22' in *
#     *  the name.                                                *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_BlOutSafeBand    = 0L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_BlTimeout        = 1L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_CoincidenceMet    = 2L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_Tvaw                = 3L,
# 
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-CI  *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL >= 130.22                      *
#     *  For older firmwares, use the values above.               *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_R22_ExtTrg       = 4L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_R22_OverThr      = 5L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_R22_TrigOut      = 6L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_R22_CoincWin     = 7L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE1_R22_Coincidence  = 9L,
# } CAEN_DGTZ_DPP_CI_DigitalProbe1_t;
# 
# /*! 
#  * \brief Defines the signals that can be carried by the digital probe 2
#  *        in the readout data of the DPP-CI version 2
#  */
# typedef enum
# {
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-CI  *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL <= 130.20                      *
#     *  For newer firmwares, use the values marked with 'R22' in *
#     *  the name.                                                *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_BlOutSafeBand    = 0L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_BlTimeout        = 1L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_CoincidenceMet   = 2L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_Tvaw             = 3L,
# 
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-CI  *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL >= 130.22                      *
#     *  For older firmwares, use the values above.               *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_R22_OverThr      = 5L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_R22_TrgVal       = 6L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_R22_TrgHO        = 7L,
#     CAEN_DGTZ_DPP_CI_DIGITALPROBE2_R22_Coincidence  = 9L,
# } CAEN_DGTZ_DPP_CI_DigitalProbe2_t;
# 
# /*! 
#  * \brief Defines the signals that can be carried by the virtual analog probe
#  *        in the readout data of the DPP-PSD
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_PSD_VIRTUALPROBE_Baseline     = 0L,
#     CAEN_DGTZ_DPP_PSD_VIRTUALPROBE_Threshold    = 1L,
# } CAEN_DGTZ_DPP_PSD_VirtualProbe_t;
# 
# /*! 
#  * \brief Defines the signals that can be carried by the digital probe 1
#  *        in the readout data of the DPP-PSD
#  */
# typedef enum
# {
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-PSD *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL <= 131.5                       *
#     *       x751 Boards: AMC_REL <= 132.5                       *
#     *  For newer firmwares, use the values marked with 'R6' in  *
#     *  the name.                                                *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
#     
#     /* x720 Digital Probes Types */
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_Armed           = 0L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_Trigger         = 1L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_ChargeReady     = 2L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_PileUp          = 3L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_BlOutSafeBand   = 4L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_BlTimeout       = 5L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_CoincidenceMet  = 6L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_Tvaw            = 7L,
# 
#     /* x751 Digital Probes Types */
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_OverThr         = 8L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_GateShort       = 9L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_None            = 10L,
# 
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-PSD *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL >= 131.6                       *
#     *       x751 Boards: AMC_REL >= 132.6                       *
#     *  For older firmwares, use the values above.               *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_R6_ExtTrg       = 11L, /* x720 only */
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_R6_OverThr      = 12L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_R6_TrigOut      = 13L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_R6_CoincWin     = 14L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_R6_PileUp       = 15L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_R6_Coincidence  = 16L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE1_R6_GateLong     = 17L, 
# } CAEN_DGTZ_DPP_PSD_DigitalProbe1_t;
# 
# /*! 
#  * \brief Defines the signals that can be carried by the digital probe 2
#  *        in the readout data of the DPP-PSD
#  */
# typedef enum
# {
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-PSD *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL <= 131.5                       *
#     *       x751 Boards: AMC_REL <= 132.5                       *
#     *  For newer firmwares, use the values marked with 'R6' in  *
#     *  the name.                                                *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
# 
#     /* x720 Digital Probes Types */
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_Armed           = 0L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_Trigger         = 1L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_ChargeReady     = 2L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_PileUp          = 3L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_BlOutSafeBand   = 4L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_BlTimeout       = 5L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_CoincidenceMet  = 6L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_Tvaw            = 7L,
# 
#     /* x751 Digital Probes Types */
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_GateShort       = 8L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_GateLong        = 9L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_None            = 10L,
# 
#     /************************************************************
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     *  The following values are valid for the following DPP-PSD *
#     *  Firmwares:                                               *
#     *       x720 Boards: AMC_REL >= 131.6                       *
#     *       x751 Boards: AMC_REL >= 132.6                       *
#     *  For older firmwares, use the values above.               *
#     *  WARNING WARNING WARNING WARNING WARNING WARNING WARNING  *
#     ************************************************************/
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_R6_GateShort    = 11L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_R6_OverThr      = 12L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_R6_TrgVal       = 13L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_R6_TrgHO        = 14L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_R6_PileUp       = 15L,
#     CAEN_DGTZ_DPP_PSD_DIGITALPROBE2_R6_Coincidence  = 16L,
# } CAEN_DGTZ_DPP_PSD_DigitalProbe2_t;
# 
#   ANALOG_TRACE_1 (0)
#   ANALOG_TRACE_2 (1)
#   DIGITAL_TRACE_1 (2)
#   DIGITAL_TRACE_2 (3)
#   DIGITAL_TRACE_3 (4)
#   DIGITAL_TRACE_4 (5)
# 
#   CAEN_DGTZ_DPP_VIRTUALPROBE_Invalid (-1)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_Input (0)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_Delta (1)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_Delta2 (2)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_Trapezoid (3)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_TrapezoidReduced (4)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_Baseline (5)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_Threshold (6)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_CFD (7)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_SmoothedInput (8)
#   CAEN_DGTZ_DPP_VIRTUALPROBE_None (9)
# 
#   CAEN_DGTZ_DPP_DIGITALPROBE_TRGWin (10)
#   CAEN_DGTZ_DPP_DIGITALPROBE_Armed (11)
#   CAEN_DGTZ_DPP_DIGITALPROBE_PkRun (12)
#   CAEN_DGTZ_DPP_DIGITALPROBE_Peaking (13)
#   CAEN_DGTZ_DPP_DIGITALPROBE_CoincWin (14)
#   CAEN_DGTZ_DPP_DIGITALPROBE_BLHoldoff (15)
#   CAEN_DGTZ_DPP_DIGITALPROBE_TRGHoldoff (16)
#   CAEN_DGTZ_DPP_DIGITALPROBE_TRGVal (17)
#   CAEN_DGTZ_DPP_DIGITALPROBE_ACQVeto (18)
#   CAEN_DGTZ_DPP_DIGITALPROBE_BFMVeto (19)
#   CAEN_DGTZ_DPP_DIGITALPROBE_ExtTRG (20)
#   CAEN_DGTZ_DPP_DIGITALPROBE_OverThr (21)
#   CAEN_DGTZ_DPP_DIGITALPROBE_TRGOut (22)
#   CAEN_DGTZ_DPP_DIGITALPROBE_Coincidence (23)
#   CAEN_DGTZ_DPP_DIGITALPROBE_PileUp (24)
#   CAEN_DGTZ_DPP_DIGITALPROBE_Gate (25)
#   CAEN_DGTZ_DPP_DIGITALPROBE_GateShort (26)
#   CAEN_DGTZ_DPP_DIGITALPROBE_Trigger (27)
#   CAEN_DGTZ_DPP_DIGITALPROBE_None (28)
#   CAEN_DGTZ_DPP_DIGITALPROBE_BLFreeze (29)
#   CAEN_DGTZ_DPP_DIGITALPROBE_Busy (30)
#   CAEN_DGTZ_DPP_DIGITALPROBE_PrgVeto (31)
# 
# 
# /*! 
#  * \brief Defines the kind of histogram data returned in readout data
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_SAVE_PARAM_EnergyOnly     = 0L, /*!< Only energy (DPP-PHA) or charge (DPP-PSD/DPP-CI v2) is returned */
#     CAEN_DGTZ_DPP_SAVE_PARAM_TimeOnly       = 1L, /*!< Only time is returned */
#     CAEN_DGTZ_DPP_SAVE_PARAM_EnergyAndTime  = 2L, /*!< Both energy/charge and time are returned */
#     CAEN_DGTZ_DPP_SAVE_PARAM_ChargeAndTime  = 4L, /*!< \deprecated On DPP-PSD and DPP-CI use CAEN_DGTZ_DPP_SAVE_PARAM_EnergyAndTime */
#     CAEN_DGTZ_DPP_SAVE_PARAM_None           = 3L, /*!< No histogram data is returned */
# } CAEN_DGTZ_DPP_SaveParam_t;
# 
# typedef enum {
#     CAEN_DGTZ_IOLevel_NIM        = 0L,
#     CAEN_DGTZ_IOLevel_TTL        = 1L,
# } CAEN_DGTZ_IOLevel_t;
# 
# typedef enum {
#     CAEN_DGTZ_DRS4_5GHz         = 0L,
#     CAEN_DGTZ_DRS4_2_5GHz       = 1L,
#     CAEN_DGTZ_DRS4_1GHz         = 2L,
#     CAEN_DGTZ_DRS4_750MHz       = 3L, 
#     _CAEN_DGTZ_DRS4_COUNT_      = 4L,
# } CAEN_DGTZ_DRS4Frequency_t;
# 
# typedef enum {
#     CAEN_DGTZ_SAM_3_2GHz        = 0L,
#     CAEN_DGTZ_SAM_1_6GHz        = 1L,
#     CAEN_DGTZ_SAM_800MHz        = 2L,
#     CAEN_DGTZ_SAM_400MHz        = 3L,
# } CAEN_DGTZ_SAMFrequency_t;
# /*! 
#  * \brief Defines the available synchronization modes to be set with CAEN_DGTZ_SetDPPRunSynchronizationMode
#  */
# typedef enum {
#     CAEN_DGTZ_RUN_SYNC_Disabled,
#     CAEN_DGTZ_RUN_SYNC_TrgOutTrgInDaisyChain,
#     CAEN_DGTZ_RUN_SYNC_TrgOutSinDaisyChain,
#     CAEN_DGTZ_RUN_SYNC_SinFanout,
#     CAEN_DGTZ_RUN_SYNC_GpioGpioDaisyChain
# } CAEN_DGTZ_RunSyncMode_t;
# 
# 
# typedef enum {
#     CAEN_DGTZ_TriggerOnRisingEdge        = 0L,
#     CAEN_DGTZ_TriggerOnFallingEdge        = 1L,
# } CAEN_DGTZ_TriggerPolarity_t;
# 
# typedef enum {
#     CAEN_DGTZ_PulsePolarityPositive        = 0,
#     CAEN_DGTZ_PulsePolarityNegative        = 1,
# } CAEN_DGTZ_PulsePolarity_t;
# 
# 
# typedef enum {
#     CAEN_DGTZ_SAMPulseSoftware            = 0,
#     CAEN_DGTZ_SAMPulseCont                = 1,
# } CAEN_DGTZ_SAMPulseSourceType_t;
# 
# typedef enum  {
#     CAEN_DGTZ_AcquisitionMode_STANDARD    = 0,    
#     CAEN_DGTZ_AcquisitionMode_DPP_CI    = 1,
# } CAEN_DGTZ_AcquisitionMode_t ;
# 
# typedef enum {
#     CAEN_DGTZ_LOGIC_OR            = 0,
#     CAEN_DGTZ_LOGIC_AND            = 1,
#     CAEN_DGTZ_LOGIC_MAJORITY    = 2,
# } CAEN_DGTZ_TrigerLogic_t;
# 
# typedef struct {
#     char                        ModelName[12];
#     uint32_t                    Model;
#     uint32_t                    Channels;
#     uint32_t                    FormFactor;
#     uint32_t                    FamilyCode;
#     char                        ROC_FirmwareRel[20];
#     char                        AMC_FirmwareRel[40];
#     uint32_t                    SerialNumber;
#     char                        MezzanineSerNum[4][8];       //used only for x743 boards
#     uint32_t                    PCB_Revision;
#     uint32_t                    ADC_NBits;
#     uint32_t                    SAMCorrectionDataLoaded;        //used only for x743 boards
#     int                         CommHandle;
#     int                         VMEHandle;
#     char                        License[MAX_LICENSE_LENGTH];
# } CAEN_DGTZ_BoardInfo_t;
# 
# typedef struct 
# {
#     uint32_t             EventSize;
#     uint32_t             BoardId;
#     uint32_t             Pattern;
#     uint32_t             ChannelMask;
#     uint32_t             EventCounter;
#     uint32_t             TriggerTimeTag;
# } CAEN_DGTZ_EventInfo_t;
# 
# typedef struct 
# {
#     uint32_t                 ChSize[MAX_X742_CHANNEL_SIZE];           // the number of samples stored in DataChannel array  
#     float                     *DataChannel[MAX_X742_CHANNEL_SIZE];  // the array of ChSize samples
#     uint32_t                 TriggerTimeTag;
#     uint16_t                 StartIndexCell;
# } CAEN_DGTZ_X742_GROUP_t;
# 
# typedef struct 
# {
#     uint32_t                 ChSize;                                   // the number of samples stored in DataChannel array  
#     float                    *DataChannel[MAX_X743_CHANNELS_X_GROUP];     // the array of ChSize samples
#     uint16_t                 TriggerCount[MAX_X743_CHANNELS_X_GROUP];
#     uint16_t                 TimeCount[MAX_X743_CHANNELS_X_GROUP];
#     uint8_t                  EventId;
#     uint16_t                 StartIndexCell;
#     uint64_t                 TDC;
# 	float					 PosEdgeTimeStamp;
# 	float					 NegEdgeTimeStamp;
# 	uint16_t				 PeakIndex;
# 	float					 Peak;
# 	float					 Baseline;
# 	float					 Charge;
# 
# } CAEN_DGTZ_X743_GROUP_t;
# 
# typedef struct 
# {
#     uint32_t            ChSize[MAX_UINT16_CHANNEL_SIZE]; // the number of samples stored in DataChannel array  
#     uint16_t            *DataChannel[MAX_UINT16_CHANNEL_SIZE]; // the array of ChSize samples
# } CAEN_DGTZ_UINT16_EVENT_t;
# 
# typedef struct 
# {
#     uint32_t            ChSize[MAX_UINT8_CHANNEL_SIZE]; // the number of samples stored in DataChannel array  
#     uint8_t                *DataChannel[MAX_UINT8_CHANNEL_SIZE];  // the array of ChSize samples
# } CAEN_DGTZ_UINT8_EVENT_t;
# 
# typedef struct 
# {
#     uint8_t                    GrPresent[MAX_X742_GROUP_SIZE]; // If the group has data the value is 1 otherwise is 0  
#     CAEN_DGTZ_X742_GROUP_t    DataGroup[MAX_X742_GROUP_SIZE]; // the array of ChSize samples
# } CAEN_DGTZ_X742_EVENT_t;
# 
# typedef struct 
# {
#     uint8_t                   GrPresent[MAX_V1743_GROUP_SIZE]; // If the group has data the value is 1 otherwise is 0  
#     CAEN_DGTZ_X743_GROUP_t    DataGroup[MAX_V1743_GROUP_SIZE]; // the array of ChSize samples
# } CAEN_DGTZ_X743_EVENT_t;
# 
# /*! 
#  * \brief Event type for DPP-PHA to be used within the <b>new readout API</b>
#  */
# typedef struct 
# {
#     uint32_t Format;
#     uint64_t TimeTag;
#     uint16_t Energy;
#     int16_t Extras;
#     uint32_t *Waveforms; /*!< pointer to coded data inside the readout buffer. only meant to be supplied to CAEN_DGTZ_DecodeDPPWaveforms */ 
#     uint32_t Extras2;
# } CAEN_DGTZ_DPP_PHA_Event_t;
# 
# /*! 
#  * \brief Event type for DPP-PSD to be used within the <b>new readout API</b>
#  */
# typedef struct 
# {
#     uint32_t Format;
#     uint32_t Format2;
#     uint32_t TimeTag;
#     int16_t ChargeShort;
#     int16_t ChargeLong;
#     int16_t Baseline;
#     int16_t Pur;
#     uint32_t *Waveforms; /*!< pointer to coded data inside the readout buffer. only meant to be supplied to CAEN_DGTZ_DecodeDPPWaveforms */ 
#     uint32_t Extras;
# } CAEN_DGTZ_DPP_PSD_Event_t;
# 
# /*! 
#  * \brief Event type for DPP-CI v2 to be used within the <b>new readout API</b>
#  */
# typedef struct 
# {
#     uint32_t Format;
#     uint32_t TimeTag;
#     int16_t Charge;
#     int16_t Baseline;
#     uint32_t *Waveforms; /*!< pointer to coded data inside the readout buffer. only meant to be supplied to CAEN_DGTZ_DecodeDPPWaveforms */ 
# } CAEN_DGTZ_DPP_CI_Event_t;
# 
# /*!
# * \brief Event type for DPP-QDC to be used within the <b>new readout API</b>
# */
# typedef struct
# {
# 	uint8_t  isExtendedTimeStamp;
# 	uint32_t Format;
# 	uint64_t TimeTag;
# 	uint16_t Charge;
# 	int16_t  Baseline;
# 	uint16_t Pur;
# 	uint16_t Overrange;
# 	uint16_t SubChannel;
# 	uint32_t *Waveforms; 
# 	uint32_t Extras;
# } CAEN_DGTZ_DPP_QDC_Event_t;
# 
# 
# /*! 
#  * \brief Event type for 751 ZLE to be used within the <b>new readout API</b>
#  */
# typedef struct 
# {
#     uint32_t timeTag;
#     uint32_t baseline;
#     uint32_t *Waveforms;
# } CAEN_DGTZ_751_ZLE_Event_t;
# 
# typedef struct
# {
# 	uint32_t TraceNumber;
# 	uint16_t *Trace;
# 	uint32_t *TraceIndex;
# 
# } CAEN_DGTZ_730_ZLE_Waveforms_t;
# 
# typedef struct
# {
# 	uint32_t fifo_full;
# 	uint32_t size_wrd;
# 	uint32_t baseline;				   
# 	uint32_t *DataPtr;
# 	CAEN_DGTZ_730_ZLE_Waveforms_t *Waveforms;
# } CAEN_DGTZ_730_ZLE_Channel_t;
# 
# typedef struct
# {
# 	uint32_t size;
# 	uint16_t chmask;
# 	uint32_t tcounter;
# 	uint64_t timeStamp;				   
# 	CAEN_DGTZ_730_ZLE_Channel_t *Channel[MAX_V1730_CHANNEL_SIZE];
# 
# } CAEN_DGTZ_730_ZLE_Event_t;
# 
# typedef struct
# {
# 	uint16_t *Trace;
# } CAEN_DGTZ_730_DAW_Waveforms_t;
# 
# typedef struct
# {
# 	uint32_t truncate;
# 	uint32_t EvType;
# 	uint32_t size;
# 	uint64_t timeStamp;
# 	uint16_t baseline;
# 	uint16_t *DataPtr; 
# 	CAEN_DGTZ_730_DAW_Waveforms_t *Waveforms; // Waveform coincides with raw data for DAW, used for uniformity with other firmwares
# } CAEN_DGTZ_730_DAW_Channel_t;
# 
# typedef struct
# {
# 	uint32_t size;
# 	uint16_t chmask;
# 	uint32_t tcounter;
# 	uint64_t timeStamp; // ha senso metterla? La timestamp dell'header non ha nessun senso fisico
# 	CAEN_DGTZ_730_DAW_Channel_t *Channel[MAX_V1730_CHANNEL_SIZE];
# } CAEN_DGTZ_730_DAW_Event_t;
# 
# 
# 
# typedef struct 
# {
#     float   Charge;// in pico-Coulombs :  array of ChSize samples
#     int     StartIndexCell;
# } CAEN_DGTZ_DPP_X743_Event_t;
# 
# /*! 
#  * \brief Waveform type for DPP-PHA to be used within the <b>new readout API</b>
#  */
# typedef struct 
# {
#     uint32_t Ns;
#     uint8_t  DualTrace;
#     uint8_t  VProbe1;
#     uint8_t  VProbe2;
#     uint8_t  VDProbe;
#     int16_t *Trace1;
#     int16_t *Trace2;
#     uint8_t  *DTrace1;
#     uint8_t  *DTrace2;
# } CAEN_DGTZ_DPP_PHA_Waveforms_t;
# 
# /*! 
#  * \brief Waveform type for DPP-PSD to be used within the <b>new readout API</b>
#  */
# typedef struct
# {
#     uint32_t Ns;
#     uint8_t  dualTrace;
#     uint8_t  anlgProbe;
#     uint8_t  dgtProbe1;
#     uint8_t  dgtProbe2;
#     uint16_t *Trace1;
#     uint16_t *Trace2;
#     uint8_t  *DTrace1;
#     uint8_t  *DTrace2;
#     uint8_t  *DTrace3;
#     uint8_t  *DTrace4;
# } CAEN_DGTZ_DPP_PSD_Waveforms_t;
# 
# 
# /*! 
#  * \brief Waveform type for 751ZLE to be used within the <b>new readout API</b>
#  */
# typedef struct
# {
#     uint32_t Ns;
#     uint16_t *Trace1;
#     uint8_t *Discarded;
# } CAEN_DGTZ_751_ZLE_Waveforms_t;
# 
#   CAEN_DGTZ_DPP_CI_Waveforms_t CAEN_DGTZ_DPP_PSD_Waveforms_t /*!< \brief Waveform types for DPP-CI and DPP-PSD are the same, hence this define */
# 
# typedef struct
# {
# 	uint32_t Ns;
# 	uint8_t  dualTrace;
# 	uint8_t  anlgProbe;
# 	uint8_t  dgtProbe1;
# 	uint8_t  dgtProbe2;
# 	uint16_t *Trace1;
# 	uint16_t *Trace2;
# 	uint8_t  *DTrace1;
# 	uint8_t  *DTrace2;
# 	uint8_t  *DTrace3;
# 	uint8_t  *DTrace4;
# } CAEN_DGTZ_DPP_QDC_Waveforms_t;
# 
#   CAEN_DGTZ_AutoAggregation 0
# 
# /*! 
#  * \brief Defines the Pile Up Rejection method
#  * \note Only for DPP-PSD and DPP-CI version 2
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_PSD_PUR_DetectOnly, /*!< Only detect pile-up events by setting the Pur field in the readout data (CAEN_DGTZ_DPP_PSD_Event_t) */
#     CAEN_DGTZ_DPP_PSD_PUR_Enabled /*!< Reject pile-up events. They won't be read out */
# } CAEN_DGTZ_DPP_PUR_t;
#   CAEN_DGTZ_DPP_CI_PUR_DetectOnly CAEN_DGTZ_DPP_PSD_PUR_DetectOnly /*!< \brief PileUp Rejection types for DPP-CI and DPP-PSD are the same, hence this define */
#   CAEN_DGTZ_DPP_CI_PUR_Enabled CAEN_DGTZ_DPP_PSD_PUR_Enabled /*!< \brief PileUp Rejection types for DPP-CI and DPP-PSD are the same, hence this define */
# 
# typedef enum
# {
# 	CAEN_DGTZ_DPP_DISCR_MODE_LED, /*!< Leading Edge event discimination */
# 	CAEN_DGTZ_DPP_DISCR_MODE_CFD /*!< Constant Fraction event discrimination */
# } CAEN_DGTZ_DPP_Discrimination_t;
# 
# 
# /*! 
#  * \brief Defines the trigger mode to be set with CAEN_DGTZ_SetDPPTriggerMode
#  * \note Only for DPP-PSD and DPP-CI version 2
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_TriggerMode_Normal,
#     CAEN_DGTZ_DPP_TriggerMode_Coincidence
# } CAEN_DGTZ_DPP_TriggerMode_t;
# 
# /*! 
#  * \brief Defines the trigger configuration to be set with CAEN_DGTZ_SetDPPTriggerConfig
#  * \note Only for DPP-PSD and DPP-CI version 2
#  */
# typedef enum
# {
#     CAEN_DGTZ_DPP_TriggerConfig_Peak,
#     CAEN_DGTZ_DPP_TriggerConfig_Threshold
# } CAEN_DGTZ_DPP_TriggerConfig_t;
# 
# 
# typedef enum 
# {
#     CAEN_DGTZ_DPPFirmware_PHA,
#     CAEN_DGTZ_DPPFirmware_PSD,
#     CAEN_DGTZ_DPPFirmware_CI,
# 	CAEN_DGTZ_DPPFirmware_ZLE,
# 	CAEN_DGTZ_DPPFirmware_QDC,
# 	CAEN_DGTZ_DPPFirmware_DAW,
#     CAEN_DGTZ_NotDPPFirmware = -1
# } CAEN_DGTZ_DPPFirmware_t;
# 
# /*! 
#  * \brief DPP parameter structure to be initialized and passed to CAEN_DGTZ_SetDPPParameters
#  * \note1 Only for DPP-PHA
#  */
# typedef struct
# {
#     int M           [MAX_DPP_PHA_CHANNEL_SIZE]; // Signal Decay Time Constant
#     int m           [MAX_DPP_PHA_CHANNEL_SIZE]; // Trapezoid Flat Top
#     int k           [MAX_DPP_PHA_CHANNEL_SIZE]; // Trapezoid Rise Time
#     int ftd         [MAX_DPP_PHA_CHANNEL_SIZE]; //
#     int a           [MAX_DPP_PHA_CHANNEL_SIZE]; // Trigger Filter smoothing factor
#     int b           [MAX_DPP_PHA_CHANNEL_SIZE]; // Input Signal Rise time
#     int thr         [MAX_DPP_PHA_CHANNEL_SIZE]; // Trigger Threshold
#     int nsbl        [MAX_DPP_PHA_CHANNEL_SIZE]; // Number of Samples for Baseline Mean
#     int nspk        [MAX_DPP_PHA_CHANNEL_SIZE]; // Number of Samples for Peak Mean Calculation
#     int pkho        [MAX_DPP_PHA_CHANNEL_SIZE]; // Peak Hold Off
#     int blho        [MAX_DPP_PHA_CHANNEL_SIZE]; // Base Line Hold Off
#     int otrej       [MAX_DPP_PHA_CHANNEL_SIZE]; // 
#     int trgho       [MAX_DPP_PHA_CHANNEL_SIZE]; // Trigger Hold Off
#     int twwdt       [MAX_DPP_PHA_CHANNEL_SIZE]; // 
#     int trgwin      [MAX_DPP_PHA_CHANNEL_SIZE]; //
#     int dgain       [MAX_DPP_PHA_CHANNEL_SIZE]; // Digital Probe Gain
#     float enf       [MAX_DPP_PHA_CHANNEL_SIZE]; // Energy Nomralization Factor
#     int decimation  [MAX_DPP_PHA_CHANNEL_SIZE]; // Decimation of Input Signal
# 	int enskim      [MAX_DPP_PHA_CHANNEL_SIZE]; // Enable energy skimming
# 	int eskimlld    [MAX_DPP_PHA_CHANNEL_SIZE]; // LLD    energy skimming
#     int eskimuld    [MAX_DPP_PHA_CHANNEL_SIZE]; // ULD    energy skimming
# 	int blrclip     [MAX_DPP_PHA_CHANNEL_SIZE]; // Enable baseline restorer clipping
#     int dcomp       [MAX_DPP_PHA_CHANNEL_SIZE]; // tt_filter compensation
#     int trapbsl     [MAX_DPP_PHA_CHANNEL_SIZE]; // trapezoid baseline adjuster
# } CAEN_DGTZ_DPP_PHA_Params_t;
# 
# /*! 
#  * \brief DPP parameter structure to be initialized and passed to CAEN_DGTZ_SetDPPParameters
#  * \note Only for DPP-PSD
#  */
# typedef struct {
#     int blthr;
#     int bltmo;
#     int trgho;
#     int thr         [MAX_DPP_PSD_CHANNEL_SIZE];
#     int selft       [MAX_DPP_PSD_CHANNEL_SIZE];
#     int csens       [MAX_DPP_PSD_CHANNEL_SIZE];
#     int sgate       [MAX_DPP_PSD_CHANNEL_SIZE];
#     int lgate       [MAX_DPP_PSD_CHANNEL_SIZE];
#     int pgate       [MAX_DPP_PSD_CHANNEL_SIZE];
#     int tvaw        [MAX_DPP_PSD_CHANNEL_SIZE];
#     int nsbl        [MAX_DPP_PSD_CHANNEL_SIZE];
# 	int discr		[MAX_DPP_PSD_CHANNEL_SIZE];	//only for FW > 132.32
# 	int cfdf		[MAX_DPP_PSD_CHANNEL_SIZE]; //only for FW > 132.32
# 	int cfdd		[MAX_DPP_PSD_CHANNEL_SIZE]; //only for FW > 132.32
#     CAEN_DGTZ_DPP_TriggerConfig_t trgc // Ignored for x751
#                     [MAX_DPP_PSD_CHANNEL_SIZE];
#     CAEN_DGTZ_DPP_PUR_t purh; 
#     int purgap; // Ignored for x751
# } CAEN_DGTZ_DPP_PSD_Params_t;
# 
# 
# /*! 
#  * \brief DPP parameter structure to be initialized and passed to CAEN_DGTZ_SetDPPParameters
#  * \note Only for DPP-CI version 2
#  */
# typedef struct {
# 	int purgap;
# 	int purh;
#     int blthr;
#     int bltmo;
#     int trgho;
#     int thr     [MAX_DPP_CI_CHANNEL_SIZE];
#     int selft   [MAX_DPP_CI_CHANNEL_SIZE];
#     int csens   [MAX_DPP_CI_CHANNEL_SIZE];
#     int gate    [MAX_DPP_CI_CHANNEL_SIZE];
#     int pgate   [MAX_DPP_CI_CHANNEL_SIZE];
#     int tvaw    [MAX_DPP_CI_CHANNEL_SIZE];
#     int nsbl    [MAX_DPP_CI_CHANNEL_SIZE];
#     CAEN_DGTZ_DPP_TriggerConfig_t trgc
#                 [MAX_DPP_CI_CHANNEL_SIZE];
# } CAEN_DGTZ_DPP_CI_Params_t;
# 
# typedef struct {
#     int NSampBck        [MAX_ZLE_CHANNEL_SIZE];
#     int NSampAhe        [MAX_ZLE_CHANNEL_SIZE];
#     int ZleUppThr       [MAX_ZLE_CHANNEL_SIZE];
#     int ZleUndThr       [MAX_ZLE_CHANNEL_SIZE];
#     int selNumSampBsl   [MAX_ZLE_CHANNEL_SIZE];
#     int bslThrshld      [MAX_ZLE_CHANNEL_SIZE];
#     int bslTimeOut      [MAX_ZLE_CHANNEL_SIZE];
#     int preTrgg;
# } CAEN_DGTZ_751_ZLE_Params_t;
# 
# typedef struct {
#     CAEN_DGTZ_EnaDis_t  disableSuppressBaseline;
#     unsigned int        startCell[MAX_X743_CHANNELS_X_GROUP    * MAX_V1743_GROUP_SIZE];
#     unsigned short      chargeLength[MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE];
#     CAEN_DGTZ_EnaDis_t  enableChargeThreshold[MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE];
#     float               chargeThreshold    [MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE]; // in pC
# } CAEN_DGTZ_DPP_X743_Params_t;
# 
# 
# /*!
# * \brief DPP parameter structure to be initialized and passed to CAEN_DGTZ_SetDPPParameters
# * \note Only for DPP-QDC
# */
# typedef struct {
# 	int trgho[MAX_X740_GROUP_SIZE];
# 	int GateWidth[MAX_X740_GROUP_SIZE];
# 	int PreGate[MAX_X740_GROUP_SIZE];
# 	int FixedBaseline[MAX_X740_GROUP_SIZE];
# 	int DisTrigHist[MAX_X740_GROUP_SIZE];
# 	int DisSelfTrigger[MAX_X740_GROUP_SIZE];
# 	int BaselineMode[MAX_X740_GROUP_SIZE];
# 	int TrgMode[MAX_X740_GROUP_SIZE];
# 	int ChargeSensitivity[MAX_X740_GROUP_SIZE];
# 	int PulsePol[MAX_X740_GROUP_SIZE];
# 	int EnChargePed[MAX_X740_GROUP_SIZE];
# 	int TestPulsesRate[MAX_X740_GROUP_SIZE];
# 	int EnTestPulses[MAX_X740_GROUP_SIZE];
# 	int InputSmoothing[MAX_X740_GROUP_SIZE];
# 	int EnableExtendedTimeStamp;
# 
# } CAEN_DGTZ_DPP_QDC_Params_t;
# 
# typedef struct {
#     int16_t     cell[MAX_X742_CHANNEL_SIZE][1024];
#     int8_t      nsample[MAX_X742_CHANNEL_SIZE][1024];
#     float       time[1024];
# } CAEN_DGTZ_DRS4Correction_t;
# 
# typedef struct {
# 	float OffsetPedestal[MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE][1024];
# 	float INLPedestal[MAX_X743_CHANNELS_X_GROUP * MAX_V1743_GROUP_SIZE][1024];
# } CAEN_DGTZ_SAMCorrection_t;
# 
# typedef enum {
#     CAEN_DGTZ_SAM_CORRECTION_DISABLED       = 0,
#     CAEN_DGTZ_SAM_CORRECTION_PEDESTAL_ONLY  = 1,
#     CAEN_DGTZ_SAM_CORRECTION_INL            = 2,
#     CAEN_DGTZ_SAM_CORRECTION_ALL            = 3,
# } CAEN_DGTZ_SAM_CORRECTION_LEVEL_t;
# 
# #endif
