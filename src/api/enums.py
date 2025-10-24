"""Order state enum mappings for TopstepX API integration.

This module resolves the contract mismatch between:
1. TopstepX API order states (what the API actually sends)
2. Internal order states (used by our backend logic)
3. SPEC definitions (what was originally documented)

See docs/contracts/enum_mapping.md for full rationale.
"""

from enum import IntEnum
from typing import Optional


class TopstepXOrderState(IntEnum):
    """Order states as received from TopstepX API.

    These are the actual integer values sent by TopstepX Gateway API
    in the 'status' field of order objects (REST API and SignalR events).

    Based on official OrderStatus enum from TopstepX Gateway API documentation:
    Source: projectx_gateway_api/realtime_updates/realtime_data_overview.md (lines 438-451)

    Verified with actual API response examples showing:
    - status=1 for open/working orders (fillVolume=0)
    - status=2 for filled orders (fillVolume > 0)
    """
    NONE = 0        # No status / Unknown
    OPEN = 1        # Order is working on exchange (active)
    FILLED = 2      # Order completely filled
    CANCELLED = 3   # Order cancelled by user or system
    EXPIRED = 4     # Order expired
    REJECTED = 5    # Order rejected by exchange
    PENDING = 6     # Order submitted but not yet working


class InternalOrderState(IntEnum):
    """Internal order states used by backend logic.

    These are normalized states that make sense for our risk management
    logic, abstracting away API-specific details.

    Design decisions:
    - PENDING: Order exists but not yet active (maps to TopstepX PENDING)
    - ACTIVE: Order is working on exchange (maps to TopstepX WORKING)
    - FILLED: Order completely filled (terminal state)
    - CANCELLED: Order was cancelled (terminal state)
    - REJECTED: Order was rejected (terminal state)
    - EXPIRED: Order expired (TopstepX may add this in future)
    - PARTIAL: Partially filled (may be added later for advanced tracking)
    """
    PENDING = 1
    ACTIVE = 2
    FILLED = 3
    CANCELLED = 4
    REJECTED = 5
    EXPIRED = 6      # Reserved for future use
    PARTIAL = 7      # Reserved for future use


def api_to_internal_order_state(api_state: int) -> InternalOrderState:
    """Convert TopstepX API order state to internal representation.

    Args:
        api_state: Integer state value from TopstepX API (0-6, from OrderStatus enum)

    Returns:
        Internal order state enum value

    Raises:
        ValueError: If api_state is not a valid TopstepX order state

    Example:
        >>> api_to_internal_order_state(1)  # OPEN
        <InternalOrderState.ACTIVE: 2>
        >>> api_to_internal_order_state(2)  # FILLED
        <InternalOrderState.FILLED: 3>
    """
    mapping = {
        TopstepXOrderState.NONE: InternalOrderState.PENDING,        # Map unknown to pending
        TopstepXOrderState.OPEN: InternalOrderState.ACTIVE,         # Open = working on exchange
        TopstepXOrderState.FILLED: InternalOrderState.FILLED,       # Filled
        TopstepXOrderState.CANCELLED: InternalOrderState.CANCELLED, # Cancelled
        TopstepXOrderState.EXPIRED: InternalOrderState.EXPIRED,     # Expired
        TopstepXOrderState.REJECTED: InternalOrderState.REJECTED,   # Rejected
        TopstepXOrderState.PENDING: InternalOrderState.PENDING,     # Pending = not yet working
    }

    try:
        api_enum = TopstepXOrderState(api_state)
    except ValueError:
        raise ValueError(
            f"Invalid TopstepX order state: {api_state}. "
            f"Valid values are: {[s.value for s in TopstepXOrderState]}"
        )

    return mapping[api_enum]


def internal_to_api_order_state(internal_state: InternalOrderState) -> int:
    """Convert internal order state to TopstepX API representation.

    Args:
        internal_state: Internal order state enum value

    Returns:
        Integer state value for TopstepX API (0-6, OrderStatus enum)

    Raises:
        ValueError: If internal_state cannot be mapped to API state

    Example:
        >>> internal_to_api_order_state(InternalOrderState.ACTIVE)
        1  # OPEN
        >>> internal_to_api_order_state(InternalOrderState.FILLED)
        2  # FILLED
    """
    reverse_mapping = {
        InternalOrderState.PENDING: TopstepXOrderState.PENDING,     # 6
        InternalOrderState.ACTIVE: TopstepXOrderState.OPEN,         # 1
        InternalOrderState.FILLED: TopstepXOrderState.FILLED,       # 2
        InternalOrderState.CANCELLED: TopstepXOrderState.CANCELLED, # 3
        InternalOrderState.REJECTED: TopstepXOrderState.REJECTED,   # 5
        InternalOrderState.EXPIRED: TopstepXOrderState.EXPIRED,     # 4
    }

    if internal_state not in reverse_mapping:
        raise ValueError(
            f"Cannot map internal state {internal_state} to TopstepX API state. "
            f"Mappable states are: {list(reverse_mapping.keys())}"
        )

    return reverse_mapping[internal_state].value


def is_terminal_state(state: InternalOrderState) -> bool:
    """Check if order state is terminal (order is done, won't change).

    Terminal states: FILLED, CANCELLED, REJECTED, EXPIRED
    Non-terminal states: PENDING, ACTIVE, PARTIAL

    Args:
        state: Internal order state to check

    Returns:
        True if state is terminal, False otherwise

    Example:
        >>> is_terminal_state(InternalOrderState.FILLED)
        True
        >>> is_terminal_state(InternalOrderState.ACTIVE)
        False
    """
    terminal_states = {
        InternalOrderState.FILLED,
        InternalOrderState.CANCELLED,
        InternalOrderState.REJECTED,
        InternalOrderState.EXPIRED,
    }
    return state in terminal_states


def is_active_state(state: InternalOrderState) -> bool:
    """Check if order state means order is still working on exchange.

    Active states: PENDING, ACTIVE, PARTIAL
    Inactive states: FILLED, CANCELLED, REJECTED, EXPIRED

    Args:
        state: Internal order state to check

    Returns:
        True if order is still active, False otherwise

    Example:
        >>> is_active_state(InternalOrderState.ACTIVE)
        True
        >>> is_active_state(InternalOrderState.FILLED)
        False
    """
    active_states = {
        InternalOrderState.PENDING,
        InternalOrderState.ACTIVE,
        InternalOrderState.PARTIAL,
    }
    return state in active_states


def get_order_state_display_name(state: InternalOrderState) -> str:
    """Get human-readable display name for order state.

    Args:
        state: Internal order state

    Returns:
        Human-readable string (e.g., "Working", "Filled")

    Example:
        >>> get_order_state_display_name(InternalOrderState.ACTIVE)
        'Working'
        >>> get_order_state_display_name(InternalOrderState.FILLED)
        'Filled'
    """
    display_names = {
        InternalOrderState.PENDING: "Pending",
        InternalOrderState.ACTIVE: "Working",
        InternalOrderState.FILLED: "Filled",
        InternalOrderState.CANCELLED: "Cancelled",
        InternalOrderState.REJECTED: "Rejected",
        InternalOrderState.EXPIRED: "Expired",
        InternalOrderState.PARTIAL: "Partially Filled",
    }
    return display_names.get(state, f"Unknown ({state})")


# Convenience constants for state manager compatibility
# These match the official OrderStatus enum from TopstepX API
STATE_NONE = TopstepXOrderState.NONE.value            # 0
STATE_OPEN = TopstepXOrderState.OPEN.value            # 1
STATE_FILLED = TopstepXOrderState.FILLED.value        # 2
STATE_CANCELLED = TopstepXOrderState.CANCELLED.value  # 3
STATE_EXPIRED = TopstepXOrderState.EXPIRED.value      # 4
STATE_REJECTED = TopstepXOrderState.REJECTED.value    # 5
STATE_PENDING = TopstepXOrderState.PENDING.value      # 6

# Terminal states set (for quick lookups)
# Orders in these states won't change anymore
TERMINAL_STATES = {STATE_FILLED, STATE_CANCELLED, STATE_EXPIRED, STATE_REJECTED}

# Active states set (orders still working)
ACTIVE_STATES = {STATE_OPEN, STATE_PENDING}


# Additional API enum definitions for converters
class APIOrderType(IntEnum):
    """TopstepX API OrderType enum"""
    UNKNOWN = 0
    LIMIT = 1
    MARKET = 2
    STOP_LIMIT = 3
    STOP = 4
    TRAILING_STOP = 5
    JOIN_BID = 6
    JOIN_ASK = 7


class APIOrderSide(IntEnum):
    """TopstepX API OrderSide enum (0=Buy, 1=Sell)"""
    BID = 0  # Buy
    ASK = 1  # Sell


class APIOrderStatus(IntEnum):
    """TopstepX API OrderStatus enum (alternative format from some endpoints)"""
    NONE = 0
    OPEN = 1
    FILLED = 2
    CANCELLED = 3
    EXPIRED = 4
    REJECTED = 5
    PENDING = 6


class APIPositionType(IntEnum):
    """TopstepX API PositionType enum"""
    UNDEFINED = 0
    LONG = 1
    SHORT = 2


# Conversion functions for converters.py
def api_to_internal_order_side(api_side: int) -> str:
    """Convert API order side (0=Bid, 1=Ask) to internal format (buy/sell)"""
    if api_side == APIOrderSide.BID:
        return "buy"
    elif api_side == APIOrderSide.ASK:
        return "sell"
    else:
        raise ValueError(f"Unknown API order side: {api_side}")


def api_to_internal_position_type(api_type: int) -> str:
    """Convert API position type to internal format (long/short)"""
    if api_type == APIPositionType.LONG:
        return "long"
    elif api_type == APIPositionType.SHORT:
        return "short"
    else:
        raise ValueError(f"Unknown API position type: {api_type}")


def internal_to_api_order_side(internal_side: str) -> int:
    """Convert internal order side (buy/sell) to API format"""
    if internal_side.lower() == "buy":
        return APIOrderSide.BID
    elif internal_side.lower() == "sell":
        return APIOrderSide.ASK
    else:
        raise ValueError(f"Unknown internal order side: {internal_side}")


def internal_to_api_order_type(order_type_str: str) -> int:
    """Convert internal order type string to API enum"""
    mapping = {
        "market": APIOrderType.MARKET,
        "limit": APIOrderType.LIMIT,
        "stop": APIOrderType.STOP,
        "stop_limit": APIOrderType.STOP_LIMIT,
        "trailing_stop": APIOrderType.TRAILING_STOP,
    }

    api_type = mapping.get(order_type_str.lower())
    if api_type is None:
        raise ValueError(f"Unknown internal order type: {order_type_str}")

    return api_type
