#!/usr/bin/env python3
"""
Quick benchmark script for rapid performance testing.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, timeout=60):
    """Run command and return (success, stdout, stderr, elapsed_time)"""
    start_time = time.time()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start_time

        if result.returncode == 0:
            return True, result.stdout, result.stderr, elapsed
        else:
            return False, result.stdout, result.stderr, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return False, "", "Timeout", elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        return False, "", str(e), elapsed

def parse_match_count(output):
    """Extract match count from output"""
    for line in output.split('\n'):
        if 'Matches' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    return int(parts[1].strip())
                except:
                    pass
    return 0

def quick_benchmark():
    """Run quick performance benchmark on 10MB dataset"""

    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    inputs_dir = project_root / "inputs"

    print("\n" + "=" * 60)
    print("QUICK PERFORMANCE BENCHMARK (10MB)")
    print("=" * 60)

    # Check if binaries exist
    implementations = [
        ("aho_naive", "Naive Sequential"),
        ("aho_seq", "Optimized Sequential"),
        ("aho_simd", "SIMD Vectorized"),
        ("aho_omp", "OpenMP Parallel"),
        ("aho_openmp_simd", "OpenMP+SIMD Hybrid"),
        ("aho_mpi", "MPI Distributed")
    ]

    # Test files
    text_file = inputs_dir / "text_10MB.txt"
    keywords_file = inputs_dir / "keywords.txt"

    if not text_file.exists() or not keywords_file.exists():
        print("Input files not found. Run generate_data.py first.")
        return False

    # Load keywords
    with open(keywords_file, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]

    results = []

    for binary, name in implementations:
        print(f"\n  Testing {name}...", end=" ", flush=True)

        # Skip MPI if not available
        if binary == "aho_mpi":
            cmd = ["mpirun", "-np", "2", f"./{binary}", str(text_file)] + keywords
        else:
            if not (project_root / binary).exists():
                print("Binary not found")
                continue
            cmd = [f"./{binary}", str(text_file)] + keywords

        success, stdout, stderr, elapsed = run_command(cmd, timeout=300)

        if success:
            match_count = parse_match_count(stdout)
            file_size_mb = text_file.stat().st_size / (1024 * 1024)
            throughput = file_size_mb / elapsed if elapsed > 0 else 0

            print(f"✓ {elapsed:.2f}s, {throughput:.1f} MB/s, {match_count} matches")
            results.append((name, elapsed, throughput, match_count))
        else:
            print(f"✗ Failed: {stderr[:100] if stderr else 'Unknown error'}")
            results.append((name, 0, 0, 0))

    # Summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    if results:
        print(f"\n{'Implementation':<25} {'Time(s)':<10} {'MB/s':<10} {'Matches':<12}")
        print("-" * 60)

        # Display results in order
        for name, elapsed, throughput, matches in results:
            if elapsed > 0:
                print(f"{name:<25} {elapsed:<10.3f} {throughput:<10.2f} {matches:<12,}")
            else:
                print(f"{name:<25} {'FAILED':<10} {'FAILED':<10} {'FAILED':<12}")

        # Find best
        best = max([(n, t, tp, m) for n, t, tp, m in results if t > 0], key=lambda x: x[2], default=None)
        if best:
            print("\n" + "-" * 60)
            print(f"🏆 FASTEST: {best[0]} with {best[2]:.1f} MB/s ({best[1]:.3f}s)")
    else:
        print("  No successful benchmarks")

    return True

if __name__ == "__main__":
    success = quick_benchmark()
    sys.exit(0 if success else 1)