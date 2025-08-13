import math
import os
import pygame
from settings import TILE_SIZE, PLAYER_SHEET_ROWS, PLAYER_FRAMES_PER_DIRECTION

ANIM_FRAME_TIME = 0.15  # Sekunden pro Frame

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, world=None):
        super().__init__()
        self.speed = 200
        self.target_pos: pygame.Vector2 | None = None
        self.arrive_threshold = 4
        self.world = world  # SimpleWorld Referenz für Kollision

        # Animationsverwaltung
        self.direction = 'down'  # down, up, left, right
        self.anim_time_acc = 0.0
        self.anim_frame_index = 0
        self.animations: dict[str, list[pygame.Surface]] = {}
        self.idle_frames: dict[str, pygame.Surface] = {}

        self._load_sheet()
        # Fallback falls nichts geladen wurde
        if not self.animations:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill((255, 255, 0))
            self.animations = {d: [surf] for d in ['down','up','left','right']}
            self.idle_frames = {d: surf for d in ['down','up','left','right']}

        self.image = self.idle_frames[self.direction]
        self.rect = self.image.get_rect(topleft=pos)

    def _load_sheet(self):
        """Liest das Sprite-Sheet dynamisch und schneidet 32x32-Kacheln.
        Erwartete Reihenfolge (Heuristik):
        row 0: walk down, row 1: walk left, row 2: walk right, row 3: walk up.
        Zusätzliche Reihen ignoriert (z.B. Angriffe / Spezial)."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        sheet_path = os.path.join(base_dir, 'assets', 'Player', 'character-grid-sprite.png')
        if not os.path.exists(sheet_path):
            return
        try:
            sheet = pygame.image.load(sheet_path).convert_alpha()
        except Exception:
            return
        w, h = sheet.get_size()
        cols = w // TILE_SIZE
        rows = h // TILE_SIZE
        # mind. 4 Reihen für die 4 Richtungen? Wenn weniger -> Mapping anpassen.
        # Slice alle Tiles
        grid: list[list[pygame.Surface]] = []
        for ry in range(rows):
            row_frames = []
            y = ry * TILE_SIZE
            for cx in range(cols):
                x = cx * TILE_SIZE
                frame = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), (x, y, TILE_SIZE, TILE_SIZE))
                # Transparente oder komplett leere Frames überspringen? -> Prüfen Pixel Alpha
                if pygame.mask.from_surface(frame).count() == 0:
                    continue
                row_frames.append(frame)
            if row_frames:
                grid.append(row_frames)

        # Konfiguriertes Mapping der Reihen
        for direction, row_index in PLAYER_SHEET_ROWS.items():
            if row_index == -1 and direction == 'left':
                # Mirror der right-Frames wird später gemacht
                continue
            if 0 <= row_index < len(grid):
                row_frames = grid[row_index]
                frames = row_frames[:PLAYER_FRAMES_PER_DIRECTION] if PLAYER_FRAMES_PER_DIRECTION else row_frames
                if frames:
                    self.animations[direction] = frames
                    self.idle_frames[direction] = frames[0]

        # Mirroring für left falls konfiguriert
        if PLAYER_SHEET_ROWS.get('left') == -1 and 'right' in self.animations:
            mirrored = [pygame.transform.flip(f, True, False) for f in self.animations['right']]
            self.animations['left'] = mirrored
            self.idle_frames['left'] = mirrored[0]
        if self.animations:
            try:
                print("[Player] Geladene Reihen / Mapping:", {d: PLAYER_SHEET_ROWS.get(d) for d in self.animations})
            except Exception:
                pass

        # Fallback falls bestimmte Richtungen fehlen
        if len(self.animations) < 4 and grid:
            first = next(iter(self.animations.values()), grid[0])
            for d in ['down','left','right','up']:
                if d not in self.animations:
                    self.animations[d] = first
                    self.idle_frames[d] = first[0]

    def set_target(self, world_pos):
        self.target_pos = pygame.Vector2(world_pos)

    def stop(self):
        self.target_pos = None

    def _update_direction(self, move_vec: pygame.Vector2):
        if move_vec.length_squared() == 0:
            return
        dx, dy = move_vec.x, move_vec.y
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'

    def _animate(self, dt, moving: bool):
        frames = self.animations[self.direction]
        if not moving:
            self.anim_frame_index = 0
            self.image = self.idle_frames[self.direction]
            return
        self.anim_time_acc += dt
        if self.anim_time_acc >= ANIM_FRAME_TIME:
            self.anim_time_acc -= ANIM_FRAME_TIME
            self.anim_frame_index = (self.anim_frame_index + 1) % len(frames)
        self.image = frames[self.anim_frame_index]

    def update(self, dt):
        """🚀 SMOOTH MOVEMENT: Optimierte Player-Bewegung für flüssiges Scrolling"""
        moving = False
        if self.target_pos:
            current = pygame.Vector2(self.rect.center)
            delta = self.target_pos - current
            dist = delta.length()
            
            if dist <= self.arrive_threshold:
                # Ziel erreicht
                self.rect.center = (int(self.target_pos.x), int(self.target_pos.y))
                self.target_pos = None
            else:
                direction = delta / dist if dist else pygame.Vector2()
                step = direction * self.speed * dt
                
                if step.length() >= dist:
                    # Würde über Ziel hinausschießen
                    self.rect.center = (int(self.target_pos.x), int(self.target_pos.y))
                    self.target_pos = None
                else:
                    # 🚀 SMOOTH: Floating-Point-Position für sanfte Bewegung
                    tentative = current + step
                    new_rect = self.rect.copy()
                    
                    # Verwende Float-Werte für sanfte Bewegung, aber int für Rect
                    new_center_x = tentative.x
                    new_center_y = tentative.y
                    new_rect.center = (int(new_center_x), int(new_center_y))
                    
                    # Kollisionserkennung
                    collision = False
                    if self.world:
                        if hasattr(self.world, 'is_walkable'):
                            collision = not self.world.is_walkable(new_center_x, new_center_y)
                        elif hasattr(self.world, 'is_blocked_rect'):
                            collision = self.world.is_blocked_rect(new_rect)
                    
                    if collision:
                        # Stop bei Kollision
                        self.target_pos = None
                        # Entferne debug print für bessere Performance
                        # print(f"🚫 Collision at: ({new_center_x:.1f}, {new_center_y:.1f})")
                    else:
                        # 🚀 SMOOTH: Aktualisiere Position sanft
                        self.rect = new_rect
                        
                self._update_direction(delta)
                moving = True
                
        self._animate(dt, moving)
