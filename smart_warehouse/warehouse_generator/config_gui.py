import tkinter as tk
from tkinter import messagebox

class ConfigGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Warehouse Configuration")
        
        self.shelves_var = tk.IntVar(value=1)
        self.columns_var = tk.IntVar(value=1)
        self.levels_var = tk.IntVar(value=1)
        self.agvs_var = tk.IntVar(value=1)
        
        self.result = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Number of Shelves
        tk.Label(self.master, text="Number of Shelves:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        tk.Spinbox(self.master, from_=1, to=100, textvariable=self.shelves_var, width=10).grid(row=0, column=1, padx=10, pady=5)
        
        # Columns per Shelf
        tk.Label(self.master, text="Columns per Shelf:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        tk.Spinbox(self.master, from_=1, to=100, textvariable=self.columns_var, width=10).grid(row=1, column=1, padx=10, pady=5)
        
        # Levels per Shelf
        tk.Label(self.master, text="Levels per Shelf:").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        tk.Spinbox(self.master, from_=1, to=100, textvariable=self.levels_var, width=10).grid(row=2, column=1, padx=10, pady=5)
        
        # Number of AGVs
        tk.Label(self.master, text="Number of AGVs:").grid(row=3, column=0, padx=10, pady=5, sticky='w')
        tk.Spinbox(self.master, from_=1, to=100, textvariable=self.agvs_var, width=10).grid(row=3, column=1, padx=10, pady=5)
        
        # Confirm Button
        tk.Button(self.master, text="Confirm", command=self._on_confirm, width=15, bg="green", fg="white").grid(row=4, column=0, columnspan=2, pady=20)
    
    def _on_confirm(self):
        self.result = {
            'shelves': self.shelves_var.get(),
            'columns': self.columns_var.get(),
            'levels': self.levels_var.get(),
            'agvs': self.agvs_var.get()
        }
        self.master.quit()
    
    def get_config(self):
        return self.result


if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()
    config = app.get_config()
    if config:
        print(f"Configuration: {config}")