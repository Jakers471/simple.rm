"""
Symbol parsing utilities for contract ID and symbol extraction.
"""

import logging

logger = logging.getLogger(__name__)


def extract_symbol_root(contract_id: str) -> str:
    """
    Extract symbol root from contract ID.

    Examples:
    - "CON.F.US.RTY.H25" → "RTY"
    - "CON.F.US.ES.U25" → "ES"
    - "CON.F.US.MNQ.M25" → "MNQ"
    - "CON.F.US.BTC.Z25" → "BTC"

    Args:
        contract_id: Full contract identifier (e.g., "CON.F.US.RTY.H25")

    Returns:
        Symbol root (e.g., "RTY")
    """
    # Contract ID format: CON.F.{region}.{symbol}.{expiry}
    parts = contract_id.split('.')

    if len(parts) >= 4:
        return parts[3]  # Symbol is 4th part (0-indexed: parts[3])

    # Fallback: return full contract ID if format unexpected
    logger.warning(f"Unexpected contract ID format: {contract_id}")
    return contract_id


__all__ = ['extract_symbol_root']
