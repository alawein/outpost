"""Put the repo root on sys.path so the tests can import the top-level `install` and `validate`
modules and the `kit` package without an editable install."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
