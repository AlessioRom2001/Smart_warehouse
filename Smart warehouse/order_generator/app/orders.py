import time
import numpy as np
import threading
import json

import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "my-mosquitto-broker"
PORT = 1883
TOPIC = "warehouse/order"
CONFIG_TOPIC = "warehouse/config/param/number_of_shelves"

# Global event to signal config received
config_received_event = threading.Event()

def generate_order_times(num_orders, mean_interval_sec=20):
    """
    Generate order arrival times with exponential distribution (Poisson process).
    
    Args:
        num_orders: Number of orders to generate
        mean_interval_sec: Mean interval between orders in seconds
    
    Returns:
        List of timestamps in seconds, sorted
    """
    times = []
    current_time = 0.0
    for _ in range(num_orders):
        interval = np.random.exponential(mean_interval_sec)
        current_time += interval
        times.append(current_time)
    
    return times

# MQTT callback for config
def on_config_message(client, userdata, msg):
    print(f"Received config message on {CONFIG_TOPIC}: {msg.payload.decode()}")
    config_received_event.set()


def wait_for_config(broker=BROKER, port=PORT, config_topic=CONFIG_TOPIC):
    client = mqtt.Client()
    client.on_message = on_config_message
    client.connect(broker, port, 60)
    client.subscribe(config_topic)
    client.loop_start()
    print(f"Waiting for configuration on topic {config_topic}...")
    config_received_event.wait()  # Block until event is set
    client.loop_stop()
    client.disconnect()
    print("Configuration received. Proceeding with order generation.")


def simulate_orders(num_orders=480, mean_interval_sec=20):
    """
    Simulate order arrivals by publishing to MQTT topic every ~20s (exponential randomness).
    """
    # Wait for config before starting
    wait_for_config()

    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)

    # Generate order times (relative, in seconds)
    order_times = generate_order_times(num_orders, mean_interval_sec)

    start_time = time.time()

    for i, order_time in enumerate(order_times):
        # Wait until the scheduled time
        current_time = time.time() - start_time
        wait_time = order_time - current_time

        if wait_time > 0:
            time.sleep(wait_time)

        # Publish order with order_id and timestamp
        order_payload = {
            "order_id": i + 1,
            "timestamp": time.time()
        }
        client.publish(TOPIC, json.dumps(order_payload), qos=1, retain=False)
        elapsed = time.time() - start_time
        print(f"Order {i+1}/{num_orders} published at {elapsed:.1f} seconds: {order_payload}")

    client.disconnect()
    print("Order simulation completed")


if __name__ == "__main__":
    simulate_orders(num_orders=480, mean_interval_sec=20)