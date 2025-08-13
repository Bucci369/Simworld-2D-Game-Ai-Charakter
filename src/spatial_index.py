"""
🚀 SPATIAL INDEXING für ultra-schnelles Frustum Culling
Teilt die Welt in Grids auf für O(1) Culling statt O(n) Linear Search
"""

class SpatialIndex:
    """Spatial Grid für optimiertes Frustum Culling"""
    
    def __init__(self, world_width: int, world_height: int, grid_size: int = 256):
        self.world_width = world_width
        self.world_height = world_height
        self.grid_size = grid_size
        
        # Berechne Grid-Dimensionen
        self.grid_cols = (world_width + grid_size - 1) // grid_size
        self.grid_rows = (world_height + grid_size - 1) // grid_size
        
        # Grid für Objects - jede Zelle ist eine Liste von Objekten
        self.grid = [[[] for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        
        print(f"🗂️ Spatial Index created: {self.grid_cols}x{self.grid_rows} cells ({grid_size}px each)")
    
    def add_object(self, x: int, y: int, obj_data: dict):
        """Füge Objekt zum Spatial Grid hinzu"""
        grid_x = min(x // self.grid_size, self.grid_cols - 1)
        grid_y = min(y // self.grid_size, self.grid_rows - 1)
        
        if 0 <= grid_x < self.grid_cols and 0 <= grid_y < self.grid_rows:
            obj_entry = {
                'x': x,
                'y': y,
                'data': obj_data
            }
            self.grid[grid_y][grid_x].append(obj_entry)
    
    def get_objects_in_view(self, view_left: int, view_top: int, view_right: int, view_bottom: int):
        """Hole alle Objekte im Sichtbereich - ultra-schnell mit Grid"""
        # Berechne betroffene Grid-Zellen
        start_col = max(0, view_left // self.grid_size)
        end_col = min(self.grid_cols - 1, view_right // self.grid_size)
        start_row = max(0, view_top // self.grid_size)
        end_row = min(self.grid_rows - 1, view_bottom // self.grid_size)
        
        visible_objects = []
        
        # Durchlaufe nur betroffene Grid-Zellen (massiv reduzierte Iterationen)
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                # Alle Objekte in dieser Zelle sind potentiell sichtbar
                # Bounds-Check wird später in der Render-Funktion gemacht
                visible_objects.extend(self.grid[row][col])
        
        return visible_objects
    
    def clear(self):
        """Lösche alle Objekte aus dem Index"""
        for row in self.grid:
            for cell in row:
                cell.clear()