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
        
        # 🚀 SMOOTH CAMERA: Deadzone für ruhigere Kamera
        self.deadzone_w = 80  # Horizontale Deadzone
        self.deadzone_h = 60  # Vertikale Deadzone

    def apply_to_point(self, pos):
        """Konvertiert Welt-Position zu Screen-Position"""
        return pos[0] - self.camera.left, pos[1] - self.camera.top
    
    def apply_to_rect(self, rect):
        """Konvertiert Welt-Rect zu Screen-Rect"""
        screen_x, screen_y = self.apply_to_point((rect.x, rect.y))
        return pygame.Rect(screen_x, screen_y, rect.width, rect.height)

    def update(self, target_rect: pygame.Rect, dt: float = 0.016):
        """🚀 SMOOTH CAMERA: Interpolation + Deadzone für ultra-flüssiges Scrolling"""
        
        # Aktuelle Kamera-Position
        current_center_x = self.camera.centerx
        current_center_y = self.camera.centery
        
        # Ziel-Position (Player)
        target_center_x = target_rect.centerx
        target_center_y = target_rect.centery
        
        # 🚀 DEADZONE: Bewege Kamera nur wenn Player die Deadzone verlässt
        screen_center_x = self.screen_w // 2
        screen_center_y = self.screen_h // 2
        
        # Player-Position relativ zur Kamera
        player_screen_x = target_center_x - current_center_x + screen_center_x
        player_screen_y = target_center_y - current_center_y + screen_center_y
        
        # Berechne neue Kamera-Ziele nur wenn außerhalb Deadzone
        new_target_x = current_center_x
        new_target_y = current_center_y
        
        # Horizontale Deadzone
        if player_screen_x < screen_center_x - self.deadzone_w:
            new_target_x = target_center_x + self.deadzone_w
        elif player_screen_x > screen_center_x + self.deadzone_w:
            new_target_x = target_center_x - self.deadzone_w
            
        # Vertikale Deadzone
        if player_screen_y < screen_center_y - self.deadzone_h:
            new_target_y = target_center_y + self.deadzone_h
        elif player_screen_y > screen_center_y + self.deadzone_h:
            new_target_y = target_center_y - self.deadzone_h
        
        # 🚀 SMOOTH CAMERA: Lineare Interpolation für sanftes Folgen
        camera_speed = 6.0  # Etwas langsamer für ruhigere Kamera
        lerp_factor = min(1.0, camera_speed * dt)
        
        # Sanfte Bewegung zur neuen Ziel-Position
        final_x = current_center_x + (new_target_x - current_center_x) * lerp_factor
        final_y = current_center_y + (new_target_y - current_center_y) * lerp_factor
        
        # Setze neue Kamera-Position
        self.camera.centerx = final_x
        self.camera.centery = final_y

        # Clamp to world bounds
        if self.camera.left < 0:
            self.camera.left = 0
        elif self.camera.right > self.world_w:
            self.camera.right = self.world_w
        if self.camera.top < 0:
            self.camera.top = 0
        elif self.camera.bottom > self.world_h:
            self.camera.bottom = self.world_h

        return self.camera
    
    def screen_to_world(self, screen_pos):
        """Konvertiert Screen-Koordinaten zu Welt-Koordinaten"""
        return (screen_pos[0] + self.camera.left, screen_pos[1] + self.camera.top)
    
    def world_to_screen(self, world_pos):
        """Konvertiert Welt-Koordinaten zu Screen-Koordinaten"""
        return self.apply_to_point(world_pos)
