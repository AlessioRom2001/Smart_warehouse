
import json
import requests
import paho.mqtt.client as mqtt
import yaml
import threading
import time

# Dizionario globale per lo stato degli slot
slot_status = {}


CONF_FILE_PATH = "C:/Users/alexa/Desktop/Università/Magistrale/Distributed and IoT/D_Iot_project/V8/data_fetcher/app/fetcher_conf.yaml"


# Default Configuration Dictionary
configuration_dict = {
    "broker_ip": "my-mqtt-broker",
    "broker_port": 1883,
    "target_param_topic": "warehouse/config/param/#",
    "target_agv_topic": "warehouse/agv/#",
    "target_slots_topic": "warehouse/slots/#",
    "device_api_url": "http://127.0.0.1:7070/api/v1/iot/inventory/location/l0001/device"
}

# Read Configuration from target Configuration File Path
def read_configuration_file():
    global configuration_dict

    with open(CONF_FILE_PATH, 'r') as file:
        configuration_dict = yaml.safe_load(file)

    return configuration_dict

configuration_dict = read_configuration_file()

print("Read Configuration from file ({}): {}".format(CONF_FILE_PATH, configuration_dict))

# MQTT Broker Configuration
mqtt_broker_host = configuration_dict["broker_ip"]
mqtt_broker_port = configuration_dict["broker_port"]
mqtt_topic_parameters = configuration_dict["target_param_topic"]
mqtt_topic_agvs = configuration_dict["target_agv_topic"]
mqtt_topic_slots = configuration_dict["target_slots_topic"]

# HTTP API Configuration
api_url = configuration_dict["device_api_url"]

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code " + str(rc))
    client.subscribe(mqtt_topic_parameters)
    client.subscribe(mqtt_topic_agvs)
    client.subscribe(mqtt_topic_slots)
    
def on_message(client, userdata, msg):
    try:
        payload_dict = json.loads(msg.payload.decode())
        # Gestione parametri
        if mqtt.topic_matches_sub(mqtt_topic_parameters, msg.topic):
            print(f"[DEBUG] Received MQTT message on topic '{msg.topic}': {payload_dict}")
            type_to_param = {
                "shelves": "number_of_shelves",
                "columns": "columns_per_shelf",
                "levels": "levels_per_shelf",
                "agvs": "number_of_agvs"
            }
            parameter = payload_dict.get("type")
            if parameter in type_to_param:
                api_param = type_to_param[parameter]
                warehouse_param_url = f"{api_url}/{api_param}"
                print(f'Sending HTTP POST Request to: {warehouse_param_url}')
                param_payload = {
                    "value": payload_dict.get("value"),
                    "timestamp": payload_dict.get("timestamp"),
                    "data_type": payload_dict.get("data_type")
                }
                param_payload = {k: v for k, v in param_payload.items() if v is not None}
                response = requests.post(warehouse_param_url, json=param_payload)
                if response.status_code == 201:
                    print(f"Parameter {api_param} registered successfully.")
                else:
                    print(f"Failed to register parameter {api_param}. Status code: {response.status_code} Response: {response.text}")
                return
            # Caso 2: messaggio multiparametro senza 'type'
            multi_params = ["shelves", "columns", "levels", "agvs"]
            found = False
            import time
            for param in multi_params:
                if param in payload_dict:
                    found = True
                    api_param = type_to_param[param]
                    warehouse_param_url = f"{api_url}/{api_param}"
                    param_payload = {
                        "value": payload_dict[param],
                        "timestamp": time.time(),
                        "data_type": None
                    }
                    print(f'Sending HTTP POST Request to: {warehouse_param_url} (multi-param)')
                    response = requests.post(warehouse_param_url, json=param_payload)
                    if response.status_code == 201:
                        print(f"Parameter {api_param} registered successfully.")
                    else:
                        print(f"Failed to register parameter {api_param}. Status code: {response.status_code} Response: {response.text}")
            if not found:
                print(f"[ERROR] MQTT message missing 'type' field and no known parameters found: {payload_dict}")
        # Gestione posizione AGV
        if mqtt.topic_matches_sub(mqtt_topic_agvs, msg.topic):
            agv_id = payload_dict.get("agv_id")
            position = payload_dict.get("position")
            timestamp = payload_dict.get("timestamp")
            if agv_id is not None and position is not None:
                agv_position_url = f"{api_url}/agv/{agv_id}/position"
                pos_payload = {
                    "agv_id": agv_id,
                    "position": position,
                    "timestamp": timestamp
                }
                response = requests.post(agv_position_url, json=pos_payload)
                if response.status_code == 201:
                    print(f"Posizione AGV {agv_id} registrata correttamente.")
                else:
                    print(f"Errore registrazione posizione AGV {agv_id}. Status code: {response.status_code} Response: {response.text}")
            else:
                print(f"[ERROR] Messaggio posizione AGV non valido: {payload_dict}")
        # Gestione slot: aggiorna dizionario globale slot_status
        if mqtt.topic_matches_sub(mqtt_topic_slots, msg.topic):
            slot_id = payload_dict.get("slot_id")
            if slot_id is not None:
                slot_status[slot_id] = payload_dict
    except Exception as e:
        print(f"Error processing MQTT message: {str(e)}")


# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT Broker
client.connect(mqtt_broker_host, mqtt_broker_port, 60)


# Funzione per inviare periodicamente tutti gli slot all'API HTTP

def post_all_slots_periodically():
    print("[DEBUG] Thread di invio slot partito!")
    while True:
        try:
            print(f"[DEBUG] Stato attuale slot_status: {slot_status}")
            if slot_status:
                print(f"[DEBUG] Invio {len(slot_status)} slot all'API...")
                response = requests.post(
                    f"{api_url}/slots",
                    json={"slots": list(slot_status.values())}
                )
                print(f"POST slots: {response.status_code}")
            else:
                print("[DEBUG] Nessuno slot da inviare.")
        except Exception as e:
            print(f"Error posting slots: {e}")
        time.sleep(10)  # ogni 10 secondi

# Avvia il thread per la pubblicazione periodica
print("[DEBUG] Avvio thread per invio periodico slot...")
threading.Thread(target=post_all_slots_periodically, daemon=True).start()

# Avvia il loop MQTT (bloccante)
client.loop_forever()