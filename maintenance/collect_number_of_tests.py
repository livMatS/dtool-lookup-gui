import subprocess

def get_number_of_tests():
    try:
        result = subprocess.run(
            ["pytest", "--collect-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("collected"):
                # Extract the number of tests from the line
                return int(line.split()[1])
    except subprocess.CalledProcessError as e:
        print("Error while running pytest:", e.stderr)
        return None

if __name__ == "__main__":
    num_tests = get_number_of_tests()
    if num_tests is not None:
        print(num_tests)
