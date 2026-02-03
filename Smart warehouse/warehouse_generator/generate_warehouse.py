import tkinter as tk
from typing import Optional, Dict
import sys
import os
import json
import numpy as np
import paho.mqtt.client as mqtt

# Import local modules
from config_gui import ConfigGUI
from matrix import WarehouseMatrix
from graph import WarehouseGraph


class WarehouseGenerator:
    """
    Main class to orchestrate the warehouse generation process.
    Uses configuration from GUI, creates matrix representation, and generates graph visualization.
    """
    
    def __init__(self):
        self.config = None
        self.warehouse_matrix = None
        self.warehouse_graph = None
        
        # MQTT configuration
        self.mqtt_broker = "my-mosquitto-broker"
        self.mqtt_port = 1883
        self.mqtt_topic_prefix = "warehouse/config/"
        self.mqtt_client = None
    
    def get_configuration(self) -> Dict:
        """
        Launch the configuration GUI and get user input parameters.
        
        Returns:
            Dictionary containing warehouse configuration parameters
        """
        root = tk.Tk()
        config_app = ConfigGUI(root)
        root.mainloop()
        
        self.config = config_app.get_config()
        
        if self.config is None:
            print("No configuration provided. Exiting...")
            sys.exit(0)
        
        return self.config
    
    def create_warehouse_matrix(self):
        """Create the warehouse matrix representation."""
        if self.config is None:
            raise ValueError("Configuration not set. Call get_configuration() first.")
        
        print("\n" + "="*60)
        print("CREATING WAREHOUSE MATRIX")
        print("="*60)
        print(f"Number of Shelves:    {self.config['shelves']}")
        print(f"Columns per Shelf:    {self.config['columns']}")
        print(f"Levels per Shelf:     {self.config['levels']}")
        print(f"Number of AGVs:       {self.config['agvs']}")
        print("="*60)
        
        self.warehouse_matrix = WarehouseMatrix(
            num_shelves=self.config['shelves'],
            columns_per_shelf=self.config['columns'],
            levels_per_shelf=self.config['levels'],
            num_agvs=self.config['agvs']
        )
        
        # Print the grid representation
        self.warehouse_matrix.print_grid()
        
        return self.warehouse_matrix
    
    def create_warehouse_graph(self):
        """Create the warehouse graph representation."""
        if self.warehouse_matrix is None:
            raise ValueError("Warehouse matrix not created. Call create_warehouse_matrix() first.")
        
        print("\n" + "="*60)
        print("CREATING WAREHOUSE GRAPH")
        print("="*60)
        
        self.warehouse_graph = WarehouseGraph(
            adjacency_matrix=self.warehouse_matrix.get_adjacency_matrix(),
            node_positions=self.warehouse_matrix.get_node_positions(),
            node_types=self.warehouse_matrix.get_node_types(),
            warehouse_grid=self.warehouse_matrix.get_grid()
        )
        
        # Print graph statistics
        self.warehouse_graph.print_statistics()
        
        return self.warehouse_graph
    
    def visualize_warehouse(self, visualization_type: str = 'combined', 
                           save_path: Optional[str] = None):
        """
        Visualize the warehouse.
        
        Args:
            visualization_type: Type of visualization ('grid', 'graph', or 'combined')
            save_path: Optional path to save the visualization
        """
        if self.warehouse_graph is None:
            raise ValueError("Warehouse graph not created. Call create_warehouse_graph() first.")
        
        print(f"\nGenerating {visualization_type} visualization...")
        
        if visualization_type == 'grid':
            self.warehouse_graph.visualize_grid(save_path=save_path)
        elif visualization_type == 'graph':
            self.warehouse_graph.visualize_graph(save_path=save_path)
        elif visualization_type == 'combined':
            self.warehouse_graph.visualize_combined(save_path=save_path)
        else:
            raise ValueError(f"Unknown visualization type: {visualization_type}")
    
    def generate_complete_warehouse(self, visualization_type: str = 'graph',
                                   save_path: Optional[str] = None):
        """
        Complete warehouse generation pipeline.
        
        Args:
            visualization_type: Type of visualization to display
            save_path: Optional path to save the visualization
        """
        try:
            # Step 1: Get configuration
            print("\nStep 1: Getting warehouse configuration...")
            self.get_configuration()
            
            # Step 2: Create matrix representation
            print("\nStep 2: Creating warehouse matrix...")
            self.create_warehouse_matrix()
            
            # Step 3: Create graph representation
            print("\nStep 3: Creating warehouse graph...")
            self.create_warehouse_graph()
            
            # Step 4: Visualize
            print("\nStep 4: Generating visualization...")
            self.visualize_warehouse(visualization_type=visualization_type, 
                                    save_path=save_path)
            
            print("\n" + "="*60)
            print("WAREHOUSE GENERATION COMPLETE!")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\nError during warehouse generation: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_warehouse_info(self) -> Dict:
        """
        Get comprehensive information about the generated warehouse.
        Returns:
            Dictionary with warehouse configuration, dimensions, and statistics
        """
        if self.warehouse_graph is None:
            raise ValueError("Warehouse not generated yet.")
        info = {
            'config': self.config,
            'dimensions': self.warehouse_matrix.get_dimensions(),
            'matrix_shape': self.warehouse_matrix.get_adjacency_matrix().shape,
            'graph_stats': self.warehouse_graph.get_statistics(),
            'agv_start_nodes': self.warehouse_matrix.get_agv_start_nodes(),
            'shipping_nodes': self.warehouse_matrix.get_shipping_nodes(),
            'pallet_spawn_nodes': self.warehouse_matrix.get_pallet_spawn_nodes(),
            'shelf_nodes': self.warehouse_matrix.get_shelf_nodes()

        }
        return info
    
    def publish_to_mqtt(self, broker: str = "my-mosquitto-broker", port: int = 1883, 
                       topic_prefix: str = "warehouse/config") -> bool:
        """
        Publish warehouse data to MQTT broker.
        
        Args:
            broker: MQTT broker address (default: localhost, use 'my-mosquitto-broker' for Docker)
            port: MQTT broker port (default: 1883)
            topic_prefix: Prefix for MQTT topics (default: 'warehouse/config')
            
        Returns:
            True if successful, False otherwise
        """
        if self.warehouse_matrix is None or self.warehouse_graph is None:
            raise ValueError("Warehouse not generated yet. Generate warehouse first.")
        
        try:
            print("\n" + "="*60)
            print("PUBLISHING TO MQTT BROKER")
            print("="*60)
            print(f"Broker: {broker}:{port}")
            print(f"Topic prefix: {topic_prefix}")
            
            # Create MQTT client
            self.mqtt_client = mqtt.Client()
            
            # Set callback for connection confirmation
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    print("✓ Successfully connected to MQTT Broker")
                else:
                    print(f"✗ Failed to connect to MQTT Broker. Return code: {rc}")
            
            self.mqtt_client.on_connect = on_connect
            
            # Connect to broker
            print("Connecting to broker...")
            self.mqtt_client.connect(broker, port, 60)
            self.mqtt_client.loop_start()
            
            # Give time for connection to establish
            import time
            time.sleep(1)
            
            # 1. Publish configuration parameters
            print("Publishing configuration parameters...")
            config_topics = {
                "shelves": f"{topic_prefix}/param/number_of_shelves",
                "columns": f"{topic_prefix}/param/columns_per_shelf",
                "levels": f"{topic_prefix}/param/levels_per_shelf",
                "agvs": f"{topic_prefix}/param/number_of_agvs"
            }
            
            for param, topic in config_topics.items():
                payload = json.dumps({
                    "type": param,
                    "value": self.config[param],
                    "timestamp": time.time()
                }, indent=2)
                # Retain True only for the first 4 config params
                result = self.mqtt_client.publish(topic, payload, qos=1, retain=True)
                result.wait_for_publish()
                print(f"  ✓ Published {param} to {topic}")
            
            # 2. Publish adjacency matrix
            matrix_topic = f"{topic_prefix}/adjacency_matrix"
            adjacency_matrix = self.warehouse_matrix.get_adjacency_matrix()
            matrix_payload = json.dumps({
                "shape": list(adjacency_matrix.shape),
                "data": adjacency_matrix.tolist(),
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(matrix_topic, matrix_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published adjacency matrix to {matrix_topic}")
            
            # 3. Publish node positions
            positions_topic = f"{topic_prefix}/node_positions"
            node_positions = self.warehouse_matrix.get_node_positions()
            positions_payload = json.dumps({
                "positions": {str(k): v for k, v in node_positions.items()},
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(positions_topic, positions_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published node positions to {positions_topic}")
            
            # 4. Publish node types
            types_topic = f"{topic_prefix}/node_types"
            node_types = self.warehouse_matrix.get_node_types()
            types_payload = json.dumps({
                "types": {str(k): v for k, v in node_types.items()},
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(types_topic, types_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published node types to {types_topic}")

            # 5. Publish AGV start nodes
            agv_topic = f"{topic_prefix}/agv_start_nodes"
            agv_nodes = self.warehouse_matrix.get_agv_start_nodes()
            agv_payload = json.dumps({
                "agv_start_nodes": agv_nodes,
                "num_agvs": len(agv_nodes),
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(agv_topic, agv_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published AGV start nodes to {agv_topic}")
            
            # 6. Publish shipping node
            shipping_topic = f"{topic_prefix}/shipping_nodes"
            shipping_nodes = self.warehouse_matrix.get_shipping_nodes()
            shipping_payload = json.dumps({
                "shipping_nodes": shipping_nodes,
                "num_shipping_nodes": len(shipping_nodes),
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(shipping_topic, shipping_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published shipping nodes to {shipping_topic}")
            
            # 7. Publish pallet spawn node
            pallet_topic = f"{topic_prefix}/pallet_spawn_nodes"
            pallet_nodes = self.warehouse_matrix.get_pallet_spawn_nodes()
            pallet_payload = json.dumps({
                "pallet_spawn_nodes": pallet_nodes,
                "num_pallet_nodes": len(pallet_nodes),
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(pallet_topic, pallet_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published pallet spawn nodes to {pallet_topic}")
            
            # 8. Publish shelf nodes
            shelf_topic = f"{topic_prefix}/shelf_nodes"
            shelf_nodes = self.warehouse_matrix.get_shelf_nodes()
            shelf_payload = json.dumps({
                "shelf_nodes": shelf_nodes,
                "num_shelf_nodes": len(shelf_nodes),
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(shelf_topic, shelf_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published shelf nodes to {shelf_topic}")

            # 9. Publish warehouse dimensions
            dimensions_topic = f"{topic_prefix}/dimensions"
            dimensions = self.warehouse_matrix.get_dimensions()
            dimensions_payload = json.dumps({
                "width": dimensions[0],
                "height": dimensions[1],
                "grid_size": f"{dimensions[0]}x{dimensions[1]}",
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(dimensions_topic, dimensions_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published warehouse dimensions to {dimensions_topic}")

            # 10. Publish graph statistics
            stats_topic = f"{topic_prefix}/graph_stats"
            graph_stats = self.warehouse_graph.get_statistics()
            stats_payload = json.dumps({
                **graph_stats,
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(stats_topic, stats_payload, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published graph statistics to {stats_topic}")

            # 11. Publish NetworkX graph as JSON

            import networkx as nx
            graph_topic = f"{topic_prefix}/graph_json"
            nx_graph = self.warehouse_graph.graph if hasattr(self.warehouse_graph, 'graph') else self.warehouse_graph
            # node_link_data di networkx 3.2.1 produce un dict con 'nodes' e 'links' (non 'edges')
            graph_data = nx.node_link_data(nx_graph)
            # Debug: assicurati che 'links' sia presente
            if "links" not in graph_data:
                print("[WARNING] Il grafo serializzato non contiene 'links'. networkx 3.2.1 richiede 'links'.")
            # Pubblica il payload compatibile
            graph_json = json.dumps({
                "graph": graph_data,
                "timestamp": time.time()
            }, indent=2)
            result = self.mqtt_client.publish(graph_topic, graph_json, qos=1, retain=False)
            result.wait_for_publish()
            print(f"✓ Published NetworkX graph JSON to {graph_topic} (con 'nodes' e 'links')")

            # Stop loop and disconnect
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

            print("="*60)
            print("MQTT PUBLISHING COMPLETE!")
            print(f"Total topics published: 14")
            print("="*60)

            return True

        except Exception as e:
            print(f"\nError publishing to MQTT: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.mqtt_client:
                try:
                    self.mqtt_client.loop_stop()
                    self.mqtt_client.disconnect()
                except:
                    pass
            return False


def main():
    """Main function to run the warehouse generator."""
    print("\n" + "="*60)
    print(" WAREHOUSE GENERATION SYSTEM")
    print("="*60)
    print("\nThis system will help you generate a warehouse representation")
    print("including matrix and graph visualizations.\n")
    
    # Create generator
    generator = WarehouseGenerator()
    
    # Generate complete warehouse
    success = generator.generate_complete_warehouse(
        visualization_type='graph',
        save_path=None  # Change to a path string to save the visualization
    )
    
    if success:
        # Print final information
        print("\nWarehouse Information:")
        info = generator.get_warehouse_info()
        print(f"Warehouse dimensions: {info['dimensions'][0]} x {info['dimensions'][1]}")
        print(f"Adjacency matrix size: {info['matrix_shape']}")
        print(f"Total graph nodes: {info['graph_stats']['num_nodes']}")
        print(f"Total graph edges: {info['graph_stats']['num_edges']}")
        print(f"Total shelf nodes: {info['graph_stats'].get('num_shelves', len(info['shelf_nodes']))}")
        
        # Publish to MQTT broker
        print("\nPublishing warehouse data to MQTT broker...")
        mqtt_success = generator.publish_to_mqtt(
            broker="my-mosquitto-broker",
            port=1883,
            topic_prefix="warehouse/config"
        )
        
        if mqtt_success:
            print("\n✓ Warehouse data successfully published to MQTT broker")
        else:
            print("\n✗ Failed to publish warehouse data to MQTT broker")
    
    return generator


if __name__ == "__main__":
    generator = main()
