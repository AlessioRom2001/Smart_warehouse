import numpy as np
from typing import Dict, List, Tuple


class WarehouseMatrix:
    """
    Class to create an adjacency matrix representation of a warehouse.
    The warehouse contains shelves, aisles, AGV starting areas, shipping areas, and pallet spawning areas.
    """
    
    def __init__(self, num_shelves: int, columns_per_shelf: int, levels_per_shelf: int, num_agvs: int):
        """
        Initialize the warehouse matrix generator.
        
        Args:
            num_shelves: Number of shelf units in the warehouse
            columns_per_shelf: Number of columns per shelf unit
            levels_per_shelf: Number of levels (height) per shelf unit
            num_agvs: Number of AGVs (Automated Guided Vehicles)
        """
        self.num_shelves = num_shelves
        self.columns_per_shelf = columns_per_shelf
        self.levels_per_shelf = levels_per_shelf
        self.num_agvs = num_agvs
        
        # Calculate warehouse dimensions
        # Layout: [AGV Start Area] [Shelves with aisles] [Shipping Area] [Pallet Spawn]
        self.aisle_width = 2  # Width of aisles between shelves
        self.agv_start_width = 1  # Width of AGV starting area (one column for AGV nodes)
        self.shipping_width = 1  # Width of shipping area (single node)
        self.pallet_spawn_width = 1  # Width of pallet spawning area (single node)
        
        # Calculate total warehouse dimensions
        # Shelves are now vertical lines (1 column wide, columns_per_shelf rows high)
        # Total shelves = num_shelves, split between left and right sides
        self.total_shelves = num_shelves
        self.shelves_left = (num_shelves + 1) // 2  # Left side gets extra shelf if odd
        self.shelves_right = num_shelves // 2  # Right side
        self.shelf_height = columns_per_shelf  # Vertical length of each shelf
        self.shelf_spacing = 2  # Spacing between vertical shelves (1 for shelf + 1 for gap)
        
        # Warehouse layout dimensions
        # New layout: AGV start on top, Pallet spawn on left, vertical shelves, Shipping on right
        left_shelves_width = self.shelves_left * self.shelf_spacing - 1  # Remove last gap
        right_shelves_width = self.shelves_right * self.shelf_spacing - 1 if self.shelves_right > 0 else 0
        self.width = (self.pallet_spawn_width + 
                     self.aisle_width +  # Left aisle
                     left_shelves_width +  # Left shelves
                     self.aisle_width +  # Middle aisle
                     right_shelves_width +  # Right shelves
                     self.aisle_width +  # Right aisle
                     self.shipping_width)
        
        self.height = self.agv_start_width + self.aisle_width + self.shelf_height + self.aisle_width + 1
        
        # Initialize matrices
        self.grid = None
        self.adjacency_matrix = None
        self.node_positions = {}  # Maps node IDs to (row, col) positions
        self.position_to_node = {}  # Maps (row, col) to node ID
        self.node_types = {}  # Maps node ID to type (aisle, shelf, agv_start, etc.)
        
        self._generate_grid()
        self._generate_adjacency_matrix()
    
    def _generate_grid(self):
        """Generate the warehouse grid layout."""
        self.grid = np.zeros((self.height, self.width), dtype=int)
        
        # Define cell types
        # 0: Free space/Aisle
        # 1: Shelf
        # 2: AGV starting area
        # 3: Shipping area
        # 4: Pallet spawning area
        
        row_offset = 0
        
        # AGV starting area (top side) - place AGV nodes horizontally
        self.grid[row_offset:row_offset + self.agv_start_width, :] = 0  # Make it aisle by default
        
        # Place exactly num_agvs AGV start nodes horizontally spaced
        if self.num_agvs > 0 and self.width > 0:
            spacing = max(1, self.width // (self.num_agvs + 1))
            for agv_idx in range(self.num_agvs):
                agv_col = spacing * (agv_idx + 1)
                if agv_col < self.width:
                    self.grid[row_offset, agv_col] = 2  # Place single AGV start node
        
        row_offset += self.agv_start_width
        
        # Horizontal aisle after AGV start
        self.grid[row_offset:row_offset + self.aisle_width, :] = 0
        row_offset += self.aisle_width
        
        # Now build the main warehouse area horizontally
        col_offset = 0
        
        # Pallet spawning area (left side) - single node
        self.grid[row_offset:, col_offset:col_offset + self.pallet_spawn_width] = 0  # Make it aisle by default
        
        # Place single pallet spawn node in the middle vertically
        available_rows = self.height - row_offset
        if available_rows > 0:
            pallet_row = row_offset + available_rows // 2
            self.grid[pallet_row, col_offset] = 4  # Place single pallet spawn node
        
        col_offset += self.pallet_spawn_width
        
        # Main aisle
        self.grid[row_offset:, col_offset:col_offset + self.aisle_width] = 0
        col_offset += self.aisle_width
        
        # Left shelves (vertical lines)
        left_shelves_start = col_offset
        for i in range(self.shelves_left):
            shelf_col = left_shelves_start + i * self.shelf_spacing
            if shelf_col < self.width and row_offset + self.shelf_height <= self.height:
                self.grid[row_offset:row_offset + self.shelf_height, shelf_col] = 1
        col_offset += self.shelves_left * self.shelf_spacing - 1  # -1 to remove last gap
        
        # Middle aisle (main corridor)
        self.grid[row_offset:, col_offset:col_offset + self.aisle_width] = 0
        col_offset += self.aisle_width
        
        # Right shelves (vertical lines)
        right_shelves_start = col_offset
        for i in range(self.shelves_right):
            shelf_col = right_shelves_start + i * self.shelf_spacing
            if shelf_col < self.width and row_offset + self.shelf_height <= self.height:
                self.grid[row_offset:row_offset + self.shelf_height, shelf_col] = 1
        if self.shelves_right > 0:
            col_offset += self.shelves_right * self.shelf_spacing - 1  # -1 to remove last gap
        
        # Aisle before shipping area (right side)
        self.grid[row_offset:, col_offset:col_offset + self.aisle_width] = 0
        col_offset += self.aisle_width
        
        # Shipping area (right side) - single node
        if col_offset + self.shipping_width <= self.width:
            self.grid[row_offset:, col_offset:col_offset + self.shipping_width] = 0  # Make it aisle by default
            
            # Place single shipping node in the middle vertically
            available_rows = self.height - row_offset
            if available_rows > 0:
                shipping_row = row_offset + available_rows // 2
                self.grid[shipping_row, col_offset] = 3  # Place single shipping node
    
    def _generate_adjacency_matrix(self):
        """Generate adjacency matrix from the warehouse grid, including shelf nodes."""
        node_id = 0
        # Create nodes for all cell types (including shelves)
        for row in range(self.height):
            for col in range(self.width):
                cell_type = self.grid[row, col]
                self.node_positions[node_id] = (row, col)
                self.position_to_node[(row, col)] = node_id
                # Store node type
                type_map = {0: 'aisle', 1: 'shelf', 2: 'agv_start', 3: 'shipping', 4: 'pallet_spawn'}
                self.node_types[node_id] = type_map.get(cell_type, 'aisle')
                node_id += 1
        # Create adjacency matrix
        num_nodes = len(self.node_positions)
        self.adjacency_matrix = np.zeros((num_nodes, num_nodes), dtype=int)
        # Connect adjacent nodes (4-connectivity: up, down, left, right)
        for node_id, (row, col) in self.node_positions.items():
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if (0 <= new_row < self.height and 
                    0 <= new_col < self.width and
                    (new_row, new_col) in self.position_to_node):
                    neighbor_id = self.position_to_node[(new_row, new_col)]
                    self.adjacency_matrix[node_id, neighbor_id] = 1
    
    def get_adjacency_matrix(self) -> np.ndarray:
        """Return the adjacency matrix."""
        return self.adjacency_matrix
    
    def get_node_positions(self) -> Dict[int, Tuple[int, int]]:
        """Return the mapping of node IDs to grid positions."""
        return self.node_positions
    
    def get_node_types(self) -> Dict[int, str]:
        """Return the mapping of node IDs to their types."""
        return self.node_types
    
    def get_grid(self) -> np.ndarray:
        """Return the warehouse grid."""
        return self.grid
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Return warehouse dimensions (height, width)."""
        return self.height, self.width
    
    def get_agv_start_nodes(self) -> List[int]:
        """Return list of node IDs in the AGV starting area."""
        return [node_id for node_id, node_type in self.node_types.items() 
                if node_type == 'agv_start']

    def get_shipping_nodes(self) -> List[int]:
        """Return list of node IDs in the shipping area."""
        return [node_id for node_id, node_type in self.node_types.items() 
                if node_type == 'shipping']

    def get_pallet_spawn_nodes(self) -> List[int]:
        """Return list of node IDs in the pallet spawning area."""
        return [node_id for node_id, node_type in self.node_types.items() 
                if node_type == 'pallet_spawn']

    def get_shelf_nodes(self) -> List[int]:
        """Return list of node IDs in the shelf area."""
        return [node_id for node_id, node_type in self.node_types.items() 
                if node_type == 'shelf']
    
    def print_grid(self):
        """Print a visual representation of the warehouse grid."""
        symbols = {
            0: '░',  # Aisle
            1: '█',  # Shelf
            2: 'A',  # AGV start
            3: 'S',  # Shipping
            4: 'P'   # Pallet spawn
        }
        
        print("\nWarehouse Layout:")
        print("Legend: ░=Aisle, █=Shelf, A=AGV Start, S=Shipping, P=Pallet Spawn")
        print("-" * (self.width + 2))
        
        for row in self.grid:
            print("|" + "".join(symbols[cell] for cell in row) + "|")
        
        print("-" * (self.width + 2))
        print(f"\nTotal nodes: {len(self.node_positions)}")
        print(f"AGV start nodes: {len(self.get_agv_start_nodes())}")
        print(f"Shipping nodes: {len(self.get_shipping_nodes())}")
        print(f"Pallet spawn nodes: {len(self.get_pallet_spawn_nodes())}")


if __name__ == "__main__":
    # Test the warehouse matrix generation
    warehouse = WarehouseMatrix(
        num_shelves=4,
        columns_per_shelf=5,
        levels_per_shelf=3,
        num_agvs=2
    )
    
    warehouse.print_grid()
    print(f"\nAdjacency matrix shape: {warehouse.get_adjacency_matrix().shape}")
