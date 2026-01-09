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

    # ========================================================================
    # TRADING CARD GAMES (TCG)
    # ========================================================================

    # Pokemon storage map
    if 'pokemon' in franchise_lower or 'pokémon' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Pokemon",
            rules=[
                # Ultra Rare / Secret Rare - Top priority access
                StorageMapRule(
                    card_types=['pokemon_ultra_rare', 'pokemon_secret_rare', 'pokemon_full_art'],
                    region=StorageRegion.TOP,
                    description="Ultra Rare Pokemon - premium storage (binder recommended)"
                ),
                # Rare / Holo Rare - Front access for trading
                StorageMapRule(
                    card_types=['pokemon_rare', 'pokemon_holo_rare'],
                    region=StorageRegion.FRONT,
                    description="Rare Pokemon - easy access for trading/selling"
                ),
                # Uncommon - Middle storage
                StorageMapRule(
                    card_types=['pokemon_uncommon'],
                    region=StorageRegion.MIDDLE,
                    description="Uncommon Pokemon - moderate access"
                ),
                # Common / Bulk - Back storage
                StorageMapRule(
                    card_types=['pokemon_common', 'pokemon'],
                    region=StorageRegion.BACK,
                    description="Common Pokemon - bulk storage"
                ),
            ],
            default_region=StorageRegion.FRONT
        )

    # Magic: The Gathering storage map
    elif 'magic' in franchise_lower or 'mtg' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Magic: The Gathering",
            rules=[
                # Mythic Rare - Top storage
                StorageMapRule(
                    card_types=['mtg_mythic', 'mtg_mythic_rare'],
                    region=StorageRegion.TOP,
                    description="Mythic Rare - premium storage"
                ),
                # Rare - Front storage
                StorageMapRule(
                    card_types=['mtg_rare'],
                    region=StorageRegion.FRONT,
                    description="MTG Rare - front access for decks"
                ),
                # Uncommon - Middle storage
                StorageMapRule(
                    card_types=['mtg_uncommon'],
                    region=StorageRegion.MIDDLE,
                    description="MTG Uncommon - moderate access"
                ),
                # Common / Bulk - Back storage
                StorageMapRule(
                    card_types=['mtg_common', 'mtg'],
                    region=StorageRegion.BACK,
                    description="MTG Common - bulk storage"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # Yu-Gi-Oh storage map
    elif 'yugioh' in franchise_lower or 'yu-gi-oh' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Yu-Gi-Oh!",
            rules=[
                # Secret Rare / Ultimate Rare - Top storage
                StorageMapRule(
                    card_types=['yugioh_secret_rare', 'yugioh_ultimate_rare', 'yugioh_ghost_rare'],
                    region=StorageRegion.TOP,
                    description="Secret/Ultimate Rare - premium storage"
                ),
                # Ultra Rare - Front storage
                StorageMapRule(
                    card_types=['yugioh_ultra_rare'],
                    region=StorageRegion.FRONT,
                    description="Ultra Rare Yu-Gi-Oh - easy access"
                ),
                # Super Rare - Middle storage
                StorageMapRule(
                    card_types=['yugioh_super_rare'],
                    region=StorageRegion.MIDDLE,
                    description="Super Rare - moderate access"
                ),
                # Common / Rare - Back storage
                StorageMapRule(
                    card_types=['yugioh_common', 'yugioh_rare', 'yugioh'],
                    region=StorageRegion.BACK,
                    description="Common/Rare - bulk storage"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # ========================================================================
    # SPORTS CARDS
    # ========================================================================

    # NFL storage map
    elif 'nfl' in franchise_lower or 'football' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NFL",
            rules=[
                # Graded cards - Top storage
                StorageMapRule(
                    card_types=['sports_nfl_graded'],
                    region=StorageRegion.TOP,
                    description="Graded NFL cards - top loader storage"
                ),
                # Rookie cards - Front storage
                StorageMapRule(
                    card_types=['sports_nfl_rookie'],
                    region=StorageRegion.FRONT,
                    description="NFL Rookie cards - front access (high value)"
                ),
                # Autographed / Memorabilia - Front storage
                StorageMapRule(
                    card_types=['sports_nfl_auto', 'sports_nfl_patch'],
                    region=StorageRegion.FRONT,
                    description="Autographed/Memorabilia - front access"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_nfl_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - middle storage"
                ),
                # Base / Common - Back storage
                StorageMapRule(
                    card_types=['sports_nfl_base', 'sports_nfl'],
                    region=StorageRegion.BACK,
                    description="NFL base cards - back storage"
                ),
            ],
            default_region=StorageRegion.FRONT
        )

    # NBA storage map
    elif 'nba' in franchise_lower or 'basketball' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NBA",
            rules=[
                # Graded cards - Top storage
                StorageMapRule(
                    card_types=['sports_nba_graded'],
                    region=StorageRegion.TOP,
                    description="Graded NBA cards - top loader storage"
                ),
                # Rookie cards - Front storage
                StorageMapRule(
                    card_types=['sports_nba_rookie'],
                    region=StorageRegion.FRONT,
                    description="NBA Rookie cards - front access (high value)"
                ),
                # Autographed / Memorabilia - Front storage
                StorageMapRule(
                    card_types=['sports_nba_auto', 'sports_nba_patch'],
                    region=StorageRegion.FRONT,
                    description="Autographed/Memorabilia - front access"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_nba_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - middle storage"
                ),
                # Base / Common - Back storage
                StorageMapRule(
                    card_types=['sports_nba_base', 'sports_nba'],
                    region=StorageRegion.BACK,
                    description="NBA base cards - back storage"
                ),
            ],
            default_region=StorageRegion.FRONT
        )

    # MLB storage map
    elif 'mlb' in franchise_lower or 'baseball' in franchise_lower:
        return FranchiseStorageMap(
            franchise="MLB",
            rules=[
                # Graded cards - Top storage
                StorageMapRule(
                    card_types=['sports_mlb_graded'],
                    region=StorageRegion.TOP,
                    description="Graded MLB cards - top loader storage"
                ),
                # Rookie cards - Front storage
                StorageMapRule(
                    card_types=['sports_mlb_rookie'],
                    region=StorageRegion.FRONT,
                    description="MLB Rookie cards - front access (high value)"
                ),
                # Autographed / Memorabilia - Front storage
                StorageMapRule(
                    card_types=['sports_mlb_auto', 'sports_mlb_patch'],
                    region=StorageRegion.FRONT,
                    description="Autographed/Memorabilia - front access"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_mlb_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - middle storage"
                ),
                # Vintage (pre-1980) - Front storage
                StorageMapRule(
                    card_types=['sports_mlb_vintage'],
                    region=StorageRegion.FRONT,
                    description="Vintage MLB - front access (collectible value)"
                ),
                # Base / Common - Back storage
                StorageMapRule(
                    card_types=['sports_mlb_base', 'sports_mlb'],
                    region=StorageRegion.BACK,
                    description="MLB base cards - back storage"
                ),
            ],
            default_region=StorageRegion.FRONT
        )

    # NHL storage map
    elif 'nhl' in franchise_lower or 'hockey' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NHL",
            rules=[
                # Graded cards - Top storage
                StorageMapRule(
                    card_types=['sports_nhl_graded'],
                    region=StorageRegion.TOP,
                    description="Graded NHL cards - top loader storage"
                ),
                # Rookie cards - Front storage
                StorageMapRule(
                    card_types=['sports_nhl_rookie'],
                    region=StorageRegion.FRONT,
                    description="NHL Rookie cards - front access (high value)"
                ),
                # Autographed / Memorabilia - Front storage
                StorageMapRule(
                    card_types=['sports_nhl_auto', 'sports_nhl_patch'],
                    region=StorageRegion.FRONT,
                    description="Autographed/Memorabilia - front access"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_nhl_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - middle storage"
                ),
                # Base / Common - Back storage
                StorageMapRule(
                    card_types=['sports_nhl_base', 'sports_nhl'],
                    region=StorageRegion.BACK,
                    description="NHL base cards - back storage"
                ),
            ],
            default_region=StorageRegion.FRONT
        )

    # Soccer storage map
    elif 'soccer' in franchise_lower or 'football' in franchise_lower and 'premier' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Soccer",
            rules=[
                # Graded cards - Top storage
                StorageMapRule(
                    card_types=['sports_soccer_graded'],
                    region=StorageRegion.TOP,
                    description="Graded soccer cards - top loader storage"
                ),
                # Rookie cards - Front storage
                StorageMapRule(
                    card_types=['sports_soccer_rookie'],
                    region=StorageRegion.FRONT,
                    description="Soccer Rookie cards - front access"
                ),
                # Autographed - Front storage
                StorageMapRule(
                    card_types=['sports_soccer_auto'],
                    region=StorageRegion.FRONT,
                    description="Autographed soccer cards - front access"
                ),
                # Base / Common - Back storage
                StorageMapRule(
                    card_types=['sports_soccer_base', 'sports_soccer'],
                    region=StorageRegion.BACK,
                    description="Soccer base cards - back storage"
                ),
            ],
            default_region=StorageRegion.MIDDLE
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

