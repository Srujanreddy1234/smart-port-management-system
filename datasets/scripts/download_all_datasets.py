#!/usr/bin/env python3
"""
Master script to download ALL datasets for Smart Port Management System.
Downloads 6-7 years of data (2018-present) for V.O. Chidambaranar Port.
"""

import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPTS = [
    ("Weather (2018-present)", "download_weather_data.py"),
    ("Air Quality (2018-present)", "download_air_quality_data.py"),
    ("Marine/Oceanographic (2022-present)", "download_marine_data.py"),
]


def run_script(name, script_file):
    script_path = os.path.join(SCRIPT_DIR, script_file)
    if not os.path.exists(script_path):
        print(f"❌ {name}: Script not found at {script_path}")
        return False

    print(f"\n{'='*60}")
    print(f"📥 Downloading {name}...")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True,
        )
        if result.returncode == 0:
            print(f"✅ {name}: Completed successfully")
            return True
        else:
            print(f"❌ {name}: Failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False


def main():
    print("="*60)
    print("🚀 Smart Port Management System - Dataset Downloader")
    print("   V.O. Chidambaranar Port, Thoothukudi (8.75°N, 78.20°E)")
    print("   Downloading 6-7 years of historical data (2018-present)")
    print("="*60)

    results = []
    for name, script in SCRIPTS:
        success = run_script(name, script)
        results.append((name, success))

    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    all_ok = True
    for name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {status}: {name}")
        if not success:
            all_ok = False

    if all_ok:
        print("\n🎉 All datasets downloaded successfully!")
        print("   Data saved to datasets/raw/")
    else:
        print("\n⚠️  Some downloads failed. Check output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()