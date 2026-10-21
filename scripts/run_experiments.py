#!/usr/bin/env python3
"""
Run complete experimental suite: build, baseline, results, verification, analysis.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description="", timeout=600):
    """Run a command and return success status"""
    print(f"[*] {description}")
    print(f"    Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print("    ✓ Success")
            return True, result.stdout, result.stderr
        else:
            print(f"    ✗ Failed (exit code {result.returncode})")
            print(f"    Error: {result.stderr}")
            return False, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print("    ✗ Timeout")
        return False, "", "Timeout"
    except Exception as e:
        print(f"    ✗ Exception: {e}")
        return False, "", str(e)

def run_experiments():
    """Run complete experimental suite"""

    print("="*80)
    print("AHO-CORASICK PARALLEL IMPLEMENTATION - EXPERIMENTAL SUITE")
    print("="*80)

    # Change to project root
    os.chdir("/home/ismail/PDC_Project")

    steps = [
        ("Building all implementations", ["make", "all"]),
        ("Generating baseline results", ["python3", "src/scripts/generate_baseline.py"]),
        ("Running all implementations", ["python3", "src/scripts/generate_all_results.py"]),
        ("Verifying correctness", ["python3", "src/scripts/verify_correctness.py"]),
        ("Running performance analysis", ["python3", "src/scripts/performance_analyzer.py"]),
        ("Running comprehensive analysis", ["python3", "src/scripts/comprehensive_analysis.py"])
    ]

    success_count = 0

    for description, cmd in steps:
        print(f"\n--- {description} ---")
        success, stdout, stderr = run_command(cmd, description)

        if success:
            success_count += 1
        else:
            print(f"Step failed: {description}")
            break

    print("\n" + "="*80)
    print("EXPERIMENTAL SUITE SUMMARY")
    print("="*80)
    print(f"Completed steps: {success_count}/{len(steps)}")

    if success_count == len(steps):
        print("🎉 ALL EXPERIMENTS COMPLETED SUCCESSFULLY!")
        print("Check FINAL_COMPREHENSIVE_REPORT.md for results")
        return True
    else:
        print("❌ SOME EXPERIMENTS FAILED")
        return False

def main():
    success = run_experiments()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())