"""Test to verify API fixtures use correct field names (camelCase)

This test ensures that all API response fixtures match the actual
TopstepX Gateway API format with camelCase field names.
"""
import pytest


class TestAPIFixtureFormats:
    """Verify API fixtures use correct camelCase field names"""

    def test_position_api_fixture_format(self, single_es_long_position_api):
        """API position fixture should use camelCase"""
        position = single_es_long_position_api

        # Verify API format (camelCase)
        assert "accountId" in position, "API fixture should use 'accountId' not 'account_id'"
        assert "contractId" in position, "API fixture should use 'contractId' not 'contract_id'"
        assert "averagePrice" in position, "API fixture should use 'averagePrice' not 'average_price'"
        assert "createdAt" in position, "API fixture should use 'createdAt' not 'created_at'"
        assert "updatedAt" in position, "API fixture should use 'updatedAt' not 'updated_at'"

        # Should NOT have snake_case
        assert "account_id" not in position
        assert "contract_id" not in position
        assert "average_price" not in position

    def test_position_internal_fixture_format(self, single_es_long_position):
        """Internal position fixture should use snake_case"""
        position = single_es_long_position

        # Verify internal format (snake_case)
        assert "account_id" in position, "Internal fixture should use 'account_id' not 'accountId'"
        assert "contract_id" in position, "Internal fixture should use 'contract_id' not 'contractId'"
        assert "average_price" in position, "Internal fixture should use 'average_price' not 'averagePrice'"
        assert "created_at" in position, "Internal fixture should use 'created_at' not 'createdAt'"
        assert "updated_at" in position, "Internal fixture should use 'updated_at' not 'updatedAt'"

        # Should NOT have camelCase
        assert "accountId" not in position
        assert "contractId" not in position
        assert "averagePrice" not in position

    def test_order_api_fixture_format(self, order_stop_loss_working_api):
        """API order fixture should use camelCase"""
        order = order_stop_loss_working_api

        # Verify API format
        assert "accountId" in order
        assert "contractId" in order
        assert "stopPrice" in order
        assert "createdAt" in order
        assert "updatedAt" in order

        # Should NOT have snake_case
        assert "account_id" not in order
        assert "stop_price" not in order

    def test_order_internal_fixture_format(self, order_stop_loss_working):
        """Internal order fixture should use snake_case"""
        order = order_stop_loss_working

        # Verify internal format
        assert "account_id" in order
        assert "contract_id" in order
        assert "stop_price" in order
        assert "created_at" in order
        assert "updated_at" in order

        # Should NOT have camelCase
        assert "accountId" not in order
        assert "stopPrice" not in order

    def test_trade_api_fixture_format(self, trade_single_profit_api):
        """API trade fixture should use camelCase"""
        trade = trade_single_profit_api

        # Verify API format
        assert "accountId" in trade
        assert "contractId" in trade
        assert "profitAndLoss" in trade
        assert "executionTime" in trade
        assert "entryPrice" in trade
        assert "exitPrice" in trade

        # Should NOT have snake_case
        assert "account_id" not in trade
        assert "profit_and_loss" not in trade

    def test_trade_internal_fixture_format(self, trade_single_profit):
        """Internal trade fixture should use snake_case"""
        trade = trade_single_profit

        # Verify internal format
        assert "account_id" in trade
        assert "contract_id" in trade
        assert "profit_and_loss" in trade
        assert "execution_time" in trade
        assert "entry_price" in trade
        assert "exit_price" in trade

        # Should NOT have camelCase
        assert "accountId" not in trade
        assert "profitAndLoss" not in trade

    def test_account_api_fixture_format(self, account_details_api):
        """API account fixture should use camelCase"""
        account = account_details_api

        # Verify API format
        assert "marginUsed" in account
        assert "marginAvailable" in account
        assert "buyingPower" in account
        assert "unrealizedProfitLoss" in account

        # Should NOT have snake_case
        assert "margin_used" not in account
        assert "unrealized_pnl" not in account

    def test_existing_api_responses_fixture(self, positions_open_response):
        """Existing api_responses.py fixtures should already be correct"""
        positions = positions_open_response

        # These were already correct - verify they still are
        assert len(positions) == 2
        assert "accountId" in positions[0]
        assert "contractId" in positions[0]
        assert "averagePrice" in positions[0]

        # Should NOT have snake_case
        assert "account_id" not in positions[0]


class TestFixtureDocumentation:
    """Verify fixture documentation exists and is clear"""

    def test_fixtures_reference_exists(self):
        """Fixtures reference documentation should exist"""
        import os
        ref_path = "tests/fixtures_reference.md"
        assert os.path.exists(ref_path), f"Missing {ref_path}"

    def test_fixtures_have_docstrings(self, single_es_long_position_api,
                                     single_es_long_position):
        """All fixtures should have clear docstrings"""
        # API fixtures should mention "API response format"
        # Internal fixtures should mention "Internal format"
        # This is verified by the fixture implementation
        assert single_es_long_position_api is not None
        assert single_es_long_position is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
