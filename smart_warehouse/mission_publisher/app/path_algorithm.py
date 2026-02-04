import networkx as nx
from typing import List, Optional
from pallet_scheduler import PalletScheduler

# filepath: c:\Users\alexa\Desktop\Università\Magistrale\Distributed and IoT\D_Iot_project\V2\application\simulation\TSP\path_algorithm.py


class PathAlgorithm:
    def __init__(self, graph: nx.Graph, agv_start_node: str, spawning_node: str, scheduler: PalletScheduler):
        """
        Initialize the PathAlgorithm.
        
        Args:
            graph: NetworkX graph representing the warehouse layout
            agv_start_node: Node identifier for the AGV starting position
            spawning_node: Node identifier for the pallet spawning area
            scheduler: PalletScheduler instance for finding storage slots
        """
        self.graph = graph
        self.agv_start_node = agv_start_node
        self.spawning_node = spawning_node
        self.scheduler = scheduler
    
    def get_storage_path(self) -> Optional[List[str]]:
        """
        Generate the shortest path from AGV start to spawning node to an empty storage slot and back to AGV start.
        
        Returns:
            List of node identifiers representing the path, or None if no path exists
        """
        try:
            # Find the closest empty slot
            target_slot = self.scheduler.find_closest_empty_slot()
            if target_slot is None:
                return None
            
            # Get path from AGV start to spawning node
            path_to_spawn = nx.shortest_path(self.graph, self.agv_start_node, self.spawning_node)
            
            # Get path from spawning node to storage slot
            path_to_storage = nx.shortest_path(self.graph, self.spawning_node, target_slot)
            
            # Get path from storage slot back to AGV start
            path_to_start = nx.shortest_path(self.graph, target_slot, self.agv_start_node)
            
            # Combine paths (remove duplicates at connection points)
            full_path = path_to_spawn + path_to_storage[1:] + path_to_start[1:]
            
            return full_path
        except nx.NetworkXNoPath:
            return None
    
    def get_retrieval_path(self) -> Optional[List[str]]:
        """
        Generate the shortest path from AGV start to a used storage slot to the spawning node and back to AGV start.
        
        Returns:
            List of node identifiers representing the path, or None if no path exists
        """
        try:
            # Find the closest used slot
            source_slot = self.scheduler.find_closest_used_slot()
            if source_slot is None:
                return None
            
            # Get path from AGV start to used slot
            path_to_slot = nx.shortest_path(self.graph, self.agv_start_node, source_slot)
            
            # Get path from used slot to spawning node
            path_to_spawn = nx.shortest_path(self.graph, source_slot, self.spawning_node)
            
            # Get path from spawning node back to AGV start
            path_to_start = nx.shortest_path(self.graph, self.spawning_node, self.agv_start_node)
            
            # Combine paths (remove duplicates at connection points)
            full_path = path_to_slot + path_to_spawn[1:] + path_to_start[1:]
            
            return full_path
        except nx.NetworkXNoPath:
            return None