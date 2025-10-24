"""
API Data Converters

Converts TopstepX API responses (camelCase) to internal backend format (snake_case).
This is the SINGLE SOURCE OF TRUTH for field mapping.

References:
- TopstepX Gateway API documentation
- project-specs/SPECS/01-API-INTEGRATION/topstepx_integration.md
- reports/2025-10-22-spec-governance/02-analysis/API_ALIGNMENT_REPORT.md

API Response Format (camelCase):
    - accountId, contractId, orderId
    - creationTimestamp, updateTimestamp
    - stopPrice, limitPrice, trailPrice
    - fillVolume, filledPrice
    - averagePrice, unrealizedProfitLoss, realizedProfitLoss

Internal Format (snake_case):
    - account_id, contract_id, order_id
    - creation_timestamp, update_timestamp
    - stop_price, limit_price, trail_price
    - filled_quantity, filled_price
    - average_price, unrealized_pnl, realized_pnl
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from .enums import (
    api_to_internal_order_state,
    api_to_internal_order_side,
    api_to_internal_position_type,
    internal_to_api_order_side,
    internal_to_api_order_type,
    APIOrderStatus,
    InternalOrderState,
)


def _parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    """
    Parse TopstepX timestamp format to datetime.

    API sends timestamps in ISO 8601 format with timezone:
    - "2025-07-18T21:00:01.268009+00:00"
    - "2025-01-20T15:47:39.882Z"
    """
    if not ts:
        return None

    try:
        # Handle 'Z' suffix (Zulu time)
        if ts.endswith('Z'):
            ts = ts.replace('Z', '+00:00')

        # Parse ISO 8601 format
        return datetime.fromisoformat(ts)
    except (ValueError, AttributeError):
        # Return None if parsing fails rather than raising
        return None


def api_to_internal_account(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API account to internal format.

    API Fields (GatewayUserAccount):
        - id: int
        - name: string
        - balance: float
        - canTrade: boolean
        - isVisible: boolean
        - simulated: boolean (optional)

    Internal Fields:
        - account_id: int
        - name: str
        - balance: float
        - can_trade: bool
        - is_visible: bool
        - simulated: bool
    """
    return {
        "account_id": api_data.get("id"),
        "name": api_data.get("name"),
        "balance": api_data.get("balance", 0.0),
        "can_trade": api_data.get("canTrade", False),
        "is_visible": api_data.get("isVisible", True),
        "simulated": api_data.get("simulated", False),
    }


def api_to_internal_order(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API order to internal format.

    API Fields (GatewayUserOrder / Order search response):
        - id: int (orderId)
        - accountId: int
        - contractId: string
        - symbolId: string
        - creationTimestamp: string (ISO 8601)
        - updateTimestamp: string (ISO 8601)
        - status: int (OrderStatus enum)
        - type: int (OrderType enum)
        - side: int (OrderSide enum: 0=Buy, 1=Sell)
        - size: int
        - limitPrice: float | null
        - stopPrice: float | null
        - fillVolume: int
        - filledPrice: float | null
        - customTag: string | null

    Internal Fields:
        - order_id: int
        - account_id: int
        - contract_id: str
        - symbol_id: str
        - creation_timestamp: datetime
        - update_timestamp: datetime
        - state: InternalOrderState (enum value)
        - order_type: int
        - side: str (buy/sell)
        - quantity: int
        - limit_price: float | None
        - stop_price: float | None
        - filled_quantity: int
        - filled_price: float | None
        - custom_tag: str | None
    """
    # Handle both 'status' (OrderStatus enum 0-6) and 'state' (TopstepX state 1-5)
    # API may send either depending on endpoint
    api_status = api_data.get("status")
    api_state = api_data.get("state")

    if api_status is not None and api_status in [
        APIOrderStatus.NONE,
        APIOrderStatus.OPEN,
        APIOrderStatus.FILLED,
        APIOrderStatus.CANCELLED,
        APIOrderStatus.EXPIRED,
        APIOrderStatus.REJECTED,
        APIOrderStatus.PENDING,
    ]:
        # Map APIOrderStatus to InternalOrderState
        status_to_state_mapping = {
            APIOrderStatus.NONE: InternalOrderState.PENDING,
            APIOrderStatus.OPEN: InternalOrderState.ACTIVE,
            APIOrderStatus.FILLED: InternalOrderState.FILLED,
            APIOrderStatus.CANCELLED: InternalOrderState.CANCELLED,
            APIOrderStatus.EXPIRED: InternalOrderState.EXPIRED,
            APIOrderStatus.REJECTED: InternalOrderState.REJECTED,
            APIOrderStatus.PENDING: InternalOrderState.PENDING,
        }
        internal_state = status_to_state_mapping.get(
            api_status, InternalOrderState.PENDING
        )
    elif api_state is not None:
        # Use TopstepX state (1-5) conversion
        internal_state = api_to_internal_order_state(api_state)
    else:
        # Default to PENDING
        internal_state = InternalOrderState.PENDING

    return {
        "order_id": api_data.get("id") or api_data.get("orderId"),
        "account_id": api_data.get("accountId"),
        "contract_id": api_data.get("contractId"),
        "symbol_id": api_data.get("symbolId"),
        "creation_timestamp": _parse_timestamp(api_data.get("creationTimestamp")),
        "update_timestamp": _parse_timestamp(api_data.get("updateTimestamp")),
        "state": internal_state,
        "order_type": api_data.get("type", 0),
        "side": api_to_internal_order_side(api_data.get("side", 0)),
        "quantity": api_data.get("size", 0),
        "limit_price": api_data.get("limitPrice"),
        "stop_price": api_data.get("stopPrice"),
        "filled_quantity": api_data.get("fillVolume", 0),
        "filled_price": api_data.get("filledPrice"),
        "custom_tag": api_data.get("customTag"),
    }


def api_to_internal_position(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API position to internal format.

    API Fields (GatewayUserPosition / Position search response):
        - id: int (optional, position ID)
        - accountId: int
        - contractId: string
        - creationTimestamp: string (ISO 8601)
        - type: int (PositionType enum: 1=Long, 2=Short)
        - size: int (API uses "size", not "quantity")
        - averagePrice: float
        - side: int (optional, from old API versions)
        - quantity: int (optional, from old API versions)
        - avgPrice: float (optional, from old API versions)
        - unrealizedPnl: float (optional, from old API versions)

    Internal Fields:
        - position_id: int | None
        - account_id: int
        - contract_id: str
        - creation_timestamp: datetime | None
        - position_type: str (long/short)
        - quantity: int
        - average_price: float
        - unrealized_pnl: float
    """
    # Handle both new API (type/size) and old API (side/quantity)
    api_type = api_data.get("type")
    api_side = api_data.get("side")

    if api_type is not None:
        position_type = api_to_internal_position_type(api_type)
    elif api_side is not None:
        # Old API: side 0=Buy=Long, 1=Sell=Short
        position_type = "long" if api_side == 0 else "short"
    else:
        position_type = None

    return {
        "position_id": api_data.get("id"),
        "account_id": api_data.get("accountId"),
        "contract_id": api_data.get("contractId"),
        "creation_timestamp": _parse_timestamp(api_data.get("creationTimestamp")),
        "position_type": position_type,
        "quantity": api_data.get("size") or api_data.get("quantity", 0),
        "average_price": api_data.get("averagePrice") or api_data.get("avgPrice", 0.0),
        "unrealized_pnl": api_data.get("unrealizedPnl", 0.0),
    }


def api_to_internal_trade(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API trade to internal format.

    API Fields (GatewayUserTrade / Trade search response):
        - id: int (trade ID)
        - accountId: int
        - contractId: string
        - creationTimestamp: string (ISO 8601)
        - price: float
        - profitAndLoss: float | null (null for half-turn trades)
        - fees: float
        - side: int (OrderSide enum: 0=Buy, 1=Sell)
        - size: int
        - voided: boolean
        - orderId: int

    Internal Fields:
        - trade_id: int
        - order_id: int
        - account_id: int
        - contract_id: str
        - quantity: int
        - price: float
        - execution_time: datetime
        - side: str (buy/sell)
        - fees: float
        - profit_and_loss: float | None
        - voided: bool
    """
    return {
        "trade_id": api_data.get("id"),
        "order_id": api_data.get("orderId"),
        "account_id": api_data.get("accountId"),
        "contract_id": api_data.get("contractId"),
        "quantity": api_data.get("size", 0),
        "price": api_data.get("price", 0.0),
        "execution_time": _parse_timestamp(api_data.get("creationTimestamp")),
        "side": api_to_internal_order_side(api_data.get("side", 0)),
        "fees": api_data.get("fees", 0.0),
        "profit_and_loss": api_data.get("profitAndLoss"),  # null for half-turns
        "voided": api_data.get("voided", False),
    }


def api_to_internal_contract(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API contract to internal format.

    API Fields (Contract search response):
        - id: string (contract ID like "CON.F.US.ENQ.H25")
        - name: string
        - description: string
        - tickSize: float
        - tickValue: float
        - activeContract: boolean
        - symbolId: string
        - exchange: string (optional)
        - contractSize: int (optional)
        - symbol: string (from old API versions)

    Internal Fields:
        - contract_id: str
        - name: str
        - symbol: str
        - description: str
        - exchange: str
        - tick_size: float
        - tick_value: float
        - contract_size: int
        - active_contract: bool
    """
    return {
        "contract_id": api_data.get("id"),
        "name": api_data.get("name", ""),
        "symbol": api_data.get("symbolId") or api_data.get("symbol", ""),
        "description": api_data.get("description", ""),
        "exchange": api_data.get("exchange", ""),
        "tick_size": api_data.get("tickSize", 0.0),
        "tick_value": api_data.get("tickValue", 0.0),
        "contract_size": api_data.get("contractSize", 1),
        "active_contract": api_data.get("activeContract", True),
    }


def api_to_internal_quote(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API quote to internal format.

    API Fields (GatewayQuote):
        - symbol: string
        - symbolName: string
        - lastPrice: float
        - bestBid: float
        - bestAsk: float
        - change: float
        - changePercent: float
        - open: float
        - high: float
        - low: float
        - volume: int
        - lastUpdated: string (ISO 8601)
        - timestamp: string (ISO 8601)

    Internal Fields:
        - symbol: str
        - symbol_name: str
        - last_price: float
        - best_bid: float
        - best_ask: float
        - change: float
        - change_percent: float
        - open: float
        - high: float
        - low: float
        - volume: int
        - last_updated: datetime
        - timestamp: datetime
    """
    return {
        "symbol": api_data.get("symbol"),
        "symbol_name": api_data.get("symbolName"),
        "last_price": api_data.get("lastPrice", 0.0),
        "best_bid": api_data.get("bestBid", 0.0),
        "best_ask": api_data.get("bestAsk", 0.0),
        "change": api_data.get("change", 0.0),
        "change_percent": api_data.get("changePercent", 0.0),
        "open": api_data.get("open", 0.0),
        "high": api_data.get("high", 0.0),
        "low": api_data.get("low", 0.0),
        "volume": api_data.get("volume", 0),
        "last_updated": _parse_timestamp(api_data.get("lastUpdated")),
        "timestamp": _parse_timestamp(api_data.get("timestamp")),
    }


# Reverse converters (for sending data TO API)

def internal_to_api_order_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal order format to TopstepX API request format.

    Internal Fields:
        - account_id: int
        - contract_id: str
        - order_type: str (market/limit/stop/stop_limit/trailing_stop)
        - side: str (buy/sell)
        - quantity: int
        - limit_price: float | None
        - stop_price: float | None
        - trail_price: float | None
        - custom_tag: str | None

    API Request Fields:
        - accountId: int
        - contractId: string
        - type: int (OrderType enum)
        - side: int (OrderSide enum)
        - size: int
        - limitPrice: float | null
        - stopPrice: float | null
        - trailPrice: float | null
        - customTag: string | null
        - stopLossBracket: object | null (optional)
        - takeProfitBracket: object | null (optional)
    """
    return {
        "accountId": internal_data.get("account_id"),
        "contractId": internal_data.get("contract_id"),
        "type": internal_to_api_order_type(internal_data.get("order_type", "market")),
        "side": internal_to_api_order_side(internal_data.get("side", "buy")),
        "size": internal_data.get("quantity", 0),
        "limitPrice": internal_data.get("limit_price"),
        "stopPrice": internal_data.get("stop_price"),
        "trailPrice": internal_data.get("trail_price"),
        "customTag": internal_data.get("custom_tag"),
        "stopLossBracket": internal_data.get("stop_loss_bracket"),
        "takeProfitBracket": internal_data.get("take_profit_bracket"),
    }


def internal_to_api_order_modify_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal order modify format to TopstepX API request format.

    Internal Fields:
        - account_id: int
        - order_id: int
        - quantity: int | None
        - limit_price: float | None
        - stop_price: float | None
        - trail_price: float | None

    API Request Fields:
        - accountId: int
        - orderId: int
        - size: int | null
        - limitPrice: float | null
        - stopPrice: float | null
        - trailPrice: float | null
    """
    return {
        "accountId": internal_data.get("account_id"),
        "orderId": internal_data.get("order_id"),
        "size": internal_data.get("quantity"),
        "limitPrice": internal_data.get("limit_price"),
        "stopPrice": internal_data.get("stop_price"),
        "trailPrice": internal_data.get("trail_price"),
    }


def internal_to_api_order_cancel_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal order cancel format to TopstepX API request format.

    Internal Fields:
        - account_id: int
        - order_id: int

    API Request Fields:
        - accountId: int
        - orderId: int
    """
    return {
        "accountId": internal_data.get("account_id"),
        "orderId": internal_data.get("order_id"),
    }


def internal_to_api_position_close_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal position close format to TopstepX API request format.

    Internal Fields:
        - account_id: int
        - contract_id: str

    API Request Fields:
        - accountId: int
        - contractId: string
    """
    return {
        "accountId": internal_data.get("account_id"),
        "contractId": internal_data.get("contract_id"),
    }
