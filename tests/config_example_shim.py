"""Synthetic config for tests: config.example.py with the period narrowed to the
Feb-2026 fixtures. Tests inject this as analyze.C. Never touches a real config.py."""
import importlib.util, pathlib, sys
from datetime import date
_p = pathlib.Path(__file__).resolve().parents[1] / "config.example.py"
_spec = importlib.util.spec_from_file_location("config_example", _p)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["config_example"] = _mod
_spec.loader.exec_module(_mod)
globals().update({k: getattr(_mod, k) for k in dir(_mod) if not k.startswith("__")})
PERIOD_START = date(2026, 2, 1)
PERIOD_END = date(2026, 2, 28)
