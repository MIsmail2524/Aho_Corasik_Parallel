#!/usr/bin/env python3
"""
Advanced profiler with multiple profiling techniques and detailed analysis.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def run_command(cmd, timeout=120):
    """Run command and return results"""
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

def run_gprof_profiling(binary, text_file, keywords_file):
    """Run gprof profiling"""

    print(f"Running gprof profiling for {binary}...")

    # Run with profiling
    cmd = [f"./{binary}", str(text_file), str(keywords_file)]
    success, stdout, stderr, elapsed = run_command(cmd, timeout=300)

    if success:
        # Generate gprof report
        gmon_file = f"gmon_{binary}.out"
        if os.path.exists(gmon_file):
            gprof_cmd = ["gprof", binary, gmon_file]
            success2, gprof_output, _, _ = run_command(gprof_cmd)

            if success2:
                return True, gprof_output
            else:
                return False, "Failed to generate gprof report"
        else:
            return False, "No gmon.out file generated"
    else:
        return False, stderr

def run_perf_profiling(binary, text_file, keywords_file):
    """Run perf profiling"""

    print(f"Running perf profiling for {binary}...")

    # Run with perf record
    record_cmd = [
        "perf", "record", "-F", "99", "-g", "--",
        f"./{binary}", str(text_file), str(keywords_file)
    ]

    success, _, stderr, elapsed = run_command(record_cmd, timeout=300)

    if success:
        # Generate perf report
        report_cmd = ["perf", "report", "--stdio", "-n", "--no-children"]
        success2, perf_output, _, _ = run_command(report_cmd)

        if success2:
            return True, perf_output
        else:
            return False, "Failed to generate perf report"
    else:
        return False, stderr

def run_callgrind_profiling(binary, text_file, keywords_file):
    """Run callgrind profiling"""

    print(f"Running callgrind profiling for {binary}...")

    # Run with valgrind callgrind
    callgrind_cmd = [
        "valgrind", "--tool=callgrind", "--callgrind-out-file=callgrind.out",
        f"./{binary}", str(text_file), str(keywords_file)
    ]

    success, _, stderr, elapsed = run_command(callgrind_cmd, timeout=600)

    if success:
        # Generate callgrind report
        annotate_cmd = ["callgrind_annotate", "callgrind.out"]
        success2, annotate_output, _, _ = run_command(annotate_cmd)

        if success2:
            return True, annotate_output
        else:
            return False, "Failed to generate callgrind annotation"
    else:
        return False, stderr

def run_advanced_profiling():
    """Run advanced profiling suite"""

    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    inputs_dir = script_dir / "inputs"
    profiling_dir = project_root / "profiling_results"

    # Ensure directories exist
    profiling_dir.mkdir(exist_ok=True)

    # Build profiled versions
    print("Building profiled implementations...")
    success, _, _, _ = run_command(["make", "profile"])
    if not success:
        print("Failed to build profiled implementations")
        return False

    # Test files
    text_file = inputs_dir / "text_10MB.txt"
    keywords_file = inputs_dir / "keywords.txt"

    if not text_file.exists() or not keywords_file.exists():
        print("Input files not found")
        return False

    # Implementations to profile
    implementations = [
        "aho_naive_gprof",
        "aho_seq_gprof",
        "aho_simd_gprof",
        "aho_omp_gprof",
        "aho_openmp_simd_gprof"
    ]

    print("\n" + "="*80)
    print("ADVANCED PROFILING SUITE")
    print("="*80)

    results = {}

    for binary in implementations:
        print(f"\n--- Profiling {binary} ---")

        impl_results = {}

        # Gprof profiling
        success, output = run_gprof_profiling(binary, text_file, keywords_file)
        impl_results['gprof'] = {'success': success, 'output': output}

        if success:
            # Save gprof output
            gprof_file = profiling_dir / f"gprof_{binary}.txt"
            with open(gprof_file, 'w') as f:
                f.write(output)
            print(f"  ✓ Gprof results saved to {gprof_file}")
        else:
            print(f"  ✗ Gprof failed: {output}")

        # Perf profiling (if available)
        try:
            success, output = run_perf_profiling(binary, text_file, keywords_file)
            impl_results['perf'] = {'success': success, 'output': output}

            if success:
                perf_file = profiling_dir / f"perf_{binary}.txt"
                with open(perf_file, 'w') as f:
                    f.write(output)
                print(f"  ✓ Perf results saved to {perf_file}")
            else:
                print(f"  ✗ Perf failed: {output}")
        except:
            impl_results['perf'] = {'success': False, 'output': 'Perf not available'}
            print("  - Perf profiling not available")

        # Callgrind profiling (if available)
        try:
            success, output = run_callgrind_profiling(binary, text_file, keywords_file)
            impl_results['callgrind'] = {'success': success, 'output': output}

            if success:
                callgrind_file = profiling_dir / f"callgrind_{binary}.txt"
                with open(callgrind_file, 'w') as f:
                    f.write(output)
                print(f"  ✓ Callgrind results saved to {callgrind_file}")
            else:
                print(f"  ✗ Callgrind failed: {output}")
        except:
            impl_results['callgrind'] = {'success': False, 'output': 'Callgrind not available'}
            print("  - Callgrind profiling not available")

        results[binary] = impl_results

    # Save summary
    summary_file = profiling_dir / "advanced_profiling_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Advanced profiling completed. Summary saved to {summary_file}")
    return True

def main():
    success = run_advanced_profiling()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())