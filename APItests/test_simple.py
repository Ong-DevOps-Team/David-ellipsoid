"""
Simple test to verify the test setup works
"""
import pytest

def test_simple():
    """Simple test that should always pass."""
    assert True

def test_math():
    """Test basic math operations."""
    assert 2 + 2 == 4
    assert 3 * 5 == 15
    assert 10 - 3 == 7

class TestSimpleClass:
    """Simple test class."""
    
    def test_class_method(self):
        """Test method within a class."""
        assert "hello" in "hello world"
    
    def test_list_operations(self):
        """Test list operations."""
        test_list = [1, 2, 3]
        assert len(test_list) == 3
        assert 2 in test_list
        test_list.append(4)
        assert len(test_list) == 4
