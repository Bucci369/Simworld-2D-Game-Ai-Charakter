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

    def apply_to_point(self, pos):
        return pos[0] - self.camera.left, pos[1] - self.camera.top

    def update(self, target_rect: pygame.Rect):
        # Center camera on target
        self.camera.centerx = target_rect.centerx
        self.camera.centery = target_rect.centery

        # Clamp to world bounds
        max_left = max(0, self.world_w - self.screen_w)
        max_top = max(0, self.world_h - self.screen_h)
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
        """Konvertiert Screen-Koordinaten zu Welt-Koordinaten"""
        return (screen_pos[0] + self.camera.left, screen_pos[1] + self.camera.top)
    
    def world_to_screen(self, world_pos):
        """Konvertiert Welt-Koordinaten zu Screen-Koordinaten"""
        return (world_pos[0] - self.camera.left, world_pos[1] - self.camera.top)
