#!/usr/bin/env python3
"""
Reliable profiler with multiple measurement techniques and statistical analysis.
"""

import os
import sys
import subprocess
import time
import statistics
import json
from pathlib import Path
from collections import defaultdict

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

def parse_perf_output(output):
    """Parse perf stat output and extract metrics"""
    metrics = {}

    for line in output.split('\n'):
        line = line.strip()
        if not line or '<not supported>' in line:
            continue

        # Parse instructions per cycle
        if 'instructions' in line and '#' in line:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    metrics['instructions_per_cycle'] = float(parts[3].rstrip(','))
                except:
                    pass
        # Parse cycles
        elif 'cycles' in line and 'cycles' not in metrics:
            parts = line.split()
            if len(parts) >= 1:
                try:
                    metrics['cycles'] = int(parts[0].replace(',', ''))
                except:
                    pass
        # Parse instructions
        elif 'instructions' in line and 'instructions' not in metrics:
            parts = line.split()
            if len(parts) >= 1:
                try:
                    metrics['instructions'] = int(parts[0].replace(',', ''))
                except:
                    pass
        # Parse cache-misses
        elif 'cache-misses' in line and 'cache-misses' not in metrics:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    metrics['cache_misses'] = int(parts[0].replace(',', ''))
                    metrics['cache_miss_ratio'] = float(parts[3].rstrip('%'))
                except:
                    pass
        # Parse branch-misses
        elif 'branch-misses' in line and 'branch-misses' not in metrics:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    metrics['branch_misses'] = int(parts[0].replace(',', ''))
                    metrics['branch_miss_ratio'] = float(parts[3].rstrip('%'))
                except:
                    pass

    return metrics

def run_reliable_profiling(binary, text_file, keywords_file, runs=5):
    """Run reliable profiling with multiple runs and statistical analysis"""

    print(f"Profiling {binary} with {runs} runs...")

    results = {
        'binary': binary,
        'runs': [],
        'statistics': {}
    }

    for run in range(runs):
        print(f"  Run {run + 1}/{runs}...")

        # Run with perf stat for hardware counters
        cmd = [
            'perf', 'stat', '-e', 'cycles,instructions,cache-misses,branch-misses',
            f'./{binary}', str(text_file), str(keywords_file)
        ]

        success, stdout, stderr, elapsed = run_command(cmd, timeout=120)

        if success:
            # Parse perf output
            perf_metrics = parse_perf_output(stderr)

            run_data = {
                'run_number': run + 1,
                'elapsed_time': elapsed,
                'perf_metrics': perf_metrics,
                'success': True
            }
        else:
            run_data = {
                'run_number': run + 1,
                'elapsed_time': elapsed,
                'perf_metrics': {},
                'success': False,
                'error': stderr
            }

        results['runs'].append(run_data)

    # Calculate statistics
    successful_runs = [r for r in results['runs'] if r['success']]
    if successful_runs:
        elapsed_times = [r['elapsed_time'] for r in successful_runs]

        results['statistics'] = {
            'mean_time': statistics.mean(elapsed_times),
            'median_time': statistics.median(elapsed_times),
            'std_dev_time': statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0,
            'min_time': min(elapsed_times),
            'max_time': max(elapsed_times),
            'successful_runs': len(successful_runs),
            'total_runs': runs
        }

        # Calculate throughput statistics
        file_size_mb = text_file.stat().st_size / (1024 * 1024)
        throughputs = [file_size_mb / t for t in elapsed_times]

        results['statistics'].update({
            'mean_throughput_mb_s': statistics.mean(throughputs),
            'median_throughput_mb_s': statistics.median(throughputs),
            'std_dev_throughput_mb_s': statistics.stdev(throughputs) if len(throughputs) > 1 else 0
        })

    return results

def generate_summary_report(all_results, output_dir):
    """Generate summary report of profiling results"""

    summary_file = output_dir / "reliable_profiling_summary.txt"

    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("RELIABLE PROFILING SUMMARY REPORT\n")
        f.write("=" * 80 + "\n\n")

        for binary, results in all_results.items():
            f.write(f"Implementation: {binary}\n")
            f.write("-" * 40 + "\n")

            stats = results.get('statistics', {})
            if stats:
                f.write(f"  Mean time: {stats['mean_time']:.3f} seconds\n")
                f.write(f"  Median time: {stats['median_time']:.3f} seconds\n")
                f.write(f"  Std dev: {stats['std_dev_time']:.3f} seconds\n")
                f.write(f"  Min time: {stats['min_time']:.3f} seconds\n")
                f.write(f"  Max time: {stats['max_time']:.3f} seconds\n")
                f.write(f"  Mean throughput: {stats['mean_throughput_mb_s']:.2f} MB/s\n")
                f.write(f"  Successful runs: {stats['successful_runs']}/{stats['total_runs']}\n")
            else:
                f.write("  No successful runs\n")

            f.write("\n")

    print(f"Summary report saved: {summary_file}")

def main():
    """Run reliable profiling suite"""

    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    inputs_dir = project_root / "inputs"
    profiling_dir = project_root / "profiling_results"

    # Ensure directories exist
    profiling_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 80)
    print("RELIABLE PROFILING SUITE")
    print("=" * 80)

    # Check if binaries exist, build if needed
    implementations = [
        "aho_naive",
        "aho_seq",
        "aho_simd",
        "aho_omp",
        "aho_openmp_simd"
    ]

    missing = []
    for binary in implementations:
        if not (project_root / binary).exists():
            missing.append(binary)

    if missing:
        print(f"Building missing binaries: {missing}")
        success, _, _, _ = run_command(["make", "all"], timeout=300)
        if not success:
            print("Failed to build implementations")
            return 1

    # Test files
    text_file = inputs_dir / "text_10MB.txt"
    keywords_file = inputs_dir / "keywords.txt"

    if not text_file.exists() or not keywords_file.exists():
        print("Input files not found. Run generate_data.py first.")
        return 1

    all_results = {}

    for binary in implementations:
        results = run_reliable_profiling(binary, text_file, keywords_file, runs=3)
        all_results[binary] = results

        # Save individual results
        result_file = profiling_dir / f"reliable_profile_{binary}.json"
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=2)

    # Generate summary report
    generate_summary_report(all_results, profiling_dir)

    print("\n✓ Reliable profiling completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())