import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import numpy as np
from typing import Dict, Optional


class WarehouseGraph:
    """
    Class to create and visualize a graph representation of the warehouse
    from an adjacency matrix.
    """
    
    def __init__(self, adjacency_matrix: np.ndarray, 
                 node_positions: Dict[int, tuple], 
                 node_types: Dict[int, str],
                 warehouse_grid: np.ndarray):
        """
        Initialize the warehouse graph.
        
        Args:
            adjacency_matrix: The adjacency matrix of the warehouse
            node_positions: Dictionary mapping node IDs to (row, col) positions
            node_types: Dictionary mapping node IDs to their types
            warehouse_grid: The warehouse grid layout
        """
        self.adjacency_matrix = adjacency_matrix
        self.node_positions = node_positions
        self.node_types = node_types
        self.warehouse_grid = warehouse_grid
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_graph(self) -> nx.Graph:
        """Create a NetworkX graph from the adjacency matrix."""
        G = nx.Graph()
        
        # Add nodes with their attributes
        for node_id, (row, col) in self.node_positions.items():
            G.add_node(node_id, 
                      pos=(col, -row),  # Invert row for visualization
                      grid_pos=(row, col),
                      type=self.node_types[node_id])
        
        # Add edges from adjacency matrix
        num_nodes = self.adjacency_matrix.shape[0]
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if self.adjacency_matrix[i, j] == 1:
                    G.add_edge(i, j)
        
        return G
    
    def get_graph(self) -> nx.Graph:
        """Return the NetworkX graph."""
        return self.graph
    
    def visualize_grid(self, figsize=(14, 10), save_path: Optional[str] = None):
        """
        Visualize the warehouse grid layout.
        
        Args:
            figsize: Figure size (width, height)
            save_path: Optional path to save the figure
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Define colors for different cell types
        colors = {
            0: [0.9, 0.9, 0.9],    # Aisle - light gray
            1: [0.3, 0.3, 0.6],    # Shelf - dark blue
            2: [0.2, 0.8, 0.2],    # AGV start - green
            3: [0.8, 0.6, 0.2],    # Shipping - orange
            4: [0.8, 0.2, 0.2]     # Pallet spawn - red
        }
        
        # Create colored grid
        colored_grid = np.zeros((self.warehouse_grid.shape[0], 
                                self.warehouse_grid.shape[1], 3))
        
        for i in range(self.warehouse_grid.shape[0]):
            for j in range(self.warehouse_grid.shape[1]):
                cell_type = self.warehouse_grid[i, j]
                colored_grid[i, j] = colors[cell_type]
        
        # Display the grid
        ax.imshow(colored_grid, interpolation='nearest', aspect='auto')
        
        # Add grid lines
        ax.set_xticks(np.arange(-0.5, self.warehouse_grid.shape[1], 1), minor=True)
        ax.set_yticks(np.arange(-0.5, self.warehouse_grid.shape[0], 1), minor=True)
        ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5, alpha=0.3)
        
        # Create legend
        legend_elements = [
            mpatches.Patch(color=colors[0], label='Aisle'),
            mpatches.Patch(color=colors[1], label='Shelf'),
            mpatches.Patch(color=colors[2], label='AGV Start Area'),
            mpatches.Patch(color=colors[3], label='Shipping Area'),
            mpatches.Patch(color=colors[4], label='Pallet Spawn Area')
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))
        
        ax.set_title('Warehouse Layout Overview', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Columns', fontsize=12)
        ax.set_ylabel('Rows', fontsize=12)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Warehouse grid visualization saved to {save_path}")
        
        plt.show()
    
    def visualize_graph(self, figsize=(16, 12), save_path: Optional[str] = None,
                       show_labels: bool = False):
        """
        Visualize the warehouse as a graph with nodes and edges.
        
        Args:
            figsize: Figure size (width, height)
            save_path: Optional path to save the figure
            show_labels: Whether to show node labels
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get node positions for visualization
        pos = nx.get_node_attributes(self.graph, 'pos')
        
        # Define colors for different node types
        node_colors = {
            'aisle': '#E0E0E0',
            'shelf': '#3F51B5',
            'agv_start': '#4CAF50',
            'shipping': '#FF9800',
            'pallet_spawn': '#F44336'
        }
        # Create node color list, default to aisle if type missing
        colors = [node_colors.get(self.graph.nodes[node]['type'], node_colors['aisle'])
                  for node in self.graph.nodes()]
        
        # Draw the graph
        nx.draw_networkx_nodes(self.graph, pos, 
                              node_color=colors,
                              node_size=100,
                              alpha=0.8,
                              ax=ax)
        
        nx.draw_networkx_edges(self.graph, pos, 
                              edge_color='gray',
                              width=0.5,
                              alpha=0.5,
                              ax=ax)
        
        if show_labels:
            nx.draw_networkx_labels(self.graph, pos, 
                                   font_size=6,
                                   font_color='black',
                                   ax=ax)
        
        # Create legend
        legend_elements = [
            mpatches.Patch(color=node_colors['aisle'], label='Aisle Nodes'),
            mpatches.Patch(color=node_colors['shelf'], label='Shelf Nodes'),
            mpatches.Patch(color=node_colors['agv_start'], label='AGV Start Nodes'),
            mpatches.Patch(color=node_colors['shipping'], label='Shipping Nodes'),
            mpatches.Patch(color=node_colors['pallet_spawn'], label='Pallet Spawn Nodes')
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))
        
        ax.set_title('Warehouse Graph Representation', fontsize=16, fontweight='bold', pad=20)
        ax.axis('equal')
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Warehouse graph visualization saved to {save_path}")
        
        plt.show()
    
    def visualize_combined(self, figsize=(18, 8), save_path: Optional[str] = None):
        """
        Create a combined visualization showing both grid and graph.
        
        Args:
            figsize: Figure size (width, height)
            save_path: Optional path to save the figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # LEFT PLOT: Grid visualization
        colors = {
            0: [0.9, 0.9, 0.9],
            1: [0.3, 0.3, 0.6],
            2: [0.2, 0.8, 0.2],
            3: [0.8, 0.6, 0.2],
            4: [0.8, 0.2, 0.2]
        }
        
        colored_grid = np.zeros((self.warehouse_grid.shape[0], 
                                self.warehouse_grid.shape[1], 3))
        
        for i in range(self.warehouse_grid.shape[0]):
            for j in range(self.warehouse_grid.shape[1]):
                cell_type = self.warehouse_grid[i, j]
                colored_grid[i, j] = colors[cell_type]
        
        ax1.imshow(colored_grid, interpolation='nearest', aspect='auto')
        ax1.set_xticks(np.arange(-0.5, self.warehouse_grid.shape[1], 1), minor=True)
        ax1.set_yticks(np.arange(-0.5, self.warehouse_grid.shape[0], 1), minor=True)
        ax1.grid(which="minor", color="black", linestyle='-', linewidth=0.5, alpha=0.3)
        ax1.set_title('Warehouse Grid Layout', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Columns')
        ax1.set_ylabel('Rows')
        
        # RIGHT PLOT: Graph visualization
        pos = nx.get_node_attributes(self.graph, 'pos')
        
        node_colors_map = {
            'aisle': '#E0E0E0',
            'shelf': '#3F51B5',
            'agv_start': '#4CAF50',
            'shipping': '#FF9800',
            'pallet_spawn': '#F44336'
        }
        node_colors = [node_colors_map.get(self.graph.nodes[node]['type'], node_colors_map['aisle'])
                      for node in self.graph.nodes()]
        
        nx.draw_networkx_nodes(self.graph, pos, 
                              node_color=node_colors,
                              node_size=80,
                              alpha=0.8,
                              ax=ax2)
        
        nx.draw_networkx_edges(self.graph, pos, 
                              edge_color='gray',
                              width=0.5,
                              alpha=0.5,
                              ax=ax2)
        
        ax2.set_title('Warehouse Graph Network', fontsize=14, fontweight='bold')
        ax2.axis('equal')
        ax2.axis('off')
        
        # Add shared legend
        legend_elements = [
            mpatches.Patch(color=colors[0], label='Aisle'),
            mpatches.Patch(color=colors[1], label='Shelf'),
            mpatches.Patch(color=colors[2], label='AGV Start'),
            mpatches.Patch(color=colors[3], label='Shipping'),
            mpatches.Patch(color=colors[4], label='Pallet Spawn')
        ]
        
        fig.legend(handles=legend_elements, loc='upper center', 
                  bbox_to_anchor=(0.5, -0.02), ncol=5, frameon=False)
        
        plt.suptitle('Warehouse Representation', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Combined warehouse visualization saved to {save_path}")
        
        plt.show()
    
    def get_statistics(self) -> Dict:
        """Return statistics about the warehouse graph."""
        stats = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'num_agv_start': sum(1 for n in self.graph.nodes() 
                                if self.graph.nodes[n]['type'] == 'agv_start'),
            'num_shipping': sum(1 for n in self.graph.nodes() 
                               if self.graph.nodes[n]['type'] == 'shipping'),
            'num_pallet_spawn': sum(1 for n in self.graph.nodes() 
                                   if self.graph.nodes[n]['type'] == 'pallet_spawn'),
            'num_aisles': sum(1 for n in self.graph.nodes() 
                             if self.graph.nodes[n]['type'] == 'aisle'),
            'num_shelves': sum(1 for n in self.graph.nodes() 
                              if self.graph.nodes[n]['type'] == 'shelf'),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'is_connected': nx.is_connected(self.graph)
        }
        return stats
    
    def print_statistics(self):
        """Print detailed statistics about the warehouse graph."""
        stats = self.get_statistics()
        print("\n" + "="*50)
        print("WAREHOUSE GRAPH STATISTICS")
        print("="*50)
        print(f"Total Nodes:          {stats['num_nodes']}")
        print(f"Total Edges:          {stats['num_edges']}")
        print(f"AGV Start Nodes:      {stats['num_agv_start']}")
        print(f"Shipping Nodes:       {stats['num_shipping']}")
        print(f"Pallet Spawn Nodes:   {stats['num_pallet_spawn']}")
        print(f"Aisle Nodes:          {stats['num_aisles']}")
        print(f"Shelf Nodes:          {stats['num_shelves']}")
        print(f"Average Node Degree:  {stats['average_degree']:.2f}")
        print(f"Graph Connected:      {stats['is_connected']}")
        print("="*50 + "\n")


if __name__ == "__main__":
    # Test with a sample adjacency matrix
    from matrix import WarehouseMatrix
    
    warehouse_matrix = WarehouseMatrix(
        num_shelves=4,
        columns_per_shelf=5,
        levels_per_shelf=3,
        num_agvs=2
    )
    
    warehouse_graph = WarehouseGraph(
        adjacency_matrix=warehouse_matrix.get_adjacency_matrix(),
        node_positions=warehouse_matrix.get_node_positions(),
        node_types=warehouse_matrix.get_node_types(),
        warehouse_grid=warehouse_matrix.get_grid()
    )
    
    warehouse_graph.print_statistics()
    warehouse_graph.visualize_combined()
