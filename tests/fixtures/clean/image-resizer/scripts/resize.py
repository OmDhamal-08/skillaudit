import sys
from pathlib import Path

from PIL import Image


def resize(path: Path, max_width: int) -> Path:
    with Image.open(path) as img:
        if img.width > max_width:
            height = round(img.height * max_width / img.width)
            img = img.resize((max_width, height))
        out = path.with_name(f"{path.stem}-{max_width}{path.suffix}")
        img.save(out)
    return out


if __name__ == "__main__":
    print(resize(Path(sys.argv[1]), int(sys.argv[2])))
