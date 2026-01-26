"""
CSV Export System
Converts universal listing format to platform-specific CSV formats
"""

from .base_exporter import BaseCSVExporter
from .poshmark_exporter import PoshmarkExporter
from .rubylane_exporter import RubyLaneExporter
from .ecrater_exporter import EcraterExporter
from .bonanza_exporter import BonanzaExporter
from .google_shopping_exporter import GoogleShoppingExporter
from .ebay_exporter import EbayExporter
from .mercari_exporter import MercariExporter
from .discogs_exporter import DiscogsExporter

__all__ = [
    'BaseCSVExporter',
    'PoshmarkExporter',
    'RubyLaneExporter',
    'EcraterExporter',
    'BonanzaExporter',
    'GoogleShoppingExporter',
    'EbayExporter',
    'MercariExporter',
    'DiscogsExporter',
    'get_exporter'
]

# Platform registry
EXPORTERS = {
    'poshmark': PoshmarkExporter,
    'rubylane': RubyLaneExporter,
    'ruby_lane': RubyLaneExporter,
    'ecrater': EcraterExporter,
    'bonanza': BonanzaExporter,
    'google_shopping': GoogleShoppingExporter,
    'google': GoogleShoppingExporter,
    'ebay': EbayExporter,
    'mercari': MercariExporter,
    'discogs': DiscogsExporter,
}

def get_exporter(platform: str):
    """Get the appropriate exporter for a platform"""
    platform = platform.lower().replace(' ', '_')
    exporter_class = EXPORTERS.get(platform)
    if not exporter_class:
        raise ValueError(f"No CSV exporter available for platform: {platform}")
    return exporter_class()
