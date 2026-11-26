import subprocess


def staged_diff() -> str:
    result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True, check=True)
    return result.stdout


if __name__ == "__main__":
    print(staged_diff() or "Nothing is staged.")
