from pyModbusTCP.client import ModbusClient
import random
import paho.mqtt.client as mqtt
import time
from logger import LOG
# Kaco TL3 Model Register Map
kaco_common_registry_map = {
    "SunSpec ID": {
        "start_addr": 40001,
        "size": 2,
        "type": "uint32",
        "description": "Uniquely identifies this as a SunSpec Modbus Map",
        "default": "0x53756e53",
        "attribute": True,
    },
    "SunSpec DID": {
        "start_addr": 40003,
        "size": 1,
        "type": "uint16",
        "description": "SunSpec Model ID",
        "default": "001",
        "attribute": True,
    },
    # ...to 40070
    "SunSpec Length": {
        "start_addr" : 40004,
        "size" : 1,
        "type" : "uint16",
        "description" : "Well registers to follow : 64",
        "default" : "64",
        "attribute" : True,
    },
    "Manufacturer" : {
        "start_addr" : 40005,
        "size" : 16,
        "type" : "string",
        "description" : None,
        "default" : "KACO new energy",
        "attribute" : True,
    },
    "Model" : {
        "start_addr" : 40021,
        "size" : 16,
        "type" : "string",
        "description" : "KACO inverter name",
        "default" : "Powador 39.0 TL3",
        "attribute" : True,
    },
    "Options": {
        "start_addr": 40037,
        "size": 8,
        "type": "string",
        "description": "Data logger ID-String",
        "default": "390TL",
        "attribute": True,
    },
    "Version": {
        "start_addr": 40045,
        "size": 8,
        "type": "string",
        "description": "The packet version of the currently installed software",
        "default": "V2.10",
        "attribute": True,
    },
    "Serial Number": {
        "start_addr": 40053,
        "size": 16,
        "type": "string",
        "description": "Serial number set during production process",
        "default": "39.0TL011 23456",
        "attribute": True,
    },
    "Device Address": {
        "start_addr": 40069,
        "size": 1,
        "type": "uint16",
        "description": "Not available.",
        "attribute": True,
        "in_use" : False
    },
}
kaco_tx3_registry_map = {
    "SunSpec Inverter ID": {
        "start_addr": 40071,
        "size": 1,
        "type": "uint16",
        "description": "Uniquely identifies this as a SunSpec Inverter (Three Phase) Model",
        "default": "103 (dec)",
        "attribute": True,
    },
    "Amps":{
        "start_addr": 40073,
        "size": 1,
        "type": "uint16",
        "description": "Sum of active phases",
        "unit": "A",
        "SF": "A_SF",
    },
    "Amps PhaseA":{
        "start_addr": 40074,
        "size": 1,
        "type": "uint16",
        "description": "Phase A Current",
        "unit": "A",
        "SF": "A_SF",
    },
    "Amps PhaseB":{
        "start_addr": 40075,
        "size": 1,
        "type": "uint16",
        "description": "Phase B Current",
        "unit": "A",
        "SF": "A_SF",
    },
    "Amps PhaseC":{
        "start_addr": 40076,
        "size": 1,
        "type": "uint16",
        "description": "Phase C Current",
        "unit": "A",
        "SF": "A_SF",
    },
    "Phase Voltage AB":{
        "start_addr": 40078,
        "size": 1,
        "type": "uint16",
        "description": "Optional / not supported",
        "unit": "V",
        "SF": "V_SF",
    },
    "Phase Voltage BC":{
        "start_addr": 40079,
        "size": 1,
        "type": "uint16",
        "description": "Optional / not supported",
        "unit": "V",
        "SF": "V_SF",
    },
    "Phase Voltage CA":{
        "start_addr": 40080,
        "size": 1,
        "type": "uint16",
        "description": "Optional / not supported",
        "unit": "V",
        "SF": "V_SF",
    },
    "Phase Voltage AN":{
        "start_addr": 40081,
        "size": 1,
        "type": "uint16",
        "description": "Voltage phase A to N",
        "unit": "V",
        "SF": "V_SF",
    },
    "Phase Voltage BN":{
        "start_addr": 40082,
        "size": 1,
        "type": "uint16",
        "description": "Voltage phase B to N",
        "unit": "V",
        "SF": "V_SF",
    },
    "Phase Voltage CN":{
        "start_addr": 40083,
        "size": 1,
        "type": "uint16",
        "description": "Voltage phase C to N",
        "unit": "V",
        "SF": "V_SF",
    },
    "Watts":{
        "start_addr": 40085,
        "size": 1,
        "type": "int16",
        "description": "Total AC Power",
        "unit": "W",
        "SF": "W_SF",
    },
    "Hz":{
        "start_addr": 40087,
        "size": 1,
        "type": "uint16",
        "description": "Line Frequency",
        "unit": "Hz",
        "SF": "Hz_SF",
    },
    "VA":{
        "start_addr": 40089,
        "size": 1,
        "type": "int16",
        "description": "AC Apparent Power",
        "unit": "VA",
        "SF": "VA_SF",
    },  
    "VAr":{
        "start_addr": 40091,
        "size": 1,
        "type": "int16",
        "description": "AC Reactive Power",
        "unit": "var",
        "SF": "VAr_SF",
    },
    "PF":{
        "start_addr": 40093,
        "size": 1,
        "type": "int16",
        "description": "AC Power Factor",
        "unit": "Pct",
        "SF": "PF_SF",
    },
    "WattHours":{
        "start_addr": 40095,
        "size": 2,
        "type": "acc32",
        "description": "AC Energy",
        "unit": "Wh",
        "SF": "WH_SF",
    },
    "DC Amps":{
        "start_addr": 40098,
        "size": 1,
        "type": "uint16",
        "description": "DC Current",
        "unit": "A",
        "SF": "DCA_SF",
    },
    "DC Voltage":{
        "start_addr": 40100,
        "size": 1,
        "type": "uint16",
        "description": "DC Voltage",
        "unit": "V",
        "SF": "DCV_SF",
    },
    "DC Watts":{
        "start_addr": 40102,
        "size": 1,
        "type": "int16",
        "description": "DC Power",
        "unit": "W",
        "SF": "DCW_SF",
    },
    "Cabinet Temperature":{
        "start_addr": 40104,
        "size": 1,
        "type": "int16",
        "description": "Cabinet Temperature",
        "unit": "C",
        "SF": "Tmp_SF",
    },
    "Heat Sink Temperature":{
        "start_addr": 40105,
        "size": 1,
        "type": "int16",
        "description": "Optional / not supported",
        "unit": "C",
        "SF": "Tmp_SF",
        "in_use": False,
    },
    "Transformer Temperature":{
        "start_addr": 40106,
        "size": 1,
        "type": "int16",
        "description": "Optional / not supported",
        "unit": "C",
        "SF": "Tmp_SF",
        "in_use": False,
    },
    "Other Temperature":{
        "start_addr": 40107,
        "size": 1,
        "type": "int16",
        "description": "Optional / not supported",
        "unit": "C",
        "SF": "Tmp_SF",
        "in_use": False,
    },

    "Operating State": {
        "start_addr": 40109,
        "size": 1, 
        "type": "enum16",
        "description": "Enumerated value. Operating state.",
    },
    "Vendor Operating State": {
        "start_addr": 40110,
        "size": 1,
        "type": "enum16",
        "description": "KACO Powador-proLOG Status Description in [3]",
    },
    "Event1": {
        "start_addr": 40111,
        "size": 2,
        "type": "bitfield32",
        "description": "Bitmask value. Event fields",
    },
    "Event Bitfield 2": {
        "start_addr": 40113,
        "size": 2,
        "type": "bitfield32",
        "description": "Reserved for future use (Not used)",
        "in_use": False,
    },
    "Vendor Event Bitfield 1": {
        "start_addr": 40115,
        "size": 2,
        "type": "bitfield32",
        "description": "Optional / not supported",
        "in_use": False,
    },
    "Vendor Event Bitfield 2": {
        "start_addr": 40117,
        "size": 2,
        "type": "bitfield32",
        "description": "Optional / not supported",
        "in_use": False,
    },  
    "Vendor Event Bitfield 3": {
        "start_addr": 40119,
        "size": 2,
        "type": "bitfield32",
        "description": "Optional / not supported",
        "in_use": False,
    },
    "Vendor Event Bitfield 4": {
        "start_addr": 40121,
        "size": 2,
        "type": "bitfield32",
        "description": "Optional / not supported",
        "in_use": False,
    },
}

sunssf_registers = {
    "A_SF": {"start_addr": 40077, "default": -2},
    "V_SF": {"start_addr": 40084, "default": -1},
    "W_SF": {"start_addr": 40086, "default": 1},
    "Hz_SF": {"start_addr": 40088, "default": -1},
    "VA_SF": {"start_addr": 40090, "default": 1},
    "VAr_SF": {"start_addr": 40092, "default": 1},
    "PF_SF": {"start_addr": 40094, "default": -1},
    "WH_SF": {"start_addr": 40097, "default": 0},
    "DCA_SF": {"start_addr": 40099, "default": -2},
    "DCV_SF": {"start_addr": 40101, "default": -1},
    "DCW_SF": {"start_addr": 40103, "default": 1},
    "Tmp_SF": {"start_addr": 40108, "default": -1},
}
enum_operating_state_registers = {
    1: "Off",
    2: "Sleeping",
    3: "Starting",
    4: "Mppt",
    5: "Throttled",
    6: "Shutting Down",
    7: "Fault",
    8: "Standby",
}

GROUND_FAULT=(0x01 << 0)
DC_OVER_VOLT=(0x01 << 1)
AC_DISCONNECT=(0x01 << 2)
DC_DISCONNECT=(0x01 << 3)
GRID_DISCONNECT=(0x01 << 4)
CABINET_OPEN=(0x01 << 5)
MANUAL_SHUTDOWN=(0x01 << 6)
OVER_TEMP=(0x01 << 7)
OVER_FREQUENCY=(0x01 << 8)
UNDER_FREQUENCY=(0x01 << 9)
AC_OVER_VOLT=(0x01 << 10)
AC_UNDER_VOLT=(0x01 << 11)
BLOWN_SRING_FUSE=(0x01 << 12)
UNDER_TEMP=(0x01 << 13)
MEMORY_LOSS=(0x01<< 14)
HW_TEST_FAILURE=(0x01 << 15)

def calculate_real_value(received_value, sf, do_round=True):
    if do_round:
        return round(received_value * (10**sf), 2)
    return received_value * (10**sf)

def get_sunssf_registers_value(sf:dict, name: str):
    return sf.get(name, 0)


def get_sunssf_registers_value_modbus(modbus_client: ModbusClient, sf_data: str):
    return kako_convert_int16(
        modbus_client.read_holding_registers(
            convert_address_modbus_tcp(sf_data["start_addr"]), 1
        )
    )


def read_all_scale_factors_from_slave(modbus_client: ModbusClient):
    sf = dict()
    for sf_name, sf_data in sunssf_registers.items():
        ret, new_value = get_sunssf_registers_value_modbus(modbus_client, sf_data)
        if ret:
            LOG.debug((f'{sf_name}: {sf_data["default"]} -> {new_value}'))
        # sunssf_registers[name]["default"] = new_value
            sf[sf_name] = new_value
    return sf


def convert_address_modbus_tcp(address):
    return address - 1

def read_all_attributes_from_slave(modbus_client: ModbusClient):
    modbus_attributes = []
    modbus_attributes_dict = dict()

    for _name, fields in kaco_common_registry_map.items():
        if fields.get('attribute', False) and fields.get('in_use', True):
            msg = f"Reading attribute [{_name}]"
            values_register = modbus_client.read_holding_registers(
                        convert_address_modbus_tcp(fields["start_addr"]), fields["size"]
                    )
            if values_register:
                ret, _value = convert_data_type(
                    values_register,
                    fields["type"],
                )
                if ret:
                    msg += f" -> {_value}"
                    LOG.debug(msg)
                    modbus_attributes_dict[_name] = _value
                    modbus_attributes.append(_value)
                else:
                    LOG.error((f'Error: Cannot convert data for {_name}, values_register: {values_register}'))
            else:
                LOG.error((f'Error: Cannot read data for {_name}, start_addr: {fields["start_addr"]}'))

    return modbus_attributes, modbus_attributes_dict

def read_all_data_needed_from_slave(modbus_client: ModbusClient, sf: dict=None, last_modbus_data_dict: dict={}):
    modbus_data = list()
    modbus_data_dict = dict()
    units = dict()
    for kaco_registry_map in [kaco_common_registry_map, kaco_tx3_registry_map]:
        for _name, fields in kaco_registry_map.items():
            if not fields.get('attribute', False) and fields.get('in_use', True):
                msg = f"Reading [{_name}]"
                values_register = modbus_client.read_holding_registers(
                        convert_address_modbus_tcp(fields["start_addr"]), fields["size"]
                    )
                if values_register:
                    ret, _value = convert_data_type(
                        values_register,
                        fields["type"],
                    )
                    if ret:
                        if 'SF' in fields.keys():
                            msg += f" -> Raw:{_value}"
                            _value = calculate_real_value(_value, get_sunssf_registers_value(sf, fields['SF']))
                        msg += f" -> {_value} {fields.get('unit', '')}"
                        LOG.debug(msg)
                        update_value = True
                        if _name in ['Operating State', 'Vendor Operating State', 'Event1', 'PF', 'VAr', 'Hz']:
                            if _name in last_modbus_data_dict and last_modbus_data_dict[_name] != _value:
                                LOG.debug("Update new {_name}:{last_modbus_data_dict[_name]}->{_value}")
                                last_modbus_data_dict[_name] = _value
                            else:
                                update_value = False
                        if update_value:
                            modbus_data_dict[_name] = _value
                            units[_name] = fields.get('unit', '')
                            modbus_data.append(_value)
                    else:
                        LOG.error((f'Error: Cannot convert data for {_name}, values_register: {values_register}'))
                else:
                    LOG.error((f'Error: Cannot read data for {_name}, start_addr: {fields["start_addr"]}'))

    return modbus_data, modbus_data_dict, units


def convert_data_type(data, data_type):
    if data_type == "uint16":
        return kako_convert_uint16(data)
    elif data_type == "int16":
        return kako_convert_int16(data)
    elif data_type == "uint32":
        return kako_convert_uint32(data)
    elif data_type == "int32":
        return kako_convert_int32(data)
    elif data_type == "acc32":
        return kako_convert_acc32(data)
    elif data_type == "bitfield32":
        return kako_convert_bitfield32(data)
    elif data_type == "ipv4":
        return kako_convert_to_ipv4(data)
    elif data_type == "string":
        return kako_convert_string(data)
    elif data_type == "enum16":
        return kako_convert_uint16(data)
    else:
        return False, data


# Chuyển đổi giá trị nhận được
def kako_convert_string(data: list):  # [[byte, byte],[byte, byte],[byte, byte] , ....]
    text = ""
    if data:
        for d in data:
            char_array = bytearray(d.to_bytes(2, "big"))
            text += chr(char_array[0])
            text += chr(char_array[1])
        return True, text
    else:
        error = 'Invalid data for string conversion'
        LOG.error((error))
    return False, error


def kako_convert_int16(data: list):  # expect len = 1
    if data and len(data) == 1:
        int16 = data[0]
        if int16 & 0x8000:  # Check if the value is negative in int16
            int16 = int16 - 0x10000
        return True, int16
    else:
        LOG.error(("Error: wrong SunSpec int16 length"))
        error = "Error: wrong SunSpec int16 length"
        return False, error


def kako_convert_uint16(data: list):  # expect len = 1
    if data and len(data) == 1:
        uint16 = data[0]
        return True, uint16
    else:
        LOG.error(("Error: wrong SunSpec uint16 length"))
        return False, "Error: wrong SunSpec uint16 length"


def kako_convert_int32(data: list):  # expect len = 2
    if data and len(data) == 2:
        int32 = (data[0] << 16) | data[1]
        if int32 & 0x80000000:
            int32 = int32 - 0x100000000
        return True, int32
    else:
        LOG.error(("Error: wrong SunSpec int32 length"))
        return False, "Error: wrong SunSpec int32 length"


def kako_convert_uint32(data: list):  # expect  len = 2
    if data and len(data) == 2:
        uint32 = (data[0] << 16) + data[1]
        return True, uint32
    else:
        error = "Error: wrong SunSpec _uint32 length"
        LOG.error((error))
    return False, error


def kako_convert_acc32(data: list):
    if data and len(data) == 2:
        acc32 = (data[0] << 16) | data[1]
        return True, acc32
    else:
        LOG.error(("Error: wrong SunSpec _acc32 length"))
        return False, "Error: wrong SunSpec_acc32 length"


def kako_convert_bitfield32(data: list):  # expect  len = 2
    if data and len(data) == 2:
        bitfield32 = (data[0] << 16) | data[1]
        return True, bitfield32
    else:
        LOG.error(("Error: wrong SunSpec_bitfield32 length"))
        error = "Error: wrong SunSpec_bitfield32 length"
        return False, error


def kako_convert_to_ipv4(data: list):  # expect len = 2
    if data and len(data) == 2:
        # Mỗi phần tử 16-bit được chia thành hai phần tử 8-bit và chuyển đổi thành giá trị decimal
        ip_parts = [
            (data[0] >> 8) & 0xFF,  # High byte of the first register
            data[0] & 0xFF,  # Low byte of the first register
            (data[1] >> 8) & 0xFF,  # High byte of the second register
            data[1] & 0xFF,  # Low byte of the second register
        ]
        # Tạo chuỗi địa chỉ IP từ các phần
        ip_address = ".".join(str(part) for part in ip_parts)
        return True, ip_address
    else:
        LOG.error(("Error: wrong length for IPv4 conversion"))
        return False, "0.0.0.0"





def kaco_parse_sunspect_id(data):
    # parse SunSpec ID
    if data and len(data) == 2:
        return kako_convert_uint32(data)
    else:
        LOG.error(("Error: wrong SunSpec ID length"))
        return False, "Error: wrong SunSpec ID length"

def SIMU_read_data_from_slave(server_ip, port=502, slave_id=1):

    modbus_data = [random.random() for _ in range(5)]
    modbus_data_dict = {
        "Amps": modbus_data[0],
        "Amps PhaseA": modbus_data[1],
        "Amps PhaseB": modbus_data[2],
        "Amps PhaseC": modbus_data[3],
        "Phase Voltage AN": modbus_data[4],
    }
    units = {
        "Amps": "A",
        "Amps PhaseA": "A",
        "Amps PhaseB": "A",
        "Amps PhaseC": "A",
        "Phase Voltage AN": "V",
    }
    return modbus_data, modbus_data_dict, units
def SIMU_read_attributes_from_slave(server_ip, port=502, slave_id=1):
    modbus_data =[random.random() for _ in range(5)]
    modbus_data_dict = {
        "SunSpec ID": modbus_data[0],
        "SunSpec DID": modbus_data[1],
        "SunSpec Length": modbus_data[2],
        "Manufacturer": modbus_data[3],
        "Model": modbus_data[4],
    }
    return modbus_data, modbus_data_dict


def read_data_from_slave(server_ip, port=502, slave_id=1, last_modbus_data_dict: dict={}):
    LOG.info((f"\nReading data from {server_ip}"))
    modbus_client = ModbusClient(host=server_ip, port=port, unit_id=slave_id)
    sf = read_all_scale_factors_from_slave(modbus_client)
    return read_all_data_needed_from_slave(modbus_client, sf, last_modbus_data_dict=last_modbus_data_dict)

def read_attributes_from_slave(server_ip, port=502, slave_id=1):
    LOG.info((f"\nReading attributes from {server_ip}"))
    modbus_client = ModbusClient(host=server_ip, port=port, unit_id=slave_id)
    return read_all_attributes_from_slave(modbus_client)

# if __name__ == "__main__":

#     server_ip = "127.0.0.1"

#     # Danh sách các cổng (ports) mà các slave đang chạy
#     server_ports = [10001, 10002]#, 12346, 12347, 12348, 12349]

#     # ID của các slave
#     slave_ids = [1, 2]#, 2, 3, 4, 5]

#     try:
#         while True:
#             list_devices = [str('kaco'+str(id)) for id in slave_ids]
#             for port, slave_id, device in zip(server_ports, slave_ids, list_devices):
#                 print(f'server_port: {port}')
#                 modbus_data, modbus_data_dict= read_data_from_slave(server_ip, port, slave_id)
#                 if modbus_data:
#                     LOG.info(f"Modbus Data: {len(modbus_data_dict)}")
#                     for key,value in modbus_data_dict.items():
#                         LOG.info(f"{key}: {value}")
#                 else:
#                     LOG.info("No Modbus Data")
#             time.sleep(50)
#     except KeyboardInterrupt:
#         LOG.info("Client stopped.")
