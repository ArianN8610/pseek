import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from packaging.version import Version

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def notice(msg):
    print(f"::notice::{msg}")


# -------------------------
# Read local version
# -------------------------

print("::group::Read local version")

try:
    with PYPROJECT.open("rb") as f:
        data = tomllib.load(f)

    package_name = data["project"]["name"]
    local_version = data["project"]["version"]
except FileNotFoundError:
    fail("pyproject.toml not found.")
except KeyError:
    fail("Cannot find project.version in pyproject.toml.")
except Exception as e:
    fail(f"Failed to read pyproject.toml: {e}")

print(f"Local version : {local_version}")
print("::endgroup::")

# -------------------------
# Get latest version from PyPI
# -------------------------

print("::group::Read latest PyPI version")

url = f"https://pypi.org/pypi/{package_name}/json"

try:
    with urllib.request.urlopen(url, timeout=20) as response:
        pypi_data = json.load(response)

    latest_version = pypi_data["info"]["version"]

    print(f"PyPI version  : {latest_version}")
except urllib.error.HTTPError as e:
    fail(f"HTTP error while contacting PyPI ({e.code}).")
except urllib.error.URLError as e:
    fail(f"Cannot connect to PyPI ({e.reason}).")
except Exception as e:
    fail(f"Unexpected error while contacting PyPI: {e}")

print("::endgroup::")

# -------------------------
# Compare versions
# -------------------------

print("::group::Compare versions")

publish = Version(local_version) > Version(latest_version)
if publish:
    notice("New version detected.")
else:
    notice("Current version already exists on PyPI.")

print("::endgroup::")

# -------------------------
# Export output
# -------------------------

with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    print(f"publish={'true' if publish else 'false'}", file=f)

print(f"Publish : {publish}")
