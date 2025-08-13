import pygame
import os
from typing import Dict, Optional, Tuple

class AssetManager:
    """Zentraler Asset-Manager mit intelligentem Caching für Performance-Optimierung"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.image_cache: Dict[str, pygame.Surface] = {}
        self.scaled_cache: Dict[Tuple[str, int, int], pygame.Surface] = {}
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Preload kritische Assets
        self._preload_critical_assets()
    
    def _preload_critical_assets(self):
        """Lade nur die wichtigsten Assets beim Start"""
        critical_assets = [
            # Original Assets
            'Tiles/Grass_Middle.png',
            'Tiles/Water_Middle.png', 
            'Tiles/Path_Middle.png',
            'Tiles/FarmLand_Tile.png',
            'Outdoor decoration/Oak_Tree.png',
            'Outdoor decoration/House.png',
            # 🏘️ KENNEY CRITICAL ASSETS
            'kenney_sketch-town-expansion/Tiles/grass_block_E.png',
            'kenney_sketch-town-expansion/Tiles/cliff_E.png',
            'kenney_sketch-town-expansion/Tiles/dirt_corner_E.png',
            'kenney_sketch-town-expansion/Tiles/tree_pine_E.png',
            'kenney_sketch-town-expansion/Tiles/furrow_E.png',
            'kenney_sketch-town-expansion/Tiles/well_E.png'
        ]
        
        print("🚀 Preloading critical assets...")
        for asset_path in critical_assets:
            full_path = os.path.join(self.base_dir, asset_path)
            if os.path.exists(full_path):
                self.load_image(asset_path)
        print(f"✅ Preloaded {len(self.image_cache)} critical assets")
    
    def load_image(self, relative_path: str, convert_alpha: bool = True) -> Optional[pygame.Surface]:
        """Lade Bild mit Caching"""
        if relative_path in self.image_cache:
            self.cache_hits += 1
            return self.image_cache[relative_path]
        
        # Cache miss - lade Bild
        self.cache_misses += 1
        full_path = os.path.join(self.base_dir, relative_path)
        
        if not os.path.exists(full_path):
            # Suche in allen Unterordnern
            filename = os.path.basename(relative_path)
            for root, dirs, files in os.walk(self.base_dir):
                if filename in files:
                    full_path = os.path.join(root, filename)
                    break
            else:
                print(f"⚠️ Asset not found: {relative_path}")
                return None
        
        try:
            image = pygame.image.load(full_path)
            # 🚀 FIX: Nur convert wenn pygame.display initialisiert ist
            try:
                if convert_alpha:
                    image = image.convert_alpha()
                else:
                    image = image.convert()
            except pygame.error:
                # Display not initialized yet, use raw image
                pass
            
            # Cache begrenzen auf 100 Assets
            if len(self.image_cache) >= 100:
                # Entferne älteste 20 Assets
                keys_to_remove = list(self.image_cache.keys())[:20]
                for key in keys_to_remove:
                    del self.image_cache[key]
            
            self.image_cache[relative_path] = image
            return image
            
        except Exception as e:
            print(f"❌ Failed to load {relative_path}: {e}")
            return None
    
    def load_scaled_image(self, relative_path: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
        """Lade und skaliere Bild mit Caching"""
        cache_key = (relative_path, size[0], size[1])
        
        if cache_key in self.scaled_cache:
            self.cache_hits += 1
            return self.scaled_cache[cache_key]
        
        # Lade Basis-Bild
        base_image = self.load_image(relative_path)
        if not base_image:
            return None
        
        # Skaliere und cache
        try:
            scaled_image = pygame.transform.scale(base_image, size)
            
            # Scaled Cache begrenzen auf 200 Assets
            if len(self.scaled_cache) >= 200:
                # Entferne älteste 50 scaled Assets
                keys_to_remove = list(self.scaled_cache.keys())[:50]
                for key in keys_to_remove:
                    del self.scaled_cache[key]
            
            self.scaled_cache[cache_key] = scaled_image
            return scaled_image
            
        except Exception as e:
            print(f"❌ Failed to scale {relative_path}: {e}")
            return base_image
    
    def get_cache_stats(self) -> dict:
        """Debug-Info über Cache-Performance"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'images_cached': len(self.image_cache),
            'scaled_cached': len(self.scaled_cache), 
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }
    
    def clear_cache(self):
        """Cache leeren (für Memory Management)"""
        self.image_cache.clear()
        self.scaled_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        print("🧹 Asset cache cleared")

# Globale Instanz
asset_manager = AssetManager()