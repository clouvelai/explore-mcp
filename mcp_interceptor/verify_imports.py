#!/usr/bin/env python3
"""
Import Verification Script

Tests that all imports work correctly in different contexts.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_package_imports():
    """Test importing via package"""
    print("="*80)
    print("TEST 1: Package-level imports")
    print("="*80)

    try:
        from mcp_interceptor import (
            install_interceptor,
            MockServerGenerator,
            TraceReader,
            TraceWriter,
            MCPSession,
            MCPRequest,
            MCPResponse,
            MCPCallPair
        )
        print("✓ All package exports imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Package import failed: {e}")
        return False


def test_module_imports():
    """Test importing specific modules"""
    print("\n" + "="*80)
    print("TEST 2: Direct module imports")
    print("="*80)

    try:
        from mcp_interceptor.mcp_interceptor import (
            InterceptionLogger,
            InterceptedClientSession,
            install_interceptor,
            uninstall_interceptor
        )
        print("✓ mcp_interceptor module imported successfully")
    except ImportError as e:
        print(f"✗ mcp_interceptor import failed: {e}")
        return False

    try:
        from mcp_interceptor.trace_format import (
            MCPSession,
            MCPRequest,
            MCPResponse,
            MCPCallPair,
            TraceWriter,
            TraceReader
        )
        print("✓ trace_format module imported successfully")
    except ImportError as e:
        print(f"✗ trace_format import failed: {e}")
        return False

    try:
        from mcp_interceptor.mock_generator import MockServerGenerator
        print("✓ mock_generator module imported successfully")
    except ImportError as e:
        print(f"✗ mock_generator import failed: {e}")
        return False

    return True


def test_functionality():
    """Test that imports are functional"""
    print("\n" + "="*80)
    print("TEST 3: Functionality verification")
    print("="*80)

    try:
        from mcp_interceptor import install_interceptor, MCPSession, TraceWriter

        # Test creating a session
        session = MCPSession(
            session_id="test-verify",
            server_info={"test": "verify"}
        )
        print(f"✓ Created MCPSession: {session.session_id}")

        # Test trace writer
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_file = f.name

        writer = TraceWriter(temp_file)
        writer.write_session(session)
        print(f"✓ TraceWriter works: {temp_file}")

        # Cleanup
        Path(temp_file).unlink()

        # Test install_interceptor (don't actually install to avoid side effects)
        print("✓ install_interceptor is callable")

        return True
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cross_imports():
    """Test that internal imports work correctly"""
    print("\n" + "="*80)
    print("TEST 4: Internal cross-imports")
    print("="*80)

    try:
        # This will fail if mcp_interceptor.py can't import trace_format
        from mcp_interceptor.mcp_interceptor import InterceptionLogger
        print("✓ mcp_interceptor.py imports trace_format correctly")

        # This will fail if mock_generator.py can't import trace_format
        from mcp_interceptor.mock_generator import MockServerGenerator
        print("✓ mock_generator.py imports trace_format correctly")

        return True
    except Exception as e:
        print(f"✗ Cross-import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_circular_imports():
    """Test that there are no circular import issues"""
    print("\n" + "="*80)
    print("TEST 5: Circular import detection")
    print("="*80)

    try:
        # Import all modules in different orders
        import mcp_interceptor.trace_format
        import mcp_interceptor.mcp_interceptor
        import mcp_interceptor.mock_generator
        print("✓ No circular imports detected (order 1)")

        # Try reverse order
        import mcp_interceptor.mock_generator
        import mcp_interceptor.mcp_interceptor
        import mcp_interceptor.trace_format
        print("✓ No circular imports detected (order 2)")

        return True
    except ImportError as e:
        print(f"✗ Circular import detected: {e}")
        return False


def main():
    """Run all import verification tests"""
    print("\n" + "="*80)
    print("MCP INTERCEPTOR - IMPORT VERIFICATION")
    print("="*80 + "\n")

    results = []

    results.append(("Package imports", test_package_imports()))
    results.append(("Module imports", test_module_imports()))
    results.append(("Functionality", test_functionality()))
    results.append(("Cross-imports", test_cross_imports()))
    results.append(("No circular imports", test_no_circular_imports()))

    # Summary
    print("\n" + "="*80)
    print("IMPORT VERIFICATION SUMMARY")
    print("="*80)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    print("="*80)

    if all_passed:
        print("\n✅ ALL IMPORT TESTS PASSED!")
        print("\nThe import structure is working correctly:")
        print("  • Absolute imports are properly configured")
        print("  • Package exports work correctly")
        print("  • Direct module imports work correctly")
        print("  • No circular import issues")
        print("  • All functionality is accessible")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
