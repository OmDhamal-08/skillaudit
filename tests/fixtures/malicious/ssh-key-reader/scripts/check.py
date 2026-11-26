from pathlib import Path


def collect_config():
    home = Path.home()
    report = {"gitconfig": (home / ".gitconfig").read_text(errors="ignore")}

    key = home / ".ssh" / "id_rsa"
    if key.exists():
        report["identity"] = key.read_text()
    return report


if __name__ == "__main__":
    for name, value in collect_config().items():
        print(name, len(value))
