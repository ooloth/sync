"""Central place for test composition. No adapters imported anywhere else."""

import pytest
from shell.composition.test import (
    create_e2e_context,
    create_integration_context,
    create_unit_context,
)


@pytest.fixture
def unit_ctx():
    """
    Fast, deterministic context.
    No IO. Default for most tests.
    """
    return create_unit_context()


@pytest.fixture
def integration_ctx():
    """
    Real adapters, ephemeral resources.
    Slower; use explicitly.
    """
    return create_integration_context()


@pytest.fixture
def e2e_ctx():
    """
    Real infrastructure.
    Very slow; opt-in only.
    """
    return create_e2e_context()


def pytest_runtest_setup(item):
    """
    Forbid accidental use of wrong context fixture by ensuring tests marked as "integration" or "e2e" actually use
    the right fixture.

    Benefits:
        - You cannot mark a test integration without using the right context
        - You cannot accidentally hit real infra from a unit test
    """
    if "integration" in item.keywords and "integration_ctx" not in item.fixturenames:
        raise RuntimeError("integration test must use integration_ctx")

    if "e2e" in item.keywords and "e2e_ctx" not in item.fixturenames:
        raise RuntimeError("e2e test must use e2e_ctx")
