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
                # Common / Bulk - Front access (high frequency, trading)
                StorageMapRule(
                    card_types=['pokemon_common', 'pokemon'],
                    region=StorageRegion.FRONT,
                    description="Common Pokemon - front access for frequent trading/selling"
                ),
                # Uncommon - Middle storage
                StorageMapRule(
                    card_types=['pokemon_uncommon'],
                    region=StorageRegion.MIDDLE,
                    description="Uncommon Pokemon - moderate access"
                ),
                # Rare / Holo Rare - Back storage (protection)
                StorageMapRule(
                    card_types=['pokemon_rare', 'pokemon_holo_rare'],
                    region=StorageRegion.BACK,
                    description="Rare Pokemon - back storage for protection"
                ),
                # Ultra Rare / Secret Rare - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['pokemon_ultra_rare', 'pokemon_secret_rare', 'pokemon_full_art'],
                    region=StorageRegion.BOTTOM,
                    description="Ultra Rare Pokemon - bottom storage, maximum protection"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # Magic: The Gathering storage map
    elif 'magic' in franchise_lower or 'mtg' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Magic: The Gathering",
            rules=[
                # Common / Bulk - Front access (high frequency)
                StorageMapRule(
                    card_types=['mtg_common', 'mtg'],
                    region=StorageRegion.FRONT,
                    description="MTG Common - front access for frequent use"
                ),
                # Uncommon - Middle storage
                StorageMapRule(
                    card_types=['mtg_uncommon'],
                    region=StorageRegion.MIDDLE,
                    description="MTG Uncommon - moderate access"
                ),
                # Rare - Back storage (protection)
                StorageMapRule(
                    card_types=['mtg_rare'],
                    region=StorageRegion.BACK,
                    description="MTG Rare - back storage for protection"
                ),
                # Mythic Rare - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['mtg_mythic', 'mtg_mythic_rare'],
                    region=StorageRegion.BOTTOM,
                    description="Mythic Rare - bottom storage, maximum protection"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # Yu-Gi-Oh storage map
    elif 'yugioh' in franchise_lower or 'yu-gi-oh' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Yu-Gi-Oh!",
            rules=[
                # Common / Rare - Front access (high frequency)
                StorageMapRule(
                    card_types=['yugioh_common', 'yugioh_rare', 'yugioh'],
                    region=StorageRegion.FRONT,
                    description="Common/Rare Yu-Gi-Oh - front access for frequent trading"
                ),
                # Super Rare - Middle storage
                StorageMapRule(
                    card_types=['yugioh_super_rare'],
                    region=StorageRegion.MIDDLE,
                    description="Super Rare - moderate access"
                ),
                # Ultra Rare - Back storage (protection)
                StorageMapRule(
                    card_types=['yugioh_ultra_rare'],
                    region=StorageRegion.BACK,
                    description="Ultra Rare - back storage for protection"
                ),
                # Secret/Ultimate/Ghost Rare - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['yugioh_secret_rare', 'yugioh_ultimate_rare', 'yugioh_ghost_rare'],
                    region=StorageRegion.BOTTOM,
                    description="Secret/Ultimate/Ghost Rare - bottom storage, maximum protection"
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
                # Base / Common - Front access (high frequency)
                StorageMapRule(
                    card_types=['sports_nfl_base', 'sports_nfl'],
                    region=StorageRegion.FRONT,
                    description="NFL base cards - front access for frequent trading"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_nfl_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - moderate access"
                ),
                # Autographed / Memorabilia - Back storage (protection)
                StorageMapRule(
                    card_types=['sports_nfl_auto', 'sports_nfl_patch'],
                    region=StorageRegion.BACK,
                    description="Autographed/Memorabilia - back storage for protection"
                ),
                # Rookie / Graded - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['sports_nfl_rookie', 'sports_nfl_graded'],
                    region=StorageRegion.BOTTOM,
                    description="Rookie/Graded NFL - bottom storage, maximum protection"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # NBA storage map
    elif 'nba' in franchise_lower or 'basketball' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NBA",
            rules=[
                # Base / Common - Front access (high frequency)
                StorageMapRule(
                    card_types=['sports_nba_base', 'sports_nba'],
                    region=StorageRegion.FRONT,
                    description="NBA base cards - front access for frequent trading"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_nba_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - moderate access"
                ),
                # Autographed / Memorabilia - Back storage (protection)
                StorageMapRule(
                    card_types=['sports_nba_auto', 'sports_nba_patch'],
                    region=StorageRegion.BACK,
                    description="Autographed/Memorabilia - back storage for protection"
                ),
                # Rookie / Graded - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['sports_nba_rookie', 'sports_nba_graded'],
                    region=StorageRegion.BOTTOM,
                    description="Rookie/Graded NBA - bottom storage, maximum protection"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # MLB storage map
    elif 'mlb' in franchise_lower or 'baseball' in franchise_lower:
        return FranchiseStorageMap(
            franchise="MLB",
            rules=[
                # Base / Common - Front access (high frequency)
                StorageMapRule(
                    card_types=['sports_mlb_base', 'sports_mlb'],
                    region=StorageRegion.FRONT,
                    description="MLB base cards - front access for frequent trading"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_mlb_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - moderate access"
                ),
                # Autographed / Memorabilia - Back storage (protection)
                StorageMapRule(
                    card_types=['sports_mlb_auto', 'sports_mlb_patch'],
                    region=StorageRegion.BACK,
                    description="Autographed/Memorabilia - back storage for protection"
                ),
                # Vintage / Rookie / Graded - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['sports_mlb_vintage', 'sports_mlb_rookie', 'sports_mlb_graded'],
                    region=StorageRegion.BOTTOM,
                    description="Vintage/Rookie/Graded MLB - bottom storage, maximum protection"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # NHL storage map
    elif 'nhl' in franchise_lower or 'hockey' in franchise_lower:
        return FranchiseStorageMap(
            franchise="NHL",
            rules=[
                # Base / Common - Front access (high frequency)
                StorageMapRule(
                    card_types=['sports_nhl_base', 'sports_nhl'],
                    region=StorageRegion.FRONT,
                    description="NHL base cards - front access for frequent trading"
                ),
                # Star players - Middle storage
                StorageMapRule(
                    card_types=['sports_nhl_star'],
                    region=StorageRegion.MIDDLE,
                    description="Star players - moderate access"
                ),
                # Autographed / Memorabilia - Back storage (protection)
                StorageMapRule(
                    card_types=['sports_nhl_auto', 'sports_nhl_patch'],
                    region=StorageRegion.BACK,
                    description="Autographed/Memorabilia - back storage for protection"
                ),
                # Rookie / Graded - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['sports_nhl_rookie', 'sports_nhl_graded'],
                    region=StorageRegion.BOTTOM,
                    description="Rookie/Graded NHL - bottom storage, maximum protection"
                ),
            ],
            default_region=StorageRegion.MIDDLE
        )

    # Soccer storage map
    elif 'soccer' in franchise_lower or 'football' in franchise_lower and 'premier' in franchise_lower:
        return FranchiseStorageMap(
            franchise="Soccer",
            rules=[
                # Base / Common - Front access (high frequency)
                StorageMapRule(
                    card_types=['sports_soccer_base', 'sports_soccer'],
                    region=StorageRegion.FRONT,
                    description="Soccer base cards - front access for frequent trading"
                ),
                # Autographed - Back storage (protection)
                StorageMapRule(
                    card_types=['sports_soccer_auto'],
                    region=StorageRegion.BACK,
                    description="Autographed soccer - back storage for protection"
                ),
                # Rookie / Graded - Bottom storage (maximum protection)
                StorageMapRule(
                    card_types=['sports_soccer_rookie', 'sports_soccer_graded'],
                    region=StorageRegion.BOTTOM,
                    description="Rookie/Graded soccer - bottom storage, maximum protection"
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

