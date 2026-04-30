"""
run_tests.py — Simple test runner for the ResumeAI test suite.
Usage: python tests/run_tests.py
       (Flask app must be running on localhost:5000 first)
"""
import subprocess
import sys
import os
import re

TESTS_DIR = os.path.dirname(__file__)
TEST_FILES = [
    os.path.join(TESTS_DIR, "test_scoring.py"),
    os.path.join(TESTS_DIR, "test_auth.py"),
    os.path.join(TESTS_DIR, "test_api.py"),
]

HEADER = """
╔══════════════════════════════════════╗
║       ResumeAI Test Suite            ║
╚══════════════════════════════════════╝
"""


def run():
    print(HEADER)
    print("Running: pytest", " ".join(TEST_FILES), "-v\n")

    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + TEST_FILES + ["-v", "--tb=short"],
        capture_output=False,
    )

    print("\n" + "=" * 50)
    if result.returncode == 0:
        print("✅  All tests passed.")
    else:
        print("❌  Some tests failed. See output above for details.")
    print("=" * 50)

    sys.exit(result.returncode)


if __name__ == "__main__":
    run()
