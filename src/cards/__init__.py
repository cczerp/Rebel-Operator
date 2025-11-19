"""Card Collection Organization System

This module provides a unified system for organizing trading cards and sports cards.
Supports: Pokémon, MTG, Yu-Gi-Oh, NFL, NBA, MLB, NHL, and more.
"""

from .unified_card import UnifiedCard
from .card_manager import CardCollectionManager
from .classifiers import (
    PokemonCardClassifier,
    MTGCardClassifier,
    YuGiOhCardClassifier,
    SportsCardClassifier,
)

__all__ = [
    'UnifiedCard',
    'CardCollectionManager',
    'PokemonCardClassifier',
    'MTGCardClassifier',
    'YuGiOhCardClassifier',
    'SportsCardClassifier',
]
