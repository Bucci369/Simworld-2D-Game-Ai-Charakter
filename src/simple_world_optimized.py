import random
import os
import math
import pygame
from settings import (
    TILE_SIZE,
    SIMPLE_WORLD_WIDTH_TILES,
    SIMPLE_WORLD_HEIGHT_TILES,
    SIMPLE_WORLD_TREE_DENSITY,
    SIMPLE_WORLD_SEED,
    SIMPLE_WORLD_FARMLAND_PATCHES,
    SIMPLE_WORLD_FARMLAND_RADIUS_RANGE,
    SIMPLE_WORLD_LAKE_RADII,
    SIMPLE_WORLD_LAKE_CENTER_REL,
    HOUSE_IMAGE_PATH,
)
from asset_manager import asset_manager
from spatial_index import SpatialIndex

class SimpleWorldOptimized:
    """🚀 PERFORMANCE-OPTIMIERTE Version von SimpleWorld"""
    
    def __init__(self, area_width_tiles=None, area_height_tiles=None, tree_density=None, seed=None):
        print("🚀 Initializing OPTIMIZED SimpleWorld...")
        
        # Defaults
        self.area_width_tiles = area_width_tiles or SIMPLE_WORLD_WIDTH_TILES
        self.area_height_tiles = area_height_tiles or SIMPLE_WORLD_HEIGHT_TILES
        density = tree_density if tree_density is not None else SIMPLE_WORLD_TREE_DENSITY
        use_seed = SIMPLE_WORLD_SEED if seed is None else seed
        if use_seed is not None:
            random.seed(use_seed)

        # Dimensions
        self.width = self.area_width_tiles * TILE_SIZE
        self.height = self.area_height_tiles * TILE_SIZE

        # 🚀 PERFORMANCE: Cached Asset Loading
        print("🎯 Loading assets with caching...")
        self.grass_tile = asset_manager.load_scaled_image('Tiles/Grass_Middle.png', (TILE_SIZE, TILE_SIZE))
        self.oak_tree = asset_manager.load_image('Outdoor decoration/Oak_Tree.png')
        self.farmland_tile = asset_manager.load_scaled_image('Tiles/FarmLand_Tile.png', (TILE_SIZE, TILE_SIZE))
        self.water_tile = asset_manager.load_scaled_image('Tiles/Water_Middle.png', (TILE_SIZE, TILE_SIZE))
        self.path_tile = asset_manager.load_scaled_image('Tiles/Path_Middle.png', (TILE_SIZE, TILE_SIZE))

        # Initialize overlay grid
        self.overlay = [[None for _ in range(self.area_width_tiles)] for _ in range(self.area_height_tiles)]
        
        # 🚀 PERFORMANCE: Pre-generate all world features ONCE
        print("🎯 Generating world features...")
        self._generate_world_features()
        
        # 🚀 PERFORMANCE: Pre-render complete background
        print("🎯 Pre-rendering optimized background...")
        self.background = self._create_optimized_background()
        
        # Initialize other systems
        self._initialize_structures()
        self._generate_optimized_forests(density)
        self._load_decoration_sprites()
        self._generate_decorations()
        
        # 🚀 PERFORMANCE: Dynamic objects mit reduziertem Limit
        self.dynamic_objects = []
        self.max_dynamic_objects = 50  # Reduziert von 150
        
        # Drag & Drop System
        self.selected_object = None
        self.dragging = False
        self.drag_offset = (0, 0)
        
        print(f"✅ Optimized SimpleWorld created: {self.width}x{self.height} pixels")
        print(f"📊 Cache stats: {asset_manager.get_cache_stats()}")

    def _generate_world_features(self):
        """🚀 OPTIMIZED: Generate all world features efficiently"""
        tiles_x = self.area_width_tiles
        tiles_y = self.area_height_tiles
        center_x = tiles_x // 2
        center_y = tiles_y // 2
        
        # Lake parameters
        lake_rx_tiles, lake_ry_tiles = SIMPLE_WORLD_LAKE_RADII
        lake_cx = int(SIMPLE_WORLD_LAKE_CENTER_REL[0] * tiles_x)
        lake_cy = int(SIMPLE_WORLD_LAKE_CENTER_REL[1] * tiles_y)
        
        # Generate paths around lake
        for tx in range(tiles_x):
            if tx < lake_cx - lake_rx_tiles - 2:
                self.overlay[center_y][tx] = 'path'
            elif tx > lake_cx + lake_rx_tiles + 2:
                self.overlay[center_y][tx] = 'path'
            else:
                path_y = max(2, lake_cy - lake_ry_tiles - 3)
                if 0 <= path_y < tiles_y:
                    self.overlay[path_y][tx] = 'path'
        
        # Vertical connection paths
        west_x = max(2, lake_cx - lake_rx_tiles - 6)
        east_x = min(tiles_x - 3, lake_cx + lake_rx_tiles + 6)
        for ty in range(tiles_y):
            if 0 <= west_x < tiles_x:
                self.overlay[ty][west_x] = 'path'
            if 0 <= east_x < tiles_x:
                self.overlay[ty][east_x] = 'path'

        # Generate lake (ellipse)
        for ty in range(tiles_y):
            dy = (ty - lake_cy) / lake_ry_tiles if lake_ry_tiles else 0
            for tx in range(tiles_x):
                dx = (tx - lake_cx) / lake_rx_tiles if lake_rx_tiles else 0
                if dx*dx + dy*dy <= 1.0:
                    self.overlay[ty][tx] = 'water'

        # Generate farmland patches efficiently
        patch_count = SIMPLE_WORLD_FARMLAND_PATCHES
        min_r, max_r = SIMPLE_WORLD_FARMLAND_RADIUS_RANGE
        attempts = patch_count * 4
        placed = 0
        while placed < patch_count and attempts > 0:
            attempts -= 1
            r = random.randint(min_r, max_r)
            cx = random.randint(r, tiles_x - r - 1)
            cy = random.randint(r, tiles_y - r - 1)
            if self.overlay[cy][cx] == 'water':
                continue
            
            changed = False
            for ty in range(cy - r, cy + r + 1):
                for tx in range(cx - r, cx + r + 1):
                    if (tx - cx)**2 + (ty - cy)**2 <= r*r:
                        if self.overlay[ty][tx] is None:
                            self.overlay[ty][tx] = 'farm'
                            changed = True
            if changed:
                placed += 1

    def _create_optimized_background(self) -> pygame.Surface:
        """🚀 PERFORMANCE: Create optimized background with batch rendering"""
        background = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 1. Fill with grass base layer (single operation)
        if self.grass_tile:
            for y in range(0, self.height, TILE_SIZE):
                for x in range(0, self.width, TILE_SIZE):
                    background.blit(self.grass_tile, (x, y))
        
        # 2. Batch render special tiles by type for efficiency
        tile_positions = {'water': [], 'path': [], 'farm': []}
        
        for ty in range(self.area_height_tiles):
            for tx in range(self.area_width_tiles):
                code = self.overlay[ty][tx]
                if code in tile_positions:
                    tile_positions[code].append((tx * TILE_SIZE, ty * TILE_SIZE))
        
        # Batch blit for performance
        if self.water_tile:
            for pos in tile_positions['water']:
                background.blit(self.water_tile, pos)
        if self.path_tile:
            for pos in tile_positions['path']:
                background.blit(self.path_tile, pos)
        if self.farmland_tile:
            for pos in tile_positions['farm']:
                background.blit(self.farmland_tile, pos)
        
        print(f"✅ Background rendered: {len(tile_positions['water'])} water, {len(tile_positions['path'])} path, {len(tile_positions['farm'])} farm")
        return background

    def _initialize_structures(self):
        """Initialize houses and portals"""
        self.structures = []
        
        # Load house
        if HOUSE_IMAGE_PATH and os.path.exists(HOUSE_IMAGE_PATH):
            self.house_image = asset_manager.load_image('Outdoor decoration/House.png')
            if self.house_image:
                center_x = self.area_width_tiles // 2
                center_y = self.area_height_tiles // 2
                hx_tiles = center_x + 5
                hy_tiles = center_y - 2
                if (0 <= hx_tiles < self.area_width_tiles and 
                    0 <= hy_tiles < self.area_height_tiles and 
                    self.overlay[hy_tiles][hx_tiles] != 'water'):
                    self.structures.append(('house', hx_tiles * TILE_SIZE, (hy_tiles+1) * TILE_SIZE - self.house_image.get_height()))
        
        # Create portal sprite
        self.portal_image = self._create_portal_sprite()
        if self.portal_image:
            lake_rx_tiles, lake_ry_tiles = SIMPLE_WORLD_LAKE_RADII
            lake_cx = int(SIMPLE_WORLD_LAKE_CENTER_REL[0] * self.area_width_tiles)
            lake_cy = int(SIMPLE_WORLD_LAKE_CENTER_REL[1] * self.area_height_tiles)
            portal_x = lake_cx
            portal_y = lake_cy + lake_ry_tiles + 1
            if (0 <= portal_x < self.area_width_tiles and 
                0 <= portal_y < self.area_height_tiles and 
                self.overlay[portal_y][portal_x] != 'water'):
                self.structures.append(('portal', portal_x * TILE_SIZE, (portal_y+1) * TILE_SIZE - self.portal_image.get_height()))

    def _generate_optimized_forests(self, base_density):
        """🚀 PERFORMANCE: Generate larger forests for 70x70 world"""
        self.trees = []
        
        # Größere Waldgebiete für 70x70 Welt mit mehr Abstand zwischen Tribes
        forest_areas = [
            # Nordwest-Wald (größer)
            {'center': (self.width * 0.2, self.height * 0.2), 'radius': 180, 'density': 0.35},
            # Nordost-Wald (größer)
            {'center': (self.width * 0.8, self.height * 0.2), 'radius': 160, 'density': 0.3},
            # Südwest-Wald (größer)
            {'center': (self.width * 0.2, self.height * 0.8), 'radius': 200, 'density': 0.4},
            # Südost-Wald (größer)
            {'center': (self.width * 0.8, self.height * 0.8), 'radius': 170, 'density': 0.35},
            # Zusätzliche Wälder für größere Welt
            # West-Zentral
            {'center': (self.width * 0.1, self.height * 0.5), 'radius': 140, 'density': 0.3},
            # Ost-Zentral
            {'center': (self.width * 0.9, self.height * 0.5), 'radius': 150, 'density': 0.32},
            # Nord-Zentral (zwischen den Tribes)
            {'center': (self.width * 0.5, self.height * 0.15), 'radius': 130, 'density': 0.28},
            # Süd-Zentral
            {'center': (self.width * 0.5, self.height * 0.85), 'radius': 160, 'density': 0.35},
        ]
        
        for forest in forest_areas:
            center_x, center_y = forest['center']
            radius = forest['radius']
            density = forest['density']
            
            area_size = 3.14159 * radius * radius
            trees_in_forest = int(area_size / (TILE_SIZE * TILE_SIZE) * density)
            
            attempts = 0
            trees_placed = 0
            max_attempts = trees_in_forest * 5  # Reduced from 10
            
            while trees_placed < trees_in_forest and attempts < max_attempts:
                attempts += 1
                
                # Random position in circle
                distance = random.uniform(0, radius)
                angle = random.uniform(0, 2 * 3.14159)
                
                tx = int(center_x + distance * math.cos(angle))
                ty = int(center_y + distance * math.sin(angle))
                
                # Check bounds
                if (tx < 0 or ty < 0 or 
                    tx > self.width - self.oak_tree.get_width() or 
                    ty > self.height - self.oak_tree.get_height()):
                    continue
                
                # Check overlap with features
                tile_x = tx // TILE_SIZE
                tile_y = ty // TILE_SIZE
                if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
                    code = self.overlay[tile_y][tile_x]
                    if code in ('water', 'path', 'farm'):
                        continue
                
                # Check distance to other trees (optimized)
                min_distance = 25
                too_close = any(
                    ((tx - ex)**2 + (ty - ey)**2) < min_distance**2
                    for ex, ey in self.trees
                )
                
                if not too_close:
                    self.trees.append((tx, ty))
                    trees_placed += 1
        
        self.trees.sort(key=lambda p: p[1])  # Sort for painter's order
        
        # 🚀 PERFORMANCE: Spatial Indexing for ultra-fast tree culling
        self.tree_spatial_index = SpatialIndex(self.width, self.height, grid_size=200)
        for tree_x, tree_y in self.trees:
            self.tree_spatial_index.add_object(tree_x, tree_y, {'type': 'tree'})
        
        print(f"✅ Generated {len(self.trees)} trees in optimized forests with spatial indexing")

    def _create_portal_sprite(self):
        """Create a 2D portal sprite"""
        portal_size = 64
        portal = pygame.Surface((portal_size, portal_size), pygame.SRCALPHA)
        
        pygame.draw.circle(portal, (100, 50, 200), (portal_size//2, portal_size//2), portal_size//2 - 2, 6)
        pygame.draw.circle(portal, (150, 100, 255), (portal_size//2, portal_size//2), portal_size//2 - 8, 4)
        pygame.draw.circle(portal, (20, 10, 50), (portal_size//2, portal_size//2), portal_size//2 - 12)
        pygame.draw.circle(portal, (200, 150, 255), (portal_size//2, portal_size//2), 8)
        pygame.draw.circle(portal, (255, 255, 255), (portal_size//2, portal_size//2), 4)
        
        return portal

    def _load_decoration_sprites(self):
        """Load decorative sprites with caching"""
        self.decoration_sprites = {}
        
        decoration_files = ['pilz.png', 'blume.png', 'blume1.png', 'stone.png', 'gold.png']
        
        for filename in decoration_files:
            sprite = asset_manager.load_image(f'Outdoor decoration/{filename}')
            if sprite:
                if filename in ['stone.png', 'gold.png']:
                    sprite = pygame.transform.scale(sprite, (int(sprite.get_width() * 2.5), int(sprite.get_height() * 2.5)))
                self.decoration_sprites[filename] = sprite

    def _generate_decorations(self):
        """Generate decorative objects efficiently"""
        if not hasattr(self, 'decoration_sprites'):
            return
            
        self.decorations = []
        
        decoration_densities = {
            'pilz.png': 0.002,    # Reduced density
            'blume.png': 0.004, 
            'blume1.png': 0.004,
            'stone.png': 0.003,
            'gold.png': 0.001
        }
        
        for decoration_name, density in decoration_densities.items():
            if decoration_name not in self.decoration_sprites:
                continue
                
            sprite = self.decoration_sprites[decoration_name]
            wanted_count = int(self.area_width_tiles * self.area_height_tiles * density)
            
            attempts = 0
            placed = 0
            max_attempts = wanted_count * 5  # Reduced from 10
            
            while placed < wanted_count and attempts < max_attempts:
                attempts += 1
                
                x = random.randint(0, self.width - sprite.get_width())
                y = random.randint(0, self.height - sprite.get_height())
                
                tile_x = x // TILE_SIZE
                tile_y = y // TILE_SIZE
                
                if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
                    code = self.overlay[tile_y][tile_x]
                    
                    if code is None:  # Only on grass
                        # Quick distance check to trees (optimized)
                        too_close = any(
                            ((x - tx)**2 + (y - ty)**2) < 32**2
                            for tx, ty in self.trees[:min(50, len(self.trees))]  # Check only first 50 trees
                        )
                        
                        if not too_close:
                            self.decorations.append({
                                'sprite': sprite,
                                'x': x,
                                'y': y,
                                'name': decoration_name
                            })
                            placed += 1

    def render(self, surface: pygame.Surface, camera_rect: pygame.Rect):
        """🚀 ULTRA-OPTIMIZED rendering for smooth movement"""
        # Single background blit (much faster than tile-by-tile)
        surface.blit(self.background, (-camera_rect.left, -camera_rect.top))
        
        # 🚀 PERFORMANCE: Optimized Frustum culling - pre-calculate bounds
        view_left = camera_rect.left
        view_top = camera_rect.top
        view_right = camera_rect.right
        view_bottom = camera_rect.bottom
        
        # 🚀 PERFORMANCE: Batch decorations rendering with optimized bounds checking
        if hasattr(self, 'decorations'):
            for decoration in self.decorations:
                dx, dy = decoration['x'], decoration['y']
                sprite = decoration['sprite']
                # Optimized bounds check - avoid creating Rect objects
                if (dx < view_right and dx + sprite.get_width() > view_left and
                    dy < view_bottom and dy + sprite.get_height() > view_top):
                    surface.blit(sprite, (dx - view_left, dy - view_top))
        
        # 🚀 PERFORMANCE: Optimized structures rendering
        for structure in self.structures:
            structure_type, sx, sy = structure
            if structure_type == 'house' and hasattr(self, 'house_image') and self.house_image:
                # Optimized bounds check without Rect creation
                if (sx < view_right and sx + self.house_image.get_width() > view_left and
                    sy < view_bottom and sy + self.house_image.get_height() > view_top):
                    surface.blit(self.house_image, (sx - view_left, sy - view_top))
            elif structure_type == 'portal' and self.portal_image:
                # Optimized bounds check without Rect creation
                if (sx < view_right and sx + self.portal_image.get_width() > view_left and
                    sy < view_bottom and sy + self.portal_image.get_height() > view_top):
                    surface.blit(self.portal_image, (sx - view_left, sy - view_top))
        
        # 🚀 PERFORMANCE: Ultra-optimized dynamic objects 
        if len(self.dynamic_objects) > self.max_dynamic_objects:
            self.dynamic_objects = self.dynamic_objects[-self.max_dynamic_objects//2:]
        
        # Pre-sort objects once for painter's algorithm (cache if possible)
        if not hasattr(self, '_sorted_dynamic_cache') or len(self._sorted_dynamic_cache) != len(self.dynamic_objects):
            self._sorted_dynamic_cache = sorted(self.dynamic_objects, key=lambda e: e['y'])
        
        for i, obj in enumerate(self._sorted_dynamic_cache):
            img, ox, oy = obj['image'], obj['x'], obj['y']
            # Ultra-fast bounds check without Rect objects
            if (ox < view_right and ox + img.get_width() > view_left and
                oy < view_bottom and oy + img.get_height() > view_top):
                surface.blit(img, (ox - view_left, oy - view_top))
                
                # Selection highlighting (only if selected)
                if self.selected_object and self.selected_object[1] == i:
                    screen_x = ox - view_left - 2
                    screen_y = oy - view_top - 2
                    width = img.get_width() + 4
                    height = img.get_height() + 4
                    color = (255, 255, 0) if self.dragging else (0, 255, 0)
                    thickness = 3 if self.dragging else 2
                    pygame.draw.rect(surface, color, (screen_x, screen_y, width, height), thickness)
        
        # 🚀 PERFORMANCE: SPATIAL INDEXING für Trees - ultra-schnell bei Bewegung!
        if hasattr(self, 'tree_spatial_index'):
            # Verwende Spatial Index für O(1) statt O(n) Tree Culling
            visible_trees = self.tree_spatial_index.get_objects_in_view(view_left, view_top, view_right, view_bottom)
            tree_width = self.oak_tree.get_width()
            tree_height = self.oak_tree.get_height()
            
            for tree_entry in visible_trees:
                x, y = tree_entry['x'], tree_entry['y']
                # Final bounds check for exact visibility
                if (x < view_right and x + tree_width > view_left and
                    y < view_bottom and y + tree_height > view_top):
                    surface.blit(self.oak_tree, (x - view_left, y - view_top))
        else:
            # Fallback: Standard tree rendering
            tree_width = self.oak_tree.get_width()
            tree_height = self.oak_tree.get_height()
            
            for x, y in self.trees:
                if (x < view_right and x + tree_width > view_left and
                    y < view_bottom and y + tree_height > view_top):
                    surface.blit(self.oak_tree, (x - view_left, y - view_top))

    # Keep all other methods from original SimpleWorld
    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        tx = rect.centerx // TILE_SIZE
        ty = rect.centery // TILE_SIZE
        if 0 <= ty < self.area_height_tiles and 0 <= tx < self.area_width_tiles:
            return self.overlay[ty][tx] == 'water'
        return False

    def find_safe_spawn(self) -> tuple[int,int]:
        cx = self.area_width_tiles // 2
        cy = self.area_height_tiles // 2
        if self.overlay[cy][cx] != 'water':
            return (cx * TILE_SIZE + TILE_SIZE//2, cy * TILE_SIZE + TILE_SIZE//2)
        
        max_r = max(self.area_width_tiles, self.area_height_tiles)
        for r in range(1, max_r):
            for dx in range(-r, r+1):
                for dy in (-r, r):
                    tx, ty = cx+dx, cy+dy
                    if 0 <= tx < self.area_width_tiles and 0 <= ty < self.area_height_tiles and self.overlay[ty][tx] != 'water':
                        return (tx*TILE_SIZE + TILE_SIZE//2, ty*TILE_SIZE + TILE_SIZE//2)
            for dy in range(-r+1, r):
                for dx in (-r, r):
                    tx, ty = cx+dx, cy+dy
                    if 0 <= tx < self.area_width_tiles and 0 <= ty < self.area_height_tiles and self.overlay[ty][tx] != 'water':
                        return (tx*TILE_SIZE + TILE_SIZE//2, ty*TILE_SIZE + TILE_SIZE//2)
        return (TILE_SIZE//2, TILE_SIZE//2)

    def add_dynamic_object(self, image: pygame.Surface, x: int, y: int, image_name: str = "unknown.png") -> bool:
        """Add object with limit enforcement and cache invalidation"""
        if len(self.dynamic_objects) >= self.max_dynamic_objects:
            self.dynamic_objects = self.dynamic_objects[-self.max_dynamic_objects//2:]
            # Invalidate sort cache when trimming
            self._sorted_dynamic_cache = None
        
        tile_x = (x + image.get_width()//2) // TILE_SIZE
        tile_y = (y + image.get_height() - 1) // TILE_SIZE
        if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
            if self.overlay[tile_y][tile_x] == 'water':
                return False
        
        self.dynamic_objects.append({
            'image': image,
            'x': x,
            'y': y,
            'image_name': image_name
        })
        
        # Invalidate sort cache when adding new objects
        self._sorted_dynamic_cache = None
        return True

    def clear_dynamic_objects(self):
        self.dynamic_objects.clear()
        self._sorted_dynamic_cache = None

    def get_object_at_position(self, world_pos):
        x, y = world_pos
        for i in range(len(self.dynamic_objects) - 1, -1, -1):
            obj = self.dynamic_objects[i]
            obj_rect = pygame.Rect(obj['x'], obj['y'], obj['image'].get_width(), obj['image'].get_height())
            if obj_rect.collidepoint(x, y):
                return ('dynamic', i, obj)
        return None

    def start_drag(self, world_pos):
        object_info = self.get_object_at_position(world_pos)
        if object_info:
            obj_type, obj_index, obj_data = object_info
            self.selected_object = object_info
            self.dragging = True
            obj_center_x = obj_data['x'] + obj_data['image'].get_width() // 2
            obj_center_y = obj_data['y'] + obj_data['image'].get_height() // 2
            self.drag_offset = (world_pos[0] - obj_center_x, world_pos[1] - obj_center_y)
            return True
        return False

    def update_drag(self, world_pos):
        if self.dragging and self.selected_object:
            obj_type, obj_index, obj_data = self.selected_object
            if obj_type == 'dynamic':
                new_center_x = world_pos[0] - self.drag_offset[0]
                new_center_y = world_pos[1] - self.drag_offset[1]
                new_x = new_center_x - obj_data['image'].get_width() // 2
                new_y = new_center_y - obj_data['image'].get_height() // 2
                self.dynamic_objects[obj_index]['x'] = new_x
                self.dynamic_objects[obj_index]['y'] = new_y
                # Invalidate sort cache when dragging (y-position changes)
                self._sorted_dynamic_cache = None

    def end_drag(self):
        self.dragging = False
        self.selected_object = None
        self.drag_offset = (0, 0)

    def delete_selected_object(self):
        if self.selected_object:
            obj_type, obj_index, obj_data = self.selected_object
            if obj_type == 'dynamic':
                del self.dynamic_objects[obj_index]
                print(f"🗑️ Object {obj_data.get('image_name', 'unknown')} deleted")
            self.selected_object = None
            return True
        return False