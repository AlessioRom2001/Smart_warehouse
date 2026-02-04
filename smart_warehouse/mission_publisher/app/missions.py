import json
import time
import networkx as nx
from path_algorithm import PathAlgorithm
from pallet_scheduler import PalletScheduler
import paho.mqtt.client as mqtt

MISSIONS_TOPIC = "warehouse/missions"
missions = []

# Topics as described in generate_warehouse.py
PALLET_SPAWN_TOPIC = "warehouse/pallet_spawn_nodes"
AGV_START_TOPIC = "warehouse/config/agv_start_nodes"
SHIPPING_TOPIC = "warehouse/config/shipping_nodes"
GRAPH_TOPIC = "warehouse/config/graph_json"


# Data containers
warehouse_data = {
    "pallet_spawn_nodes": None,
    "agv_start_nodes": None,
    "shipping_nodes": None,
    "graph": None
}
# Slot data container
warehouse_slots = []


# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code", rc)
    client.subscribe([
        (PALLET_SPAWN_TOPIC, 1),
        (AGV_START_TOPIC, 1),
        (SHIPPING_TOPIC, 1),
        (GRAPH_TOPIC, 1)
    ])
    # Subscribe to all slots
    client.subscribe(("warehouse/slots/#", 1))


def on_message(client, userdata, msg):
    topic = msg.topic
    # Gestione slot
    if topic.startswith("warehouse/slots/"):
        try:
            slot = json.loads(msg.payload.decode())
            # Aggiorna o aggiungi slot
            slot_id = slot.get("slot_id")
            # Sostituisci se già presente
            for i, s in enumerate(warehouse_slots):
                if s.get("slot_id") == slot_id:
                    warehouse_slots[i] = slot
                    break
            else:
                warehouse_slots.append(slot)
            print(f"Received slot {slot_id}")
        except Exception as e:
            print(f"Error decoding slot: {e}")
        return
    # Other topics
    payload = json.loads(msg.payload.decode())
    if topic == PALLET_SPAWN_TOPIC:
        warehouse_data["pallet_spawn_nodes"] = payload.get("pallet_spawn_nodes")
        print("Received pallet spawn nodes:", warehouse_data["pallet_spawn_nodes"])
    elif topic == AGV_START_TOPIC:
        warehouse_data["agv_start_nodes"] = payload.get("agv_start_nodes")
        print("Received AGV start nodes:", warehouse_data["agv_start_nodes"])
    elif topic == SHIPPING_TOPIC:
        warehouse_data["shipping_nodes"] = payload.get("shipping_nodes")
        print("Received shipping nodes:", warehouse_data["shipping_nodes"])
    elif topic == GRAPH_TOPIC:
        if "graph" in payload:
            warehouse_data["graph"] = nx.node_link_graph(payload["graph"])
            print("Received warehouse graph from broker.")



def wait_for_all_data(timeout=5, min_slots=1):
    start = time.time()
    while time.time() - start < timeout:
        if all(v is not None for v in warehouse_data.values()) and len(warehouse_slots) >= min_slots:
            return True
        time.sleep(0.1)
    return False


def retrieve_warehouse_nodes_and_slots(broker="my-mosquitto-broker", port=1883, min_slots=1):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port, 60)
    client.loop_start()

    # Wait for all data to be received or timeout
    success = wait_for_all_data(timeout=10, min_slots=min_slots)
    client.loop_stop()
    client.disconnect()
    if not success:
        print("Timeout: Not all warehouse node/slot data received.")
    return warehouse_data, warehouse_slots



if __name__ == "__main__":
    nodes, slots = retrieve_warehouse_nodes_and_slots(min_slots=1)
    print("Final warehouse node data:", nodes)
    print("Final warehouse slots:", slots)
    # MQTT topics for order and pallet signals
    ORDER_TOPIC = "warehouse/order"
    PALLET_TOPIC = "warehouse/pallet"

    # Use the graph retrieved from the broker
    warehouse_graph = nodes["graph"]

    # Choose AGV start and spawning node (for demo, pick the first available)
    agv_start_node = nodes["agv_start_nodes"][0] if nodes["agv_start_nodes"] else None
    spawning_node = nodes["pallet_spawn_nodes"][0] if nodes["pallet_spawn_nodes"] else None

    # Initialize the scheduler and path algorithm, ora con slots
    scheduler = PalletScheduler(warehouse_graph, spawning_node, slots)
    path_algo = PathAlgorithm(warehouse_graph, agv_start_node, spawning_node, scheduler)

    # MQTT client for listening to order/pallet signals
    def on_signal_connect(client, userdata, flags, rc):
        print("Signal listener connected with result code", rc)
        client.subscribe([(ORDER_TOPIC, 1), (PALLET_TOPIC, 1)])

    def publish_slot_update(slot):
        topic = f"warehouse/slots/{slot['slot_id']}"
        signal_client.publish(topic, json.dumps(slot), retain=True)
        print(f"Updated and published slot {slot['slot_id']} (in_use={slot['in_use']}) to {topic}")

    def publish_missions():
        payload = json.dumps({"missions": missions})
        signal_client.publish(MISSIONS_TOPIC, payload)
        print(f"Published missions to {MISSIONS_TOPIC}: {missions}")

    # Only this version of on_signal_message should exist and be assigned
    def on_signal_message(client, userdata, msg):
        global missions
        topic = msg.topic
        print(f"Received signal on {topic}")
        if topic == ORDER_TOPIC:
            print("Generating retrieval path...")
            path = path_algo.get_retrieval_path()
            print("AGV retrieval mission path:", path)
            if path is not None:
                # Find the used slot node (accessible_node) chosen
                slot_node = scheduler.find_closest_used_slot()
                # Find the slot dict and update its state
                for slot in slots:
                    if slot.get('accessible_node') == slot_node and slot.get('in_use', False):
                        slot['in_use'] = False
                        publish_slot_update(slot)
                        break
                missions.append(path)
                publish_missions()
        elif topic == PALLET_TOPIC:
            print("Generating storage path...")
            path = path_algo.get_storage_path()
            print("AGV storage mission path:", path)
            if path is not None:
                # Find the empty slot node (accessible_node) chosen
                slot_node = scheduler.find_closest_empty_slot()
                # Find the slot dict and update its state
                for slot in slots:
                    if slot.get('accessible_node') == slot_node and not slot.get('in_use', False):
                        slot['in_use'] = True
                        publish_slot_update(slot)
                        break
                missions.append(path)
                publish_missions()

    # Assign only the correct callback
    signal_client = mqtt.Client()
    signal_client.on_connect = on_signal_connect
    signal_client.on_message = on_signal_message
    signal_client.connect("my-mosquitto-broker", 1883, 60)
    print("Waiting for order or pallet signals...")
    signal_client.loop_forever()