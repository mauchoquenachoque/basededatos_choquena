import pytest

from app.infrastructure.masking.strategies import SubstitutionStrategy


@pytest.mark.asyncio
async def test_substitution_strategy_is_deterministic():
    strategy = SubstitutionStrategy()
    first = strategy.mask("alice@example.com", provider="email")
    second = strategy.mask("alice@example.com", provider="email")
    assert first == second
    assert "@" in first


@pytest.mark.asyncio
async def test_substitution_strategy_handles_missing_value():
    strategy = SubstitutionStrategy()
    assert strategy.mask(None) is None
