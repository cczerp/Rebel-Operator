"""
Storage Maps - Optional Card Organization Guidance

This module provides franchise-based storage map rules that suggest
recommended physical regions for organizing cards.

Storage maps are reference rules only - they do NOT track physical containers,
binders, boxes, pages, or slots. They only suggest conceptual regions like
"front", "middle", "back" or "left", "right" based on card type and franchise.
"""

from typing import Dict, Optional, List
from enum import Enum


class StorageRegion(str, Enum):
    """Conceptual storage regions - not physical containers"""
    FRONT = "front"
    MIDDLE = "middle"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"


class StorageMapRule:
    """A rule that maps card types to storage regions"""
    
    def __init__(
        self,
        card_types: List[str],
        region: StorageRegion,
        description: str = ""
    ):
        self.card_types = card_types
        self.region = region
        self.description = description


class FranchiseStorageMap:
    """Storage map for a specific franchise"""
    
    def __init__(
        self,
        franchise: str,
        rules: List[StorageMapRule],
        default_region: StorageRegion = StorageRegion.CENTER
    ):
        self.franchise = franchise
        self.rules = rules
        self.default_region = default_region
    
    def get_recommended_region(
        self,
        card_type: str,
        rarity: Optional[str] = None,
        is_rookie: bool = False,
        grading_score: Optional[float] = None
    ) -> StorageRegion:
        """
        Get recommended storage region for a card.
        
        Args:
            card_type: Card type (pokemon, mtg, sports_nfl, etc.)
            rarity: Card rarity (optional)
            is_rookie: Whether it's a rookie card (for sports)
            grading_score: Grading score if graded (optional)
        
        Returns:
            Recommended StorageRegion
        """
        # Check rules in order
        for rule in self.rules:
            if card_type in rule.card_types:
                return rule.region
        
        # Return default if no rule matches
        return self.default_region
    
    def get_guidance_text(self, region: StorageRegion) -> str:
        """Get human-readable guidance text for a region"""
        region_text = {
            StorageRegion.FRONT: "Store in the front section of your collection",
            StorageRegion.MIDDLE: "Store in the middle section of your collection",
            StorageRegion.BACK: "Store in the back section of your collection",
            StorageRegion.LEFT: "Store in the left side of your collection",
            StorageRegion.RIGHT: "Store in the right side of your collection",
            StorageRegion.TOP: "Store in the top section of your collection",
            StorageRegion.BOTTOM: "Store in the bottom section of your collection",
            StorageRegion.CENTER: "Store in the center section of your collection",
        }
        return region_text.get(region, "Store in your collection")


# ============================================================================
# FRANCHISE STORAGE MAPS
# ============================================================================

def get_storage_map_for_franchise(franchise: str) -> Optional[FranchiseStorageMap]:
    """
    Get storage map for a franchise.
    
    Args:
        franchise: Franchise name (e.g., "Pokemon", "Magic: The Gathering", "NFL")
    
    Returns:
        FranchiseStorageMap or None if no map exists
    """
    franchise_lower = franchise.lower()
    
    # Pokemon storage map
    if 'pokemon' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Pokemon",
            rules=[
                StorageMapRule(
                    card_types=['pokemon'],
                    region=StorageRegion.FRONT,
                    description="Pokemon cards - store in front"
                ),
            ],
            default_region=StorageRegion.FRONT
        )
    
    # Magic: The Gathering storage map
    elif 'magic' in franchise_lower or 'mtg' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Magic: The Gathering",
            rules=[
                StorageMapRule(
                    card_types=['mtg'],
                    region=StorageRegion.MIDDLE,
                    description="MTG cards - store in middle"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )
    
    # Yu-Gi-Oh storage map
    elif 'yugioh' in franchise_lower or 'yu-gi-oh' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Yu-Gi-Oh!",
            rules=[
                StorageMapRule(
                    card_types=['yugioh'],
                    region=StorageRegion.MIDDLE,
                    description="Yu-Gi-Oh cards - store in middle"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )
    
    # NFL storage map
    elif 'nfl' in franchise_lower or 'football' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NFL",
            rules=[
                StorageMapRule(
                    card_types=['sports_nfl'],
                    region=StorageRegion.FRONT,
                    description="NFL cards - store in front"
                ),
            ],
            default_region=StorageRegion.FRONT
        )
    
    # NBA storage map
    elif 'nba' in franchise_lower or 'basketball' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NBA",
            rules=[
                StorageMapRule(
                    card_types=['sports_nba'],
                    region=StorageRegion.FRONT,
                    description="NBA cards - store in front"
                ),
            ],
            default_region=StorageRegion.FRONT
        )
    
    # MLB storage map
    elif 'mlb' in franchise_lower or 'baseball' in franchise_lower:
        return FranchiseStorageMap(
            franchise="MLB",
            rules=[
                StorageMapRule(
                    card_types=['sports_mlb'],
                    region=StorageRegion.FRONT,
                    description="MLB cards - store in front"
                ),
            ],
            default_region=StorageRegion.FRONT
        )
    
    # NHL storage map
    elif 'nhl' in franchise_lower or 'hockey' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NHL",
            rules=[
                StorageMapRule(
                    card_types=['sports_nhl'],
                    region=StorageRegion.FRONT,
                    description="NHL cards - store in front"
                ),
            ],
            default_region=StorageRegion.FRONT
        )
    
    # Default: no specific map
    return None


def suggest_storage_region(
    franchise: Optional[str],
    card_type: str,
    rarity: Optional[str] = None,
    is_rookie: bool = False,
    grading_score: Optional[float] = None
) -> tuple[Optional[StorageRegion], Optional[str]]:
    """
    Suggest storage region based on franchise and card attributes.
    
    Args:
        franchise: Franchise name
        card_type: Card type
        rarity: Card rarity
        is_rookie: Whether it's a rookie card
        grading_score: Grading score if graded
    
    Returns:
        Tuple of (StorageRegion or None, guidance_text or None)
    """
    if not franchise:
        return None, None
    
    storage_map = get_storage_map_for_franchise(franchise)
    if not storage_map:
        return None, None
    
    region = storage_map.get_recommended_region(
        card_type=card_type,
        rarity=rarity,
        is_rookie=is_rookie,
        grading_score=grading_score
    )
    
    guidance = storage_map.get_guidance_text(region)
    
    return region, guidance

