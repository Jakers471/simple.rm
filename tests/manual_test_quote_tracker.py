#!/usr/bin/env python3
"""Manual test for QuoteTracker to verify implementation

Tests all 8 scenarios from test spec without pytest dependency.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.quote_tracker import QuoteTracker


def test_update_quote_store_new():
    """UT-006-01: Store new quote"""
    print("Test 1: Store new quote... ", end="")

    tracker = QuoteTracker()
    assert len(tracker.quotes) == 0, "Initial state should be empty"

    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20949.75,
        ask=20950.25,
        last=20950.00,
        timestamp=datetime(2024, 7, 21, 13, 45, 0, tzinfo=timezone.utc)
    )

    assert "CON.F.US.MNQ.U25" in tracker.quotes, "Quote should be stored"
    stored = tracker.quotes["CON.F.US.MNQ.U25"]
    assert stored['lastPrice'] == 20950.00, f"Expected 20950.00, got {stored['lastPrice']}"
    assert stored['bestBid'] == 20949.75, f"Expected 20949.75, got {stored['bestBid']}"
    assert stored['bestAsk'] == 20950.25, f"Expected 20950.25, got {stored['bestAsk']}"

    print("✓ PASS")


def test_update_quote_update_existing():
    """UT-006-02: Update existing quote"""
    print("Test 2: Update existing quote... ", end="")

    tracker = QuoteTracker()

    # First quote
    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20939.75,
        ask=20940.25,
        last=20940.00,
        timestamp=datetime(2024, 7, 21, 13, 40, 0, tzinfo=timezone.utc)
    )

    # Update quote
    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20949.75,
        ask=20950.25,
        last=20950.00,
        timestamp=datetime(2024, 7, 21, 13, 45, 0, tzinfo=timezone.utc)
    )

    assert len(tracker.quotes) == 1, "Should have only 1 quote (not duplicated)"
    stored = tracker.quotes["CON.F.US.MNQ.U25"]
    assert stored['lastPrice'] == 20950.00, f"Expected updated price 20950.00, got {stored['lastPrice']}"

    print("✓ PASS")


def test_get_last_price_existing():
    """UT-006-03: Get last price for existing contract"""
    print("Test 3: Get last price (existing)... ", end="")

    tracker = QuoteTracker()
    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20949.75,
        ask=20950.25,
        last=20950.00,
        timestamp=datetime.now(timezone.utc)
    )

    price = tracker.get_last_price("CON.F.US.MNQ.U25")
    assert price == 20950.00, f"Expected 20950.00, got {price}"
    assert isinstance(price, float), f"Expected float, got {type(price)}"

    print("✓ PASS")


def test_get_last_price_missing():
    """UT-006-04: Get last price for non-existent contract"""
    print("Test 4: Get last price (missing)... ", end="")

    tracker = QuoteTracker()
    price = tracker.get_last_price("CON.F.US.INVALID.U25")
    assert price is None, f"Expected None, got {price}"

    print("✓ PASS")


def test_get_quote_age():
    """UT-006-05: Get quote age"""
    print("Test 5: Get quote age... ", end="")

    tracker = QuoteTracker()

    # Create quote 5 seconds ago
    now = datetime.now()
    past = now - timedelta(seconds=5)

    tracker.quotes["CON.F.US.MNQ.U25"] = {
        'lastPrice': 20950.00,
        'bestBid': 20949.75,
        'bestAsk': 20950.25,
        'timestamp': past,
        'lastUpdated': past
    }

    age = tracker.get_quote_age("CON.F.US.MNQ.U25")
    assert age is not None, "Age should not be None"
    assert isinstance(age, float), f"Expected float, got {type(age)}"
    assert 4.5 <= age <= 5.5, f"Expected ~5 seconds, got {age}"

    print("✓ PASS")


def test_is_quote_stale_old():
    """UT-006-06: Stale quote detection (old quote)"""
    print("Test 6: Detect stale quote... ", end="")

    tracker = QuoteTracker()

    # Create quote 15 seconds ago
    now = datetime.now()
    past = now - timedelta(seconds=15)

    tracker.quotes["CON.F.US.MNQ.U25"] = {
        'lastPrice': 20950.00,
        'bestBid': 20949.75,
        'bestAsk': 20950.25,
        'timestamp': past,
        'lastUpdated': past
    }

    is_stale = tracker.is_quote_stale("CON.F.US.MNQ.U25", max_age_seconds=10)
    assert is_stale is True, f"Quote 15s old should be stale with 10s threshold"

    print("✓ PASS")


def test_is_quote_stale_fresh():
    """UT-006-07: Fresh quote detection"""
    print("Test 7: Detect fresh quote... ", end="")

    tracker = QuoteTracker()

    # Create quote 3 seconds ago
    now = datetime.now()
    past = now - timedelta(seconds=3)

    tracker.quotes["CON.F.US.MNQ.U25"] = {
        'lastPrice': 20950.00,
        'bestBid': 20949.75,
        'bestAsk': 20950.25,
        'timestamp': past,
        'lastUpdated': past
    }

    is_stale = tracker.is_quote_stale("CON.F.US.MNQ.U25", max_age_seconds=10)
    assert is_stale is False, f"Quote 3s old should be fresh with 10s threshold"

    print("✓ PASS")


def test_is_quote_stale_missing():
    """UT-006-08: Missing quote is stale"""
    print("Test 8: Missing quote is stale... ", end="")

    tracker = QuoteTracker()
    is_stale = tracker.is_quote_stale("CON.F.US.INVALID.U25")
    assert is_stale is True, f"Missing quote should be considered stale"

    print("✓ PASS")


def test_subscribe_to_quotes():
    """Test subscription functionality"""
    print("Test 9: Subscribe to quotes... ", end="")

    tracker = QuoteTracker()
    callback_called = []

    def callback(contract_id, quote_data):
        callback_called.append((contract_id, quote_data['lastPrice']))

    tracker.subscribe_to_quotes(["CON.F.US.MNQ.U25"], callback)

    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20949.75,
        ask=20950.25,
        last=20950.00,
        timestamp=datetime.now(timezone.utc)
    )

    assert len(callback_called) == 1, f"Expected 1 callback, got {len(callback_called)}"
    assert callback_called[0][0] == "CON.F.US.MNQ.U25", "Wrong contract_id"
    assert callback_called[0][1] == 20950.00, "Wrong price"

    print("✓ PASS")


def test_unsubscribe_from_quotes():
    """Test unsubscribe functionality"""
    print("Test 10: Unsubscribe from quotes... ", end="")

    tracker = QuoteTracker()
    callback_called = []

    def callback(contract_id, quote_data):
        callback_called.append(contract_id)

    tracker.subscribe_to_quotes(["CON.F.US.MNQ.U25"], callback)

    # First update - should trigger callback
    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20949.75,
        ask=20950.25,
        last=20950.00,
        timestamp=datetime.now(timezone.utc)
    )

    assert len(callback_called) == 1, "First update should trigger callback"

    # Unsubscribe
    tracker.unsubscribe_from_quotes(["CON.F.US.MNQ.U25"], callback)

    # Second update - should NOT trigger callback
    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20951.75,
        ask=20952.25,
        last=20952.00,
        timestamp=datetime.now(timezone.utc)
    )

    assert len(callback_called) == 1, "After unsubscribe, callback should not be called"

    print("✓ PASS")


def test_get_latest_quote():
    """Test get_latest_quote method"""
    print("Test 11: Get latest quote... ", end="")

    tracker = QuoteTracker()

    tracker.update_quote(
        "CON.F.US.MNQ.U25",
        bid=20949.75,
        ask=20950.25,
        last=20950.00,
        timestamp=datetime(2024, 7, 21, 13, 45, 0, tzinfo=timezone.utc)
    )

    quote = tracker.get_latest_quote("CON.F.US.MNQ.U25")
    assert quote is not None, "Quote should exist"
    assert quote['lastPrice'] == 20950.00, "Wrong last price"
    assert quote['bestBid'] == 20949.75, "Wrong bid"
    assert quote['bestAsk'] == 20950.25, "Wrong ask"
    assert 'timestamp' in quote, "Missing timestamp"
    assert 'lastUpdated' in quote, "Missing lastUpdated"

    # Test missing quote
    missing = tracker.get_latest_quote("CON.F.US.INVALID.U25")
    assert missing is None, "Missing quote should return None"

    print("✓ PASS")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MOD-006: Quote Tracker - Manual Test Suite")
    print("="*60 + "\n")

    tests = [
        test_update_quote_store_new,
        test_update_quote_update_existing,
        test_get_last_price_existing,
        test_get_last_price_missing,
        test_get_quote_age,
        test_is_quote_stale_old,
        test_is_quote_stale_fresh,
        test_is_quote_stale_missing,
        test_subscribe_to_quotes,
        test_unsubscribe_from_quotes,
        test_get_latest_quote,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
