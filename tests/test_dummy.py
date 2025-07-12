import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
from atlas_object_partitioning.core import dummy_function


def test_dummy_function():
    """Dummy test for dummy_function."""
    assert dummy_function() is True
