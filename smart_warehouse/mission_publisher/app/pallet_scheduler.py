import networkx as nx
from typing import Optional, Tuple

class PalletScheduler:
    def __init__(self, graph: nx.Graph, starting_area_node: str, slots: list):
        """
        Initialize the PalletScheduler.
        Args:
            graph: NetworkX graph representing the warehouse layout
            starting_area_node: Node identifier for the starting area
            slots: List of slot dicts, each with at least 'in_use' and 'accessible_node'
        """
        self.graph = graph
        self.starting_area_node = starting_area_node
        self.slots = slots

    def find_closest_empty_slot(self) -> Optional[str]:
        """
        Find the closest accessible_node of an empty slot to the starting area.
        Returns:
            Node identifier of the closest empty slot's accessible_node, or None if not found
        """
        try:
            shortest_path_length = float('inf')
            closest_node = None
            for slot in self.slots:
                if not slot.get('in_use', True):
                    node = slot.get('accessible_node')
                    if node is None:
                        continue
                    path_length = nx.shortest_path_length(
                        self.graph,
                        self.starting_area_node,
                        node
                    )
                    if path_length < shortest_path_length:
                        shortest_path_length = path_length
                        closest_node = node
            return closest_node
        except nx.NetworkXNoPath:
            return None

    def find_closest_used_slot(self) -> Optional[str]:
        """
        Find the closest accessible_node of a used slot to the starting area.
        Returns:
            Node identifier of the closest used slot's accessible_node, or None if not found
        """
        try:
            shortest_path_length = float('inf')
            closest_node = None
            for slot in self.slots:
                if slot.get('in_use', False):
                    node = slot.get('accessible_node')
                    if node is None:
                        continue
                    path_length = nx.shortest_path_length(
                        self.graph,
                        self.starting_area_node,
                        node
                    )
                    if path_length < shortest_path_length:
                        shortest_path_length = path_length
                        closest_node = node
            return closest_node
        except nx.NetworkXNoPath:
            return None