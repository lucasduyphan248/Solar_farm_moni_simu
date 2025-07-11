from datetime import datetime, date
from datetime import time as dttime

import time
from tb_gateway_mqtt import TBGatewayMqttClient
from modbus_client import (
    SIMU_read_data_from_slave,
    SIMU_read_attributes_from_slave,
    read_data_from_slave,
    read_attributes_from_slave,
    slave_is_online,
)
import shutil
import psutil
import socket
import requests
import random
from logger import LOG
from config import (
    SERVER_IPS,
    GATEWAY_TOKEN,
    MQTT_SERVER,
    TIME_WAIT_S,
    TIME_WAIT_READ_ATTRIBUTE_N,
)
import requests


print("Hello from Raspberry Pi")


def get_location():
    url = "http://ip-api.com/json"
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        lat = result["lat"]
        lng = result["lon"]
        country = result["country"]
        region = result["regionName"]
        return lat, lng, country, region
    else:
        print("Error:", response.status_code)
        return None


def get_disk_usage(path):
    try:
        total, used, free = shutil.disk_usage(path)
        total = total / (1024**3)
        used = used / (1024**3)
        free = free / (1024**3)
        used_percent = used / total * 100
        return {
            "path": path,
            "total": f"{total:.2f} GB",
            "used": f"{used:.2f} GB",
            "free": f"{free:.2f} GB",
            "used_percent": f"{used_percent:.2f} %",
        }
    except Exception as e:
        return {}


def gw_get_info():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        rasp_cpu_percent = psutil.cpu_percent(4)
        rasp_ram_percent = psutil.virtual_memory()[2]
        rasp_ram_used_mb = psutil.virtual_memory()[3] / 1000000
        disk = get_disk_usage("/home/pi")
        lat, lng, country, region = get_location()
    except Exception as e:
        LOG.info((e))
        (
            hostname,
            ip_address,
            rasp_cpu_percent,
            rasp_ram_percent,
            rasp_ram_used_mb,
            disk,
        ) = ("", "", 0, 0, 0, {})
    return (
        hostname,
        ip_address,
        rasp_cpu_percent,
        rasp_ram_percent,
        rasp_ram_used_mb,
        disk,
        (lat, lng, country, region),
    )


(
    hostname,
    ip_address,
    rasp_cpu_percent,
    rasp_ram_percent,
    rasp_ram_used_mb,
    _,
    locations,
) = gw_get_info()
LOG.info((f"Hostname: {hostname}"))
LOG.info((f"IP Address: {ip_address}"))
LOG.info(("The CPU usage is: ", rasp_cpu_percent))
# Getting % usage of virtual_memory ( 3rd field)
LOG.info(("RAM memory % used:", rasp_ram_percent))
# Getting usage of virtual_memory in GB ( 4th field)
LOG.info(("RAM Used (GB):", rasp_ram_used_mb))
LOG.info((f"Location: {locations}"))


def on_attributes_change(result, exception):
    if exception is not None:
        LOG.info(("Exception:", str(exception)))
    else:
        LOG.info((result))


def tb_join_parameters(params: list):
    return ",".join(params)


class RaspGateway:
    def __init__(self, list_devices_dict: dict, gateway_token: str) -> None:
        LOG.info((("RaspGateway init", gateway_token)))
        self.gw_token = gateway_token
        self.gw_name = ""
        self.gw_id = ""
        self.list_devices_dict = list_devices_dict
        self.gateway_mqtt_client = TBGatewayMqttClient(MQTT_SERVER, 1883, self.gw_token)
        atts = self.get_share_attributes(sharedKeys=["tb_name", "tb_id"])
        if "tb_name" in atts:
            tb_name = atts.get("tb_name")
            self.gw_name = tb_name
        if "ib_id" in atts:
            tb_id = atts.get("tb_id")
            self.gw_id = tb_id

    def get_share_attributes(self, sharedKeys=None):
        a = self.get_attributes_by_http(sharedKeys=sharedKeys)
        if "shared" in a:
            return a["shared"]
        return {}

    def get_attributes_by_http(self, clientKeys: list = None, sharedKeys: list = None):
        # curl -v -X GET http://$THINGSBOARD_HOST_NAME/api/v1/$ACCESS_TOKEN/attributes?clientKeys=attribute1,attribute2&sharedKeys=shared1,shared2
        base_url = f"http://{MQTT_SERVER}:8080/api/v1/{GATEWAY_TOKEN}/attributes"
        params = dict()
        if clientKeys:
            params["clientKeys"] = tb_join_parameters(clientKeys)
        if sharedKeys:
            params["sharedKeys"] = tb_join_parameters(sharedKeys)
        r = requests.get(base_url, params=params)
        if r.status_code == 200:
            LOG.info(("get_attributes_by_http successful: "))
            LOG.info((r.json()))
            return r.json()
        LOG.info(("get_attributes_by_http Error: %s" % r.status_code))
        return {}

    def get_remote_devices_name(self, local_device_name=None):
        if local_device_name:
            LOG.debug(
                f"get_remote_devices_name:{local_device_name}->{self.list_devices_dict.get(local_device_name,'')}"
            )
            return self.list_devices_dict.get(local_device_name, "")
        return self.list_devices_dict

    def add_local_devices(self, devices: list):
        self.local_devices_name = devices

    def connect(self, retry=3):
        while retry > 0:
            try:
                self.gateway_mqtt_client.connect()
                if self.gateway_mqtt_client.is_connected():
                    if not self.list_devices_dict:
                        for device in self.local_devices_name:
                            self.list_devices_dict[device] = f"{self.gw_name}_{device}"
                    for local_name, remote_name in self.list_devices_dict.items():
                        LOG.info((f"Init device: {local_name}->{remote_name}"))
                        self.gateway_mqtt_client.gw_connect_device(remote_name)
                    retry = 0
                    return
                else:
                    LOG.info((f"Connecting to MQTT server failed: {retry}"))
                    self.gateway_mqtt_client.connect()
                    retry -= 1
            except Exception as e:
                LOG.error((f"Connect failed: {e}"))
            time.sleep(10)

    def is_connected(self):
        return self.gateway_mqtt_client.is_connected()

    def send_telemetry(self, telemetry):
        self.gateway_mqtt_client.send_telemetry(telemetry)

    def gw_push_data(self, device, data):
        """
        use GW to data to device
        """
        LOG.info((f"Pushing data to {device}, len = {len(data)}"))
        self.gateway_mqtt_client.gw_send_telemetry(device, data)

    def gw_send_attributes(self, device, attributes):
        self.gateway_mqtt_client.gw_send_attributes(device, attributes)

    def gw_update_hardware_info(self):
        (
            hostname,
            ip_address,
            rasp_cpu_percent,
            rasp_ram_percent,
            rasp_ram_used_mb,
            disk,
            locations,
        ) = gw_get_info()
        data = {
            "hostname": hostname,
            "ip_address": ip_address,
            "disk": disk,
            "rasp_cpu_percent": rasp_cpu_percent,
            "rasp_ram_percent": rasp_ram_percent,
            "rasp_ram_used_mb": rasp_ram_used_mb,
            "latitude": locations[0],
            "longitude": locations[1],
            "country": locations[2],
            "province": locations[3],
        }
        LOG.info("GwUpdateHardwareInfo")
        LOG.info(data)
        self.gateway_mqtt_client.send_attributes(data)

def apply_filter(data, filter):
    new_dict = data.copy()
    for key in filter:
        if key in new_dict:
            del new_dict[key]
    return new_dict
rasp_gateway = RaspGateway({}, GATEWAY_TOKEN)
if __name__ == "__main__":
    server_ips = SERVER_IPS

    # Danh sách các cổng (ports) mà các slave đang chạy
    server_ports = 502

    # ID của các slave
    slave_ids = 1
    time_read_telemetry = TIME_WAIT_READ_ATTRIBUTE_N+1
    last_modbus_datas_dict = dict()  # dict [server][data]
    reset_last_modbus_datas_dict = {"value": False, "dt": datetime.now()}
    while True:
        try:
            # need scan device , assign name
            local_devices_name = [f"kaco_{ip}" for ip in server_ips]  # local name
            if not rasp_gateway.is_connected():
                rasp_gateway.add_local_devices(local_devices_name)
                rasp_gateway.connect()
                rasp_gateway.gw_update_hardware_info()
                remote_devices_name = rasp_gateway.get_remote_devices_name()
                LOG.info(f"remote_devices_name: {remote_devices_name.items()}")
                for local_device_name, server_ip in zip(local_devices_name, server_ips):
                    rasp_gateway.gw_send_attributes(
                        rasp_gateway.get_remote_devices_name(local_device_name),
                        {
                            "ip_address": server_ip,
                        },
                    )
            if not rasp_gateway.is_connected():
                LOG.error(("Gateway not connected"))
                time.sleep(5)
                continue
            # check device online
            server_ips_online = []
            for local_device_name, server_ip in zip(local_devices_name, server_ips):
                if slave_is_online(server_ip):
                    server_ips_online.append(server_ip)
            LOG.info(f"server_ips_online: {server_ips_online}")
            # Read attributes of kaco
            if time_read_telemetry > TIME_WAIT_READ_ATTRIBUTE_N:
                time_read_telemetry = 0
                for local_device_name, server_ip in zip(local_devices_name, server_ips_online):
                    LOG.debug((">>> Read attribute from slave: ", server_ip))
                    # modbus_attributes, modbus_attributes_dict = SIMU_read_attributes_from_slave(server_ip)
                    modbus_attributes, modbus_attributes_dict = (
                        read_attributes_from_slave(server_ip)
                    )
                    if modbus_attributes:
                        LOG.debug(
                            (f"Modbus Attribute Length: {len(modbus_attributes_dict)}")
                        )
                        for key, value in modbus_attributes_dict.items():
                            LOG.debug((f"Attribute `{key}`: {value}"))
                        if rasp_gateway.is_connected():
                            rasp_gateway.gw_send_attributes(
                                rasp_gateway.get_remote_devices_name(local_device_name),
                                modbus_attributes_dict,
                            )
                    else:
                        LOG.warning((f"No Modbus Attribute ip: {server_ip} -> maybe offline"))
                    LOG.debug(("<<<"))
            # Read telemetry
            aggregate = [
                {
                    "name": "sum_watts",
                    "field": "Watts",
                    "eq": "sum",
                    "value": 0,
                    "unit": "W",
                    "count": 0 # number device calculated
                },
                {
                    "name": "sum_watt_hours",
                    "field": "WattHours",
                    "eq": "sum",
                    "value": 0,
                    "unit": "Wh",
                    "count": 0 
                }
            ]
            for local_device_name, server_ip in zip(local_devices_name, server_ips_online):
                LOG.info(("Read telemetry from slave: ", server_ip))
                # modbus_data, modbus_data_dict, units = SIMU_read_data_from_slave(server_ip)
                if server_ip not in last_modbus_datas_dict:
                    last_modbus_datas_dict[server_ip] = {}
                current_timenow = datetime.now()
                target_time = dttime(4, 0, 0)  # Set the target time to 4:00:00 AM
                if current_timenow.time() > target_time:
                    print("The current time is later than 4:00 AM.")
                    # clean data
                    if not reset_last_modbus_datas_dict["value"]:
                        last_modbus_datas_dict[server_ip] = {}
                        reset_last_modbus_datas_dict = {
                            "value": True,
                            "dt": datetime.now(),
                        }
                    if (
                        current_timenow.date()
                        > reset_last_modbus_datas_dict["dt"].date()
                    ):
                        reset_last_modbus_datas_dict = {
                            "value": False,
                            "dt": datetime.now(),
                        }
                modbus_data, modbus_data_dict, units = read_data_from_slave(
                    server_ip, last_modbus_data_dict=last_modbus_datas_dict[server_ip]
                )
                if modbus_data:
                    LOG.debug((f"Modbus Data Length: {len(modbus_data_dict)}"))
                    for agg in aggregate:
                        if agg["eq"] == "sum":
                            value = modbus_data_dict.get(agg["field"], 0)
                            if value >= 0:
                                agg["value"] += value
                                agg["count"] += 1
                        # TODO dung thuat toan hay hon de tinh tong
                    for key, value in modbus_data_dict.items():
                        LOG.info((f"{key}: {value} {units.get(key, '')}"))
                    if datetime.now().time() > dttime(19, 0) or datetime.now().time() < dttime(3, 0):
                        filter_data_by_time = ['Amps', 'Amps PhaseA', 'Amps PhaseB', 'Amps PhaseC', 'DC Amps', 'DC Voltage', 'DC Watts','VA', 'Watts', 'WattHours','Operating State', 'Vendor Operating State', 'Event1', 'PF', 'VAr', 'Hz']
                        modbus_data_dict = apply_filter(data=modbus_data_dict, filter=filter_data_by_time)

                    if rasp_gateway.is_connected():
                        rasp_gateway.gw_push_data(
                            rasp_gateway.get_remote_devices_name(local_device_name),
                            modbus_data_dict,
                        )
                else:
                    LOG.warning(("No Modbus Data"))
                LOG.info(("-----------"))
            # GateWay
            for agg in aggregate:
                if rasp_gateway.is_connected():
                    LOG.info((f' sending telemetry {agg["name"]}: {agg["value"]}'))
                    if agg["count"] == len(server_ips_online):
                        rasp_gateway.send_telemetry({agg["name"]: agg["value"]})
            LOG.info(("==============================="))
            time_read_telemetry += 1
        except KeyboardInterrupt:
            LOG.error(("Client stopped."))
        time.sleep(TIME_WAIT_S)
