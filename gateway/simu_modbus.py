#!/bin/python

from pyModbusTCP.server import ModbusServer, DeviceIdentification
from time import sleep
from random import uniform
import threading
from modbus_client import kaco_common_registry_map, kaco_tx3_registry_map
from itertools import chain
import time

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

class CustomModbusServer(threading.Thread):
    def __init__(self, host, port, slave_id, no_block=True):
        super().__init__()
        self.slave_id = slave_id 
        self.device_id = DeviceIdentification(objects_id=slave_id)
        self.server = ModbusServer(host, port, no_block, device_id=self.device_id)
        # self.server.data_bank.set_holding_registers(40001, [1,2])
        
        for entry_name, entry_info in chain(kaco_common_registry_map.items(), kaco_tx3_registry_map.items()):
            self.server.data_bank.set_holding_registers(entry_info.get('start_addr', 0), self.create_list(entry_info.get('size', 0)))
        self.port = port
    def run(self):  
        print(f"Start server for Slave {self.slave_id}...")
        self.server.start()
        print(f"Server for Slave {self.slave_id} is online")
        state = [0, 0]
        while True:
            for key, value in sunssf_registers.items():
                self.server.data_bank.set_holding_registers(value["start_addr"] - 1, [value["default"]])
                print(f"Address of SF value: {value['start_addr']}")
                print(f"Value: {[value['default']]}")

            for entry_name, entry_info in chain(kaco_common_registry_map.items(), kaco_tx3_registry_map.items()):
                start_addr = int(entry_info.get('start_addr', 0) - 1)
                type_modbus = str(entry_info.get('type', 'No type specified'))
                print(f"dia chi modbus: {start_addr}")  # Sử dụng 0 làm giá trị mặc định
                print(f"{entry_name}: {type_modbus}")
                print(f"mo ta : {entry_info.get('description', '')}")
                if  type_modbus == "uint32":
                    self.server.data_bank.set_holding_registers(start_addr, [int(uniform(25, 3500)), int(uniform(60, 100))])
                elif type_modbus == 'uint16':
                    self.server.data_bank.set_holding_registers(start_addr, [int(uniform(25, 3500))])
                elif type_modbus == "string":
                    default = entry_info.get('default', '') or '' 
                    ascii_values = [ord(char) for char in default]  # Chuyển mô tả thành giá trị ASCII
                    self.server.data_bank.set_holding_registers(start_addr, ascii_values)
                elif type_modbus == "int16":
                    self.server.data_bank.set_holding_registers(start_addr, [int(uniform(-32768, 32767))])
                elif type_modbus == "acc32":
                    self.server.data_bank.set_holding_registers(start_addr, [int(uniform(0, 65535)), int(uniform(0, 65535))])
                elif type_modbus == "enum16":
                    self.server.data_bank.set_holding_registers(start_addr, [int(uniform(1, 10))])
                elif type_modbus == "bitfield32":
                    self.server.data_bank.set_holding_registers(start_addr, [int(uniform(0, 65535)), int(uniform(0, 65535))])
                size_modbus = entry_info.get('size', 'No type specified')

                if size_modbus != None:
                    if state != self.server.data_bank.get_holding_registers(start_addr, size_modbus):
                        state = self.server.data_bank.get_holding_registers(start_addr, size_modbus)
                        print(f"Port [{self.port}]:Value of slave ID {self.slave_id} have changed to {state}")
            # self.server.data_bank.set_holding_registers(40001, [int(uniform(25, 3500)), int(uniform(60, 100))]) # id
            # self.server.data_bank.set_holding_registers(40005,  [ord(char) for char in 'KACO new energy'])
            # if state != self.server.data_bank.get_holding_registers(40001,2):
            #     state = self.server.data_bank.get_holding_registers(40001,2)
            #     print(f"[{self.port}] Values of Registers 0 and 1 for Slave {self.slave_id} have changed to {state}")
            sleep(10)

    def stop(self):
        print(f"Shutdown server for Slave {self.slave_id}...")
        self.server.stop()
        print(f"Server for Slave {self.slave_id} is offline")
    def create_list(self, n):
        return list(range(1, n+1))
# Create a list of CustomModbusServer instances with different slave IDs
servers = [
    CustomModbusServer("127.0.0.1", 10000 + i,i, no_block=True) for i in range(1, 5)
]

try:
    for server in servers:
        server.start()

    while True:
        sleep(1)

except KeyboardInterrupt:
    for server in servers:
        server.stop()

    print("All servers are offline")