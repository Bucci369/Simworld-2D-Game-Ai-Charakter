import pygame
import os
import logging

logger = logging.getLogger(__name__)

class CharacterSprites:
    def __init__(self):
        # Stelle sicher, dass pygame initialisiert ist
        if not pygame.get_init():
            logger.warning("⚠️ Pygame nicht initialisiert, initialisiere es jetzt...")
            pygame.init()
            
        # Stelle sicher, dass das Display initialisiert ist für das Laden von Bildern
        if not pygame.display.get_surface():
            logger.info("🎮 Initialisiere Display für Sprite-Loading...")
            # Erstelle ein minimales Display für das Laden von Sprites
            pygame.display.set_mode((1, 1))
            
        self.sprite_sheet = None
        self.character_frames = {}  # Dictionary für die Animations-Frames jedes Charakters
        self.frame_width = 103     # Breite eines Charakters (1131 / 11 = 103)
        self.frame_height = 103    # Höhe eines Charakters (206 / 2 = 103)
        self.animation_timer = 0
        self.current_frame = 0
        self.animation_speed = 0.3  # Sekunden pro Frame
        self.frame_timers = {}     # Separate Timer für jeden Charakter
        self.debug_mode = True
        
        # Initialisiere die Frame-Timer für jeden Charakter
        for i in range(11):
            self.frame_timers[i] = 0
        
        self._load_sprite_sheet()
        
    def _load_sprite_sheet(self):
        try:
            # Versuche verschiedene Pfade für das Sprite-Sheet
            possible_paths = [
                os.path.join("assets", "characters.png"),
                os.path.join("assets", "debug_sheet.png"),
                os.path.join("assets", "2D Character Assets pack", "characters.png"),
                os.path.join("assets", "2D Character Assets pack", "debug_sheet.png")
            ]
            
            self.sprite_sheet = None
            loaded_path = None
            
            for sprite_path in possible_paths:
                if os.path.exists(sprite_path):
                    try:
                        self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                        loaded_path = sprite_path
                        break
                    except Exception as e:
                        logger.warning(f"⚠️ Konnte {sprite_path} nicht laden: {e}")
                        continue
            
            if not self.sprite_sheet:
                raise FileNotFoundError("Keine gültigen Sprite-Sheets gefunden")
            
            # Debug-Info
            logger.info(f"🎮 Character Sprite Sheet geladen: {loaded_path}")
            logger.info(f"🎮 Sprite Sheet Dimensionen: {self.sprite_sheet.get_width()}x{self.sprite_sheet.get_height()}")
            
            # Extrahiere die Frames für jeden Charakter
            for char_idx in range(11):
                frames = []
                
                # Extrahiere beide Frames (oben und unten)
                for frame_idx in range(2):
                    x = char_idx * self.frame_width
                    y = frame_idx * self.frame_height
                    
                    # Extrahiere den Frame
                    frame_surface = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
                    frame_surface.blit(self.sprite_sheet, (0, 0), (x, y, self.frame_width, self.frame_height))
                    
                    # Skaliere auf 32x32 für gute NPC-Sichtbarkeit
                    scaled_frame = pygame.transform.scale(frame_surface, (32, 32))
                    frames.append(scaled_frame)
                    
                    # Debug: Speichere Frame
                    if self.debug_mode:
                        debug_dir = os.path.join("debug_sprites")
                        if not os.path.exists(debug_dir):
                            os.makedirs(debug_dir)
                        debug_path = os.path.join(debug_dir, f"char_{char_idx}_frame_{frame_idx}.png")
                        pygame.image.save(scaled_frame, debug_path)
                        logger.info(f"💾 Debug Frame gespeichert: {debug_path}")
                
                self.character_frames[char_idx] = frames
                logger.info(f"✅ Character Sprite-Sheet geladen: {len(self.character_frames)} Charaktere")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Character Sprite-Sheets: {str(e)}")
            # Erstelle Fallback-Sprite
            fallback = pygame.Surface((60, 60), pygame.SRCALPHA)
            fallback.fill((255, 0, 0, 128))  # Halbtransparentes Rot
            self.character_frames[0] = [fallback, fallback]
    
    def get_frame(self, char_index: int, dt: float) -> pygame.Surface:
        """Gibt den aktuellen Animationsframe für den gewählten Charakter zurück"""
        if char_index not in self.character_frames:
            logger.warning(f"⚠️ Charakter {char_index} nicht gefunden, nutze Fallback")
            char_index = 0  # Fallback zum ersten Charakter
            
        # Aktualisiere den Timer für diesen Charakter
        self.frame_timers[char_index] += dt
        
        # Berechne aktuellen Frame - wechsle zwischen 0 und 1
        current_frame = int(self.frame_timers[char_index] / self.animation_speed) % 2
        
        # Reset Timer wenn er zu groß wird
        if self.frame_timers[char_index] >= self.animation_speed * 2:
            self.frame_timers[char_index] = 0
            
        return self.character_frames[char_index][current_frame]
