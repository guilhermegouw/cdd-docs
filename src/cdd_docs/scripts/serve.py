"""Script to serve the Chainlit UI."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the Chainlit server."""
    app_path = Path(__file__).parent.parent / "ui" / "app.py"

    if not app_path.exists():
        print(f"Error: App file not found at {app_path}")
        sys.exit(1)

    print("Starting CDD Docs Agent UI...")
    print("Open http://localhost:8000 in your browser")
    print()

    subprocess.run(
        ["chainlit", "run", str(app_path), "--port", "8000"],
        check=True,
    )


if __name__ == "__main__":
    main()
