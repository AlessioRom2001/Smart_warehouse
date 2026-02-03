import threading
import time
import json
import paho.mqtt.client as mqtt
from AGV import AGV
import networkx as nx


# MQTT broker configuration
BROKER = "my-mosquitto-broker"
PORT = 1883
MISSIONS_TOPIC = "warehouse/missions"
AGV_COUNT_TOPIC = "warehouse/config/param/number_of_agvs"
GRAPH_TOPIC = "warehouse/config/graph_json"
NODE_POSITIONS_TOPIC = "warehouse/config/node_positions"


def get_num_agvs_from_mqtt(broker, port, topic, timeout=10):
    """
    Retrieve the number of AGVs from the MQTT broker by subscribing to the given topic.
    Returns the number of AGVs as an integer, or None if not received within the timeout.
    """
    num_agvs = None
    received = False

    def on_connect(client, userdata, flags, rc):
        client.subscribe(topic)

    def on_message(client, userdata, msg):
        nonlocal num_agvs, received
        try:
            payload = json.loads(msg.payload.decode())
            num_agvs = int(payload["value"])
            received = True
        except Exception as e:
            print(f"Error parsing AGV number: {e}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, 60)
    client.loop_start()

    start = time.time()
    while not received and (time.time() - start) < timeout:
        time.sleep(0.1)

    client.loop_stop()
    client.disconnect()
    return num_agvs


class AGVWorker(threading.Thread):
    """
    Thread class for simulating an AGV executing missions asynchronously.
    Each AGV listens to the missions topic, picks the first available mission,
    simulates following the path, and publishes its position updates.
    Ora si sottoscrive anche ai topic per il grafo e le posizioni dei nodi.
    """

    def __init__(self, agv, missions_topic):
        super().__init__()
        self.agv = agv
        self.missions_topic = missions_topic
        self.missions = []
        self.graph = None
        self.node_positions = None
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_message = self.on_message
        try:
            print(f"[DEBUG] Connecting to MQTT broker {BROKER}:{PORT} ...")
            self.mqtt_client.connect(BROKER, PORT, 60)
            print(f"[DEBUG] Connected. Subscribing to topics: {self.missions_topic}, {GRAPH_TOPIC}, {NODE_POSITIONS_TOPIC}")
            self.mqtt_client.subscribe(self.missions_topic)
            self.mqtt_client.subscribe(GRAPH_TOPIC)
            self.mqtt_client.subscribe(NODE_POSITIONS_TOPIC)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"[ERROR] MQTT connection failed: {e}")
        self.running = True

    def on_message(self, client, userdata, msg):
        print(f"[DEBUG] Received message on topic {msg.topic}: {msg.payload}")
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == self.missions_topic:
                # Accetta sia una lista semplice che un dict con 'missions'
                if isinstance(payload, list):
                    self.missions = payload
                    print(f"[DEBUG] Missions updated (simple list): {self.missions}")
                elif isinstance(payload, dict) and "missions" in payload:
                    self.missions = payload["missions"]
                    print(f"[DEBUG] Missions updated: {self.missions}")
                else:
                    print(f"[DEBUG] Payload for missions not recognized: {payload}")
            elif msg.topic == GRAPH_TOPIC:
                import networkx as nx
                if "graph" in payload:
                    self.graph = nx.node_link_graph(payload["graph"])
                    self.agv.graph = self.graph  # Aggiorna il grafo dell'AGV
                    print(f"[DEBUG] Graph updated from broker.")
                else:
                    print(f"[DEBUG] No 'graph' key in payload for graph topic.")
            elif msg.topic == NODE_POSITIONS_TOPIC:
                if "positions" in payload:
                    self.node_positions = {int(k): tuple(v) for k, v in payload["positions"].items()}
                    self.agv.node_positions = self.node_positions  # Aggiorna le posizioni nodi dell'AGV
                    print(f"[DEBUG] Node positions updated: {self.node_positions}")
                else:
                    print(f"[DEBUG] No 'positions' key in payload for node positions topic.")
        except Exception as e:
            print(f"[ERROR] Error parsing message on topic {msg.topic}: {e}")

    # ...existing code...

    def run(self):
        while self.running:
            if self.missions:
                print(f"[DEBUG] Missions queue: {self.missions}")
                mission = self.missions.pop(0)
                # Ripubblica le missioni residue sul topic
                try:
                    missions_payload = json.dumps({"missions": self.missions})
                    result = self.mqtt_client.publish(self.missions_topic, missions_payload)
                    if result.rc == 0:
                        print(f"[DEBUG] Republished remaining missions: {self.missions}")
                    else:
                        print(f"[ERROR] Failed to republish missions, rc={result.rc}")
                except Exception as e:
                    print(f"[ERROR] Exception during republish missions: {e}")
                print(f"[DEBUG] Starting mission: {mission}")
                self.simulate_mission(mission)
            else:
                print(f"[DEBUG] No missions available. Waiting...")
                time.sleep(1)  # Wait for new missions

    def simulate_mission(self, path):
        """
        Simulate following the mission path, updating encoder position and publishing to MQTT.
        Now simulates intermediate movement at 1.5 m/s.
        """
        print(f"[DEBUG] Starting mission simulation with path: {path}")
        self.agv.start()
        self.agv.path = path
        self.agv.current_path_index = 0
        speed_m_s = 1.5  # AGV speed in meters per second
        update_interval = 0.1  # seconds between position updates
        if not self.agv.node_positions:
            print("[ERROR] Node positions not available, cannot interpolate movement.")
            return
        for i in range(len(path) - 1):
            start_node = path[i]
            end_node = path[i + 1]
            start_pos = self.agv.node_positions.get(start_node)
            end_pos = self.agv.node_positions.get(end_node)
            if not start_pos or not end_pos:
                print(f"[ERROR] Missing node position for {start_node} or {end_node}, skipping segment.")
                continue
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance == 0:
                continue
            duration = distance / speed_m_s
            steps = max(1, int(duration / update_interval))
            for step in range(steps):
                frac = step / steps
                x = start_pos[0] + frac * dx
                y = start_pos[1] + frac * dy
                # Update AGV encoder sensor position directly
                if self.agv.encoder_sensor_list:
                    self.agv.encoder_sensor_list[0].value['x_axis'] = x
                    self.agv.encoder_sensor_list[0].value['y_axis'] = y
                pos_payload = json.dumps({
                    "agv_id": self.agv.device_id,
                    "position": (x, y),
                    "timestamp": time.time()
                })
                try:
                    result = self.mqtt_client.publish(
                        f"warehouse/agv/{self.agv.device_id}/position",
                        pos_payload,
                        qos=0,
                        retain=False
                    )
                    if result.rc == 0:
                        print(f"[DEBUG] Published position: {pos_payload}")
                    else:
                        print(f"[ERROR] Failed to publish position, rc={result.rc}")
                except Exception as e:
                    print(f"[ERROR] Exception during publish: {e}")
                time.sleep(update_interval)
            # At the end of the segment, set position exactly to end_pos
            if self.agv.encoder_sensor_list:
                self.agv.encoder_sensor_list[0].value['x_axis'] = end_pos[0]
                self.agv.encoder_sensor_list[0].value['y_axis'] = end_pos[1]
        # Publish final position at last node
        if path:
            last_node = path[-1]
            last_pos = self.agv.node_positions.get(last_node)
            if last_pos and self.agv.encoder_sensor_list:
                self.agv.encoder_sensor_list[0].value['x_axis'] = last_pos[0]
                self.agv.encoder_sensor_list[0].value['y_axis'] = last_pos[1]
                pos_payload = json.dumps({
                    "agv_id": self.agv.device_id,
                    "position": last_pos,
                    "timestamp": time.time()
                })
                try:
                    result = self.mqtt_client.publish(
                        f"warehouse/agv/{self.agv.device_id}/position",
                        pos_payload,
                        qos=0,
                        retain=False
                    )
                    if result.rc == 0:
                        print(f"[DEBUG] Published final position: {pos_payload}")
                    else:
                        print(f"[ERROR] Failed to publish final position, rc={result.rc}")
                except Exception as e:
                    print(f"[ERROR] Exception during publish: {e}")
        self.agv.stop()
        print(f"[DEBUG] Mission simulation completed.")

    def stop(self):
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()


def main():
    num_agvs = get_num_agvs_from_mqtt(BROKER, PORT, AGV_COUNT_TOPIC)
    if num_agvs is None:
        print("AGV number not received from broker.")
        return

    agv_list = [AGV(f"AGV_{i+1}") for i in range(num_agvs)]
    for agv in agv_list:
        agv.set_other_agvs(agv_list)

    workers = [AGVWorker(agv, MISSIONS_TOPIC) for agv in agv_list]
    for w in workers:
        w.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for w in workers:
            w.stop()
        for w in workers:
            w.join()

if __name__ == "__main__":
    main()