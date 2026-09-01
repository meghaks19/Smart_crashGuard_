# Kept only as a simple entry point for existing VS Code launch configurations.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from crashguard.__main__ import main
if __name__ == "__main__": main()
