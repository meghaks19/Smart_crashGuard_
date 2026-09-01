from __future__ import annotations
import argparse
from .app import CrashGuardApp
from .config import load_settings

def main():
    parser = argparse.ArgumentParser(description="Smart CrashGuard live dashcam monitor")
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()
    CrashGuardApp(load_settings(args.config)).run()
if __name__ == "__main__": main()
