import json

import paho.mqtt.client as mqtt

# MQTT Broker Configuration
BROKER_ADDRESS = "my-mosquitto-broker"
BROKER_PORT = 1883
# Topics for individual parameters
PARAM_TOPICS = {
    "num_shelves": "warehouse/config/param/number_of_shelves",
    "columns_per_shelf": "warehouse/config/param/columns_per_shelf",
    "levels_per_column": "warehouse/config/param/levels_per_shelf"
}
SLOTS_TOPIC_PREFIX = "warehouse/slots"

# Additional topics for node mapping
SHELF_NODES_TOPIC = "warehouse/config/shelf_nodes"
NODE_POSITIONS_TOPIC = "warehouse/config/node_positions"
NODE_TYPES_TOPIC = "warehouse/config/node_types"

# Global variables to store warehouse parameters
warehouse_params = {
    "num_shelves": None,
    "columns_per_shelf": None,
    "levels_per_column": None
}
slots_data = []


# Data for node mapping
shelf_nodes = None
node_positions = None
node_types = None

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print("Connected to MQTT Broker")
        # Subscribe to all parameter topics
        for param, topic in PARAM_TOPICS.items():
            client.subscribe(topic)
            print(f"Subscribed to {topic}")
        # Subscribe to node mapping topics
        client.subscribe(SHELF_NODES_TOPIC)
        print(f"Subscribed to {SHELF_NODES_TOPIC}")
        client.subscribe(NODE_POSITIONS_TOPIC)
        print(f"Subscribed to {NODE_POSITIONS_TOPIC}")
        client.subscribe(NODE_TYPES_TOPIC)
        print(f"Subscribed to {NODE_TYPES_TOPIC}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback when a message is received"""
    global warehouse_params, shelf_nodes, node_positions, node_types
    updated = False
    # Check which parameter topic was received
    for param, topic in PARAM_TOPICS.items():
        if msg.topic == topic:
            try:
                payload = json.loads(msg.payload.decode())
                value = payload.get("value")
                warehouse_params[param] = value
                print(f"Received {param}: {value}")
                updated = True
            except Exception as e:
                print(f"Error decoding {param}: {e}")
    # Check for node mapping topics
    if msg.topic == SHELF_NODES_TOPIC:
        try:
            payload = json.loads(msg.payload.decode())
            shelf_nodes = payload.get("shelf_nodes")
            print(f"Received shelf nodes: {shelf_nodes}")
            updated = True
        except Exception as e:
            print(f"Error decoding shelf nodes: {e}")
    if msg.topic == NODE_POSITIONS_TOPIC:
        try:
            payload = json.loads(msg.payload.decode())
            node_positions = {int(k): tuple(v) for k, v in payload.get("positions", {}).items()}
            print(f"Received node positions")
            updated = True
        except Exception as e:
            print(f"Error decoding node positions: {e}")
    if msg.topic == NODE_TYPES_TOPIC:
        try:
            payload = json.loads(msg.payload.decode())
            node_types = {int(k): v for k, v in payload.get("types", {}).items()}
            print(f"Received node types")
            updated = True
        except Exception as e:
            print(f"Error decoding node types: {e}")
    # Ogni volta che arriva un nuovo parametro o mapping, se tutti i dati sono disponibili, pubblica gli slot
    if updated and all(warehouse_params.values()) and shelf_nodes is not None and node_positions is not None and node_types is not None:
        print(f"All parameters and node mapping received or updated. Publishing slots...")
        calculate_and_publish_slots(client)

def calculate_and_publish_slots(client):
    """Calculate total slots and publish them to MQTT, including accessible node IDs."""
    global warehouse_params, slots_data, node_positions, node_types
    num_shelves = warehouse_params.get('num_shelves')
    columns_per_shelf = warehouse_params.get('columns_per_shelf')
    levels_per_column = warehouse_params.get('levels_per_column')
    if not (num_shelves and columns_per_shelf and levels_per_column):
        print("Missing warehouse parameters, cannot publish slots.")
        return
    if node_positions is None or node_types is None:
        print("Missing node mapping data, cannot publish slots.")
        return
    total_slots = num_shelves * columns_per_shelf * levels_per_column
    print(f"Total available slots: {total_slots}")
    slots_data = []
    slot_id = 1
    print("Building slots for each shelf column...")
    for node_id, pos in node_positions.items():
        # node_id: node id, pos: (row, col)
        if node_types.get(node_id) != 'shelf':
            continue
        row, col = pos
        # For each level (slot) in this column
        for level in range(1, levels_per_column + 1):
            # Find the aisle node to the left (same row, col-1)
            accessible_node = None
            for other_id, other_pos in node_positions.items():
                if other_pos == (row, col - 1) and node_types.get(other_id) == 'aisle':
                    accessible_node = other_id
                    break
            slot = {
                "slot_id": slot_id,
                "shelf_col_node": node_id,
                "row": row,
                "col": col,
                "level": level,
                "in_use": False,
                "accessible_node": accessible_node
            }
            slots_data.append(slot)
            topic = f"{SLOTS_TOPIC_PREFIX}/{slot_id}"
            client.publish(topic, json.dumps(slot), qos=1, retain=False)
            print(f"Published slot {slot_id} to {topic} (accessible_node: {accessible_node})")
            slot_id += 1
    print(f"Published all {len(slots_data)} slots with accessible nodes")
    # Pubblica il numero totale di slot
    client.publish(f"{SLOTS_TOPIC_PREFIX}/total", json.dumps({"total_slots": len(slots_data)}), qos=1, retain=False)

def main():
    """Main function to run the MQTT client"""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
        print(f"Connecting to broker at {BROKER_ADDRESS}:{BROKER_PORT}")
        
        # Start the loop
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nDisconnecting from broker...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()