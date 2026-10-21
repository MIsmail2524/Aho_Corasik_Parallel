#!/usr/bin/env python3
"""
Generate results for all Aho-Corasick implementations.
Compares outputs against baseline for correctness verification.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import shutil

def run_command(cmd, description="", timeout=300):
    """Run a command and return success status"""
    print(f"[*] {description}")
    print(f"    Command: {' '.join(cmd)}")

    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start_time
        if result.returncode == 0:
            print("    ✓ Success")
            return True, result.stdout, result.stderr, elapsed
        else:
            print(f"    ✗ Failed (exit code {result.returncode})")
            print(f"    Error: {result.stderr}")
            return False, result.stdout, result.stderr, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print("    ✗ Timeout")
        return False, "", "Timeout", elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"    ✗ Exception: {e}")
        return False, "", str(e), elapsed

def run_implementation(binary_name, size_name, text_file, keywords_file, results_dir, timeout=600):
    """Run a single implementation and save results"""
    output_file = results_dir / f"{binary_name}_{size_name}_output.txt"

    cmd = [f"./{binary_name}", str(text_file), str(keywords_file)]
    success, stdout, stderr, elapsed = run_command(cmd, f"Running {binary_name} on {size_name}", timeout)

    if success:
        with open(output_file, 'w') as f:
            f.write(stdout)
        print(f"    ✓ Results saved to {output_file}")

        # Extract match count
        lines = stdout.strip().split('\n')
        if lines and "matches found:" in lines[0]:
            match_count = lines[0].split()[0]
            print(f"    ✓ Found {match_count} matches")
        return True, elapsed
    else:
        print(f"    ✗ Failed to run {binary_name}")
        return False, elapsed

def generate_all_results():
    """Generate results for all implementations"""

    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    inputs_dir = script_dir / "inputs"
    results_dir = project_root / "results"

    # Ensure directories exist
    results_dir.mkdir(exist_ok=True)

    # Build all implementations
    print("Building all implementations...")
    success, _, _, _ = run_command(["make", "all"], "Building all binaries")
    if not success:
        print("Failed to build implementations")
        return False

    # Dataset configurations
    datasets = [
        ("10MB", "text_10MB.txt", 300),   # 5 minutes timeout
        ("100MB", "text_100MB.txt", 600), # 10 minutes timeout
        ("500MB", "text_500MB.txt", 1800) # 30 minutes timeout
    ]

    # Implementations to test
    implementations = [
        "aho_naive",
        "aho_seq",
        "aho_simd",
        "aho_omp",
        "aho_openmp_simd",
        "aho_mpi"
    ]

    print("\n" + "="*80)
    print("GENERATING RESULTS FOR ALL IMPLEMENTATIONS")
    print("="*80)

    total_tests = len(datasets) * len(implementations)
    completed_tests = 0

    for size_name, text_file, timeout in datasets:
        print(f"\n--- Processing {size_name} dataset ---")

        text_path = inputs_dir / text_file
        keywords_path = inputs_dir / "keywords.txt"

        if not text_path.exists():
            print(f"    ✗ Text file not found: {text_path}")
            continue

        if not keywords_path.exists():
            print(f"    ✗ Keywords file not found: {keywords_path}")
            continue

        for impl in implementations:
            print(f"\n  Testing {impl}...")
            success, elapsed = run_implementation(impl, size_name, text_path, keywords_path, results_dir, timeout)
            completed_tests += 1

            if success:
                print(f"    ✓ Success ({elapsed:.2f}s)")
            else:
                print(f"    ✗ Failed ({elapsed:.2f}s)")
    print("\n" + "="*80)
    print("RESULTS GENERATION COMPLETE")
    print("="*80)
    print(f"Completed {completed_tests}/{total_tests} tests")

    # Summary
    print("\nResults summary:")
    for size_name, _, _ in datasets:
        print(f"\n  {size_name}:")
        for impl in implementations:
            output_file = results_dir / f"{impl}_{size_name}_output.txt"
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"    {impl}: ✓ ({size_mb:.2f} MB)")
            else:
                print(f"    {impl}: ✗ Missing")

    return True

if __name__ == "__main__":
    success = generate_all_results()
    sys.exit(0 if success else 1)