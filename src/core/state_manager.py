"""MOD-009: State Manager - Centralized position and order state tracking."""

from typing import Dict, List, Optional, Any


class StateManager:
    """Centralized position and order state manager with SQLite persistence."""

    def __init__(self, db_connection: Optional[Any] = None):
        self.db = db_connection
        self.positions: Dict[int, Dict[int, Dict[str, Any]]] = {}
        self.orders: Dict[int, Dict[int, Dict[str, Any]]] = {}

    def update_positions(self, account_id: int, positions: List[Dict[str, Any]]) -> None:
        """Update positions for an account (bulk update)."""
        if account_id not in self.positions:
            self.positions[account_id] = {}

        for position in positions:
            position_id = position['id']

            if position['size'] == 0:
                if position_id in self.positions[account_id]:
                    del self.positions[account_id][position_id]
                if self.db:
                    self.db.execute("DELETE FROM positions WHERE id = ?", (position_id,))
            else:
                self.positions[account_id][position_id] = {
                    'id': position_id,
                    'contractId': position['contractId'],
                    'type': position['type'],
                    'size': position['size'],
                    'averagePrice': position['averagePrice'],
                    'creationTimestamp': position['creationTimestamp']
                }
                if self.db:
                    self.db.execute("""
                        INSERT OR REPLACE INTO positions
                        (id, account_id, contract_id, type, size, average_price, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (position_id, account_id, position['contractId'], position['type'],
                          position['size'], position['averagePrice'], position['creationTimestamp']))

    def update_position(self, position_event: Dict[str, Any]) -> None:
        """Update single position from GatewayUserPosition event."""
        self.update_positions(position_event['accountId'], [position_event])

    def get_positions(self, account_id: int) -> List[Dict[str, Any]]:
        """Get all open positions for account."""
        return list(self.positions.get(account_id, {}).values())

    def get_all_positions(self, account_id: int) -> List[Dict[str, Any]]:
        """Alias for get_positions()."""
        return self.get_positions(account_id)

    def get_position_count(self, account_id: int) -> int:
        """Get total contract count across all positions."""
        return sum(p['size'] for p in self.get_positions(account_id))

    def get_positions_by_contract(self, account_id: int, contract_id: str) -> List[Dict[str, Any]]:
        """Get positions for specific contract."""
        return [p for p in self.get_positions(account_id) if p['contractId'] == contract_id]

    def get_contract_count(self, account_id: int, contract_id: str) -> int:
        """Get contract count for specific instrument."""
        return sum(p['size'] for p in self.get_positions_by_contract(account_id, contract_id))

    def update_orders(self, account_id: int, orders: List[Dict[str, Any]]) -> None:
        """Update orders for an account (bulk update)."""
        if account_id not in self.orders:
            self.orders[account_id] = {}

        for order in orders:
            order_id = order['id']

            # OrderStatus enum: 0=None, 1=Open, 2=Filled, 3=Cancelled, 4=Expired, 5=Rejected, 6=Pending
            # Terminal states (order won't change): Filled, Cancelled, Expired, Rejected
            # Source: projectx_gateway_api/realtime_updates/realtime_data_overview.md
            if order.get('status') in [2, 3, 4, 5]:  # FILLED, CANCELLED, EXPIRED, REJECTED
                if order_id in self.orders[account_id]:
                    del self.orders[account_id][order_id]
                if self.db:
                    self.db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            else:
                self.orders[account_id][order_id] = {
                    'id': order_id,
                    'accountId': account_id,
                    'contractId': order['contractId'],
                    'type': order['type'],
                    'side': order['side'],
                    'size': order['size'],
                    'limitPrice': order.get('limitPrice'),
                    'stopPrice': order.get('stopPrice'),
                    'status': order.get('status', 6),  # Default to PENDING if not specified
                    'creationTimestamp': order['creationTimestamp']
                }
                if self.db:
                    self.db.execute("""
                        INSERT OR REPLACE INTO orders
                        (id, account_id, contract_id, type, side, size, limit_price, stop_price, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, account_id, order['contractId'], order['type'], order['side'],
                          order['size'], order.get('limitPrice'), order.get('stopPrice'),
                          order.get('status', 6), order['creationTimestamp']))

    def update_order(self, order_event: Dict[str, Any]) -> None:
        """Update single order from GatewayUserOrder event."""
        self.update_orders(order_event['accountId'], [order_event])

    def get_orders(self, account_id: int) -> List[Dict[str, Any]]:
        """Get all working orders for account."""
        return list(self.orders.get(account_id, {}).values())

    def get_all_orders(self, account_id: int) -> List[Dict[str, Any]]:
        """Alias for get_orders()."""
        return self.get_orders(account_id)

    def get_orders_for_position(self, account_id: int, contract_id: str) -> List[Dict[str, Any]]:
        """Get orders for specific position/contract."""
        return [o for o in self.get_orders(account_id) if o['contractId'] == contract_id]

    def save_state_snapshot(self) -> None:
        """Persist current state to database."""
        if not self.db:
            return

        self.db.execute("DELETE FROM positions")
        self.db.execute("DELETE FROM orders")

        for account_id, account_positions in self.positions.items():
            for position in account_positions.values():
                self.db.execute("""
                    INSERT INTO positions
                    (id, account_id, contract_id, type, size, average_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (position['id'], account_id, position['contractId'], position['type'],
                      position['size'], position['averagePrice'], position['creationTimestamp']))

        for account_id, account_orders in self.orders.items():
            for order in account_orders.values():
                self.db.execute("""
                    INSERT INTO orders
                    (id, account_id, contract_id, type, side, size, limit_price, stop_price, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (order['id'], account_id, order['contractId'], order['type'], order['side'],
                      order['size'], order.get('limitPrice'), order.get('stopPrice'),
                      order['status'], order['creationTimestamp']))

        if hasattr(self.db, 'commit'):
            self.db.commit()

    def load_state_snapshot(self) -> None:
        """Restore state from database."""
        if not self.db:
            return

        cursor = self.db.execute("""
            SELECT id, account_id, contract_id, type, size, average_price, created_at
            FROM positions
        """)

        for row in cursor.fetchall():
            position_id, account_id, contract_id, type_, size, avg_price, created_at = row
            if account_id not in self.positions:
                self.positions[account_id] = {}
            self.positions[account_id][position_id] = {
                'id': position_id,
                'contractId': contract_id,
                'type': type_,
                'size': size,
                'averagePrice': avg_price,
                'creationTimestamp': created_at
            }

        cursor = self.db.execute("""
            SELECT id, account_id, contract_id, type, side, size, limit_price, stop_price, status, created_at
            FROM orders
        """)

        for row in cursor.fetchall():
            order_id, account_id, contract_id, type_, side, size, limit_price, stop_price, status, created_at = row
            if account_id not in self.orders:
                self.orders[account_id] = {}
            self.orders[account_id][order_id] = {
                'id': order_id,
                'accountId': account_id,
                'contractId': contract_id,
                'type': type_,
                'side': side,
                'size': size,
                'limitPrice': limit_price,
                'stopPrice': stop_price,
                'status': status,
                'creationTimestamp': created_at
            }

    def load_from_database(self) -> None:
        """Alias for load_state_snapshot()."""
        self.load_state_snapshot()

    def clear_state(self, account_id: int) -> None:
        """Clear all state for an account."""
        if account_id in self.positions:
            del self.positions[account_id]
        if account_id in self.orders:
            del self.orders[account_id]
        if self.db:
            self.db.execute("DELETE FROM positions WHERE account_id = ?", (account_id,))
            self.db.execute("DELETE FROM orders WHERE account_id = ?", (account_id,))
            if hasattr(self.db, 'commit'):
                self.db.commit()
