import os
import pygame
from settings import DEBUG_PANEL_WIDTH, ASSETS_DIR, DEBUG_ENABLE_AUTO_SCAN, TILE_SIZE

PANEL_BG = (20, 20, 24, 230)
PANEL_BORDER = (90, 90, 110)
ENTRY_BG = (50, 50, 60)
ENTRY_BG_HOVER = (70, 70, 85)
TEXT_COLOR = (230, 230, 230)

class DebugPanel:
    """Rechtes Overlay zum Auswählen und Platzieren von Assets.
    Steuerung:
      F1: Panel ein/aus
      Linksklick im Panel: Asset auswählen
      Shift + Linksklick in Welt: Ausgewähltes Asset platzieren (untere Mitte an Klick)
      R (bei offenem Panel): Assets neu scannen
      Mausrad: Scrollen
    """
    def __init__(self, screen_height, font=None):
        self.visible = False
        self.font = font or pygame.font.SysFont('Arial', 14)
        self.surface = pygame.Surface((DEBUG_PANEL_WIDTH, screen_height), pygame.SRCALPHA)
        self.scroll = 0
        self.entry_height = 48
        self.padding = 6
        self.assets = []  # list of dict {name, image, thumb, path}
        self.selected_index = None
        if DEBUG_ENABLE_AUTO_SCAN:
            self.scan_assets()

    def toggle(self):
        self.visible = not self.visible

    def is_mouse_over(self, mx, my, screen_width):
        if not self.visible:
            return False
        panel_left = screen_width - DEBUG_PANEL_WIDTH
        return mx >= panel_left

    def scan_assets(self, max_files=200):
        exts = {'.png'}
        collected = []
        for root, _, files in os.walk(ASSETS_DIR):
            for f in files:
                if len(collected) >= max_files:
                    break
                ext = os.path.splitext(f)[1].lower()
                if ext in exts:
                    path = os.path.join(root, f)
                    collected.append(path)
            if len(collected) >= max_files:
                break
        self.assets = []
        for p in collected:
            try:
                img = pygame.image.load(p).convert_alpha()
                tw, th = img.get_size()
                # Begrenze Thumb auf 40x40
                if tw == 0 or th == 0:
                    continue
                scale = min(40 / tw, 40 / th, 1.0)
                if scale != 1.0:
                    thumb = pygame.transform.smoothscale(img, (int(tw*scale), int(th*scale)))
                else:
                    thumb = img
                self.assets.append({
                    'name': os.path.basename(p),
                    'image': img,
                    'thumb': thumb,
                    'path': p
                })
            except Exception:
                continue

    def handle_event(self, event, screen_width):
        if not self.visible:
            return None
        panel_left = screen_width - DEBUG_PANEL_WIDTH
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if mx >= panel_left:
                if event.button == 4:
                    self.scroll = max(0, self.scroll - self.entry_height)
                elif event.button == 5:
                    max_scroll = max(0, len(self.assets)*self.entry_height - self.surface.get_height())
                    self.scroll = min(max_scroll, self.scroll + self.entry_height)
                elif event.button == 1:
                    rel_y = my + self.scroll
                    index = rel_y // self.entry_height
                    if 0 <= index < len(self.assets):
                        self.selected_index = index
                        return 'select'
        return None

    def get_selected_asset(self):
        if self.selected_index is None:
            return None
        if 0 <= self.selected_index < len(self.assets):
            return self.assets[self.selected_index]
        return None

    def draw(self, screen):
        if not self.visible:
            return
        h = self.surface.get_height()
        self.surface.fill(PANEL_BG)
        start_y = -self.scroll
        mouse_x, mouse_y = pygame.mouse.get_pos()
        panel_left = screen.get_width() - DEBUG_PANEL_WIDTH
        for idx, asset in enumerate(self.assets):
            y = start_y + idx * self.entry_height
            if y > h or y + self.entry_height < 0:
                continue
            rect = pygame.Rect(0, y, DEBUG_PANEL_WIDTH, self.entry_height)
            over = panel_left <= mouse_x < panel_left + DEBUG_PANEL_WIDTH and 0 <= mouse_y - y < self.entry_height
            bg = ENTRY_BG_HOVER if over else ENTRY_BG
            if idx == self.selected_index:
                bg = (min(bg[0]+30,255), min(bg[1]+30,255), min(bg[2]+30,255))
            pygame.draw.rect(self.surface, bg, rect)
            thumb = asset['thumb']
            self.surface.blit(thumb, (self.padding, y + (self.entry_height-thumb.get_height())//2))
            name_surf = self.font.render(asset['name'][:26], True, TEXT_COLOR)
            self.surface.blit(name_surf, (self.padding+48, y+ (self.entry_height-name_surf.get_height())//2))
        pygame.draw.rect(self.surface, PANEL_BORDER, (0,0,DEBUG_PANEL_WIDTH,h), 1)
        screen.blit(self.surface, (screen.get_width()-DEBUG_PANEL_WIDTH, 0))

    def world_click_to_place(self, world, world_pos):
        asset = self.get_selected_asset()
        if not asset:
            return False
        img = asset['image']
        x, y = world_pos
        w, h = img.get_size()
        place_x = int(x - w/2)
        place_y = int(y - h)
        if hasattr(world, 'add_dynamic_object'):
            return world.add_dynamic_object(img, place_x, place_y)
        return False
