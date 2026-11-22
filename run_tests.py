import os
import sys
import pytest

if __name__ == "__main__":
    ret = pytest.main(["-p", "no:faulthandler", "-v"])
    # Use os._exit to bypass Python 3.14 pre-release Windows thread-handle teardown issues
    os._exit(int(ret))
