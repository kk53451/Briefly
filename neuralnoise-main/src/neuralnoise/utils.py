from importlib.resources import files
from pathlib import Path
from typing import cast

package_root = cast(Path, files("neuralnoise").joinpath(""))
