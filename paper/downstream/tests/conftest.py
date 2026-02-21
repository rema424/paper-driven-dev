"""Dynamic implementation loader for downstream outcome tests.

Usage:
    DOWNSTREAM_IMPL_PATH=path/to/impl.py pytest tests/ -v
"""

import importlib.util
import os
import sys

import pytest

# Add parent directories to path for interface imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "interfaces"))


@pytest.fixture
def impl_module():
    """Load the implementation module from DOWNSTREAM_IMPL_PATH."""
    impl_path = os.environ.get("DOWNSTREAM_IMPL_PATH")
    if not impl_path:
        pytest.skip("DOWNSTREAM_IMPL_PATH not set")

    if not os.path.exists(impl_path):
        pytest.fail(f"Implementation file not found: {impl_path}")

    spec = importlib.util.spec_from_file_location("downstream_impl", impl_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
