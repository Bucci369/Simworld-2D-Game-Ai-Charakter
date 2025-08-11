"""
Asset Manager - Erweitert das Hauptspiel um getrennte Assets
"""

import os
import pygame
from pathlib import Path

class SplitAssetManager:
    """Verwaltet getrennte Assets aus dem Asset Splitter"""
    
    def __init__(self):
        self.split_assets = {}
        self.load_split_assets()
        
    def load_split_assets(self):
        """Lade alle getrennten Assets"""
        split_dir = Path("assets/split")
        if not split_dir.exists():
            return
            
        for collection_dir in split_dir.iterdir():
            if collection_dir.is_dir():
                collection_name = collection_dir.name
                self.split_assets[collection_name] = []
                
                # Lade alle PNG Dateien in der Collection
                for png_file in sorted(collection_dir.glob("*.png")):
                    if not png_file.name.endswith("_metadata.json"):
                        try:
                            image = pygame.image.load(str(png_file))
                            self.split_assets[collection_name].append({
                                'image': image,
                                'name': png_file.stem,
                                'path': str(png_file)
                            })
                        except Exception as e:
                            print(f"Fehler beim Laden von {png_file}: {e}")
                            
        print(f"Geladene Asset Collections: {list(self.split_assets.keys())}")
        for name, assets in self.split_assets.items():
            print(f"  {name}: {len(assets)} Items")
            
    def get_collection_assets(self, collection_name):
        """Hole alle Assets einer Collection"""
        return self.split_assets.get(collection_name, [])
        
    def get_asset_by_name(self, collection_name, asset_name):
        """Hole ein spezifisches Asset"""
        assets = self.get_collection_assets(collection_name)
        for asset in assets:
            if asset['name'] == asset_name:
                return asset['image']
        return None
