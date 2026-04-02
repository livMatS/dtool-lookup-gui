import subprocess
import sys


def get_number_of_tests():
    try:
        result = subprocess.run(
            [
                "pytest",
                "--collect-only",
                "-q",
                "--no-header",
                "-p", "no:cacheprovider",
                "--override-ini=addopts=",  # suppress --cov from pyproject.toml addopts
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("collected"):
                # Extract the number of tests from the line
                return int(line.split()[1])
        # Fallback: count "::test_" lines in quiet output
        count = sum(1 for line in result.stdout.splitlines() if "::" in line and not line.startswith("ERROR"))
        return count if count > 0 else None
    except subprocess.CalledProcessError as e:
        print("Error while running pytest --collect-only:", e.stderr, file=sys.stderr)
        return None


if __name__ == "__main__":
    num_tests = get_number_of_tests()
    if num_tests is not None:
        print(num_tests)
    else:
        # Safe fallback: let pytest decide parallelism with 'auto'
        print("auto")
