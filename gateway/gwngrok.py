# import ngrok python sdk
# import ngrok
import time
from datetime import datetime
from tb_gateway_mqtt import TBGatewayMqttClient
from pyngrok import ngrok
from config import NGROK_TOKEN, MQTT_SERVER, GATEWAY_TOKEN

url_shh = None
authtoken = NGROK_TOKEN
ngrok.set_auth_token(authtoken)


def on_ngrok_cfg(result, exception):
    global url_shh
    if exception is not None:
        print("Exception:", str(exception))
    else:
        print(f"[on_ngrok_cfg] {result}")
        try:
            ssh_tunnel = ngrok.connect("22", "tcp")
            print(ssh_tunnel)
            url_shh = str(ssh_tunnel)
        except Exception as e:
            print(e)


def on_attributes_change(result, exception):
    if exception is not None:
        print("Exception:", str(exception))
    else:
        print(f"[on_attributes_change] {result}")


ssh_tunnel = ngrok.connect("22", "tcp")
print(ssh_tunnel)
url_shh = str(ssh_tunnel)
rasp_token = GATEWAY_TOKEN
rasp_mqtt_client = TBGatewayMqttClient(MQTT_SERVER, 1883, rasp_token)
rasp_mqtt_client.connect()
rasp_mqtt_client.send_telemetry(
    {"time": datetime.now().strftime("%y%m%d_%H%M%S"), "url_shh": url_shh}
)
# rasp_mqtt_client.request_attributes(["ngrok_cfg"], callback=on_attributes_change)
rasp_mqtt_client.subscribe_to_attribute("ngrok_cfg", on_ngrok_cfg)
# Output ngrok url to console

while True:
    while not rasp_mqtt_client.is_connected():
        try:
            print("Connecting mqtt server...", end="")
            rasp_mqtt_client.connect()
            print("OK")
            time.sleep(5)
        except Exception as e:
            print(e)
    try:
        rasp_mqtt_client.send_telemetry(
            {"time": datetime.now().strftime("%y%m%d_%H%M%S"), "url_shh": url_shh},
            quality_of_service=1,
        )
    except Exception as e:
        print(e)
    time.sleep(6)
    pass
