import pygame
from pytmx.util_pygame import load_pygame
from settings import MAP_PATH, TILE_SIZE

class TiledMap:
    def __init__(self, filename: str):
        self.tmx_data = load_pygame(filename)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight

    def render(self, surface: pygame.Surface, camera_rect):
        tw = self.tmx_data.tilewidth
        th = self.tmx_data.tileheight
        # Only draw visible tiles (simple culling)
        start_x = max(camera_rect.left // tw, 0)
        end_x = min((camera_rect.right // tw) + 1, self.tmx_data.width)
        start_y = max(camera_rect.top // th, 0)
        end_y = min((camera_rect.bottom // th) + 1, self.tmx_data.height)

        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'tiles'):
                for x, y, image in layer.tiles():
                    if start_x <= x < end_x and start_y <= y < end_y:
                        surface.blit(image, (x * tw - camera_rect.left, y * th - camera_rect.top))

class Camera:
    def __init__(self, world_width, world_height, screen_w, screen_h):
        # camera rect repräsentiert den sichtbaren Ausschnitt (Viewport)
        self.camera = pygame.Rect(0, 0, screen_w, screen_h)
        self.world_w = world_width
        self.world_h = world_height
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # Verbessertes Zoom-System (Best Practices 2025)
        self.zoom = 1.0  # 1.0 = normal, >1.0 = zoomed in, <1.0 = zoomed out
        self.target_zoom = 1.0  # Für smooth zoom interpolation
        self.min_zoom = 0.3  # Erweitert: mehr zoom out (30%)
        self.max_zoom = 4.0  # Erweitert: mehr zoom in (400%)
        self.zoom_step = 0.15  # Smoother zoom steps
        self.zoom_speed = 8.0  # Interpolation speed
        
        # Original screen dimensions
        self.base_screen_w = screen_w
        self.base_screen_h = screen_h
        
        # World Surface für korrektes Zoom-Rendering
        self.world_surface = pygame.Surface((screen_w, screen_h))
        self.zoom_center = (screen_w // 2, screen_h // 2)
        
        # Performance-Optimierungen
        self._zoom_cache = {}  # Cache für skalierte Surfaces
        self._cache_max_size = 10  # Max cached zoom levels
        self._last_zoom_level = 1.0  # Für Cache-Invalidierung

    def apply_to_point(self, pos):
        """Konvertiert Welt-Position zu Screen-Position (ohne Zoom, das macht der World Surface)"""
        return pos[0] - self.camera.left, pos[1] - self.camera.top
    
    def apply_to_rect(self, rect):
        """Konvertiert Welt-Rect zu Screen-Rect (ohne Zoom)"""
        screen_x, screen_y = self.apply_to_point((rect.x, rect.y))
        return pygame.Rect(screen_x, screen_y, rect.width, rect.height)

    def update(self, target_rect: pygame.Rect, dt: float = 0.016):
        # Smooth zoom interpolation
        if abs(self.zoom - self.target_zoom) > 0.01:
            zoom_diff = self.target_zoom - self.zoom
            self.zoom += zoom_diff * self.zoom_speed * dt
            # Clamp to avoid overshooting
            if abs(zoom_diff) < 0.01:
                self.zoom = self.target_zoom
        
        # Center camera on target
        self.camera.centerx = target_rect.centerx
        self.camera.centery = target_rect.centery

        # Clamp to world bounds (angepasst an Zoom)
        effective_screen_w = int(self.screen_w / self.zoom)
        effective_screen_h = int(self.screen_h / self.zoom)
        
        max_left = max(0, self.world_w - effective_screen_w)
        max_top = max(0, self.world_h - effective_screen_h)
        
        if self.camera.left < 0:
            self.camera.left = 0
        elif self.camera.left > max_left:
            self.camera.left = max_left
        if self.camera.top < 0:
            self.camera.top = 0
        elif self.camera.top > max_top:
            self.camera.top = max_top

        return self.camera
    
    def screen_to_world(self, screen_pos):
        """Konvertiert Screen-Koordinaten zu Welt-Koordinaten mit World Surface Zoom"""
        if self.zoom == 1.0:
            # Kein Zoom: normale Konvertierung
            return (screen_pos[0] + self.camera.left, screen_pos[1] + self.camera.top)
        else:
            # Mit Zoom: berechne Position im World Surface
            # Der angezeigte Bereich ist kleiner und zentriert um zoom_center
            zoom_size_w = int(self.screen_w / self.zoom)
            zoom_size_h = int(self.screen_h / self.zoom)
            
            # Zoom-Area zentriert um zoom_center im World Surface
            zoom_rect = pygame.Rect(0, 0, zoom_size_w, zoom_size_h)
            zoom_rect.center = self.zoom_center
            
            # Screen-Position zu Position im Zoom-Rect
            zoom_local_x = (screen_pos[0] / self.screen_w) * zoom_size_w
            zoom_local_y = (screen_pos[1] / self.screen_h) * zoom_size_h
            
            # Position im World Surface
            world_surface_x = zoom_rect.left + zoom_local_x
            world_surface_y = zoom_rect.top + zoom_local_y
            
            # Konvertiere zu echten Welt-Koordinaten
            world_x = world_surface_x + self.camera.left
            world_y = world_surface_y + self.camera.top
            
            return (world_x, world_y)
    
    def world_to_screen(self, world_pos):
        """Konvertiert Welt-Koordinaten zu Screen-Koordinaten"""
        return self.apply_to_point(world_pos)
    
    def zoom_in(self, center_pos=None):
        """Smooth Zoom hinein"""
        if center_pos:
            self.zoom_center = center_pos
        self.target_zoom = min(self.target_zoom + self.zoom_step, self.max_zoom)
        self._clear_zoom_cache()  # Cache leeren bei Zoom-Änderung
        print(f"Zoom in: Target {self.target_zoom:.1f}x")
            
    def zoom_out(self, center_pos=None):
        """Smooth Zoom heraus"""  
        if center_pos:
            self.zoom_center = center_pos
        self.target_zoom = max(self.target_zoom - self.zoom_step, self.min_zoom)
        self._clear_zoom_cache()  # Cache leeren bei Zoom-Änderung
        print(f"Zoom out: Target {self.target_zoom:.1f}x")
    
    def set_zoom(self, zoom_level, center_pos=None):
        """Setze Zoom-Level direkt (smooth)"""
        if center_pos:
            self.zoom_center = center_pos
        self.target_zoom = max(self.min_zoom, min(zoom_level, self.max_zoom))
        self._clear_zoom_cache()
        
    def get_zoom_info(self):
        """Gib Zoom-Informationen zurück"""
        return {
            'zoom': self.zoom,
            'min_zoom': self.min_zoom,
            'max_zoom': self.max_zoom,
            'zoom_percentage': int(self.zoom * 100)
        }
    
    def render_world_to_screen(self, final_screen):
        """Optimiertes Rendering mit Caching und Smoothscale (Best Practices 2025)"""
        if abs(self.zoom - 1.0) < 0.01:
            # Kein Zoom: direkt kopieren (Performance-Optimierung)
            final_screen.blit(self.world_surface, (0, 0))
            return
            
        # Mit Zoom: optimierte Subsurface + Smoothscale Approach
        zoom_size_w = max(1, int(self.screen_w / self.zoom))
        zoom_size_h = max(1, int(self.screen_h / self.zoom))
        
        # Zoom-Area zentriert um zoom_center
        zoom_rect = pygame.Rect(0, 0, zoom_size_w, zoom_size_h)
        zoom_rect.center = self.zoom_center
        
        # Clamp zoom_rect to world_surface bounds
        world_rect = self.world_surface.get_rect()
        zoom_rect = zoom_rect.clamp(world_rect)
        
        if zoom_rect.width > 0 and zoom_rect.height > 0:
            try:
                # Cache-Key für diese Zoom-Konfiguration
                cache_key = (round(self.zoom, 2), zoom_rect.center, zoom_rect.size)
                
                # Prüfe Cache
                if cache_key in self._zoom_cache:
                    scaled_surface = self._zoom_cache[cache_key]
                else:
                    # Erstelle Subsurface (Memory-effizient)
                    zoom_subsurface = self.world_surface.subsurface(zoom_rect)
                    
                    # Smoothscale für bessere Qualität (Best Practice 2025)
                    scaled_surface = pygame.transform.smoothscale(
                        zoom_subsurface, 
                        (self.screen_w, self.screen_h)
                    )
                    
                    # Cache speichern (mit Größenlimit)
                    if len(self._zoom_cache) >= self._cache_max_size:
                        # Entferne ältesten Cache-Eintrag
                        oldest_key = next(iter(self._zoom_cache))
                        del self._zoom_cache[oldest_key]
                    
                    self._zoom_cache[cache_key] = scaled_surface
                
                final_screen.blit(scaled_surface, (0, 0))
                
            except Exception as e:
                # Fallback bei Fehlern (z.B. subsurface out of bounds)
                print(f"Zoom rendering error: {e}")
                final_screen.blit(self.world_surface, (0, 0))
        else:
            # Fallback bei ungültiger Zoom-Area
            final_screen.blit(self.world_surface, (0, 0))
    
    def get_world_surface(self):
        """Gib den World Surface zurück, auf den alles gerendert werden soll"""
        # Surface für jeden Frame leeren
        self.world_surface.fill((0, 0, 0))
        return self.world_surface
    
    def _clear_zoom_cache(self):
        """Leert den Zoom-Cache (bei Änderungen)"""
        self._zoom_cache.clear()
    
    def get_cache_info(self):
        """Debug-Info über Cache-Status"""
        return {
            'cache_size': len(self._zoom_cache),
            'cache_limit': self._cache_max_size,
            'current_zoom': round(self.zoom, 2),
            'target_zoom': round(self.target_zoom, 2)
        }
