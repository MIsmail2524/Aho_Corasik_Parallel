#!/usr/bin/env python3
"""
Compare performance results across implementations and datasets.
"""

import os
import sys
import json
import statistics
from pathlib import Path
from collections import defaultdict

def load_performance_data():
    """Load performance data from results directory"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / "results"

    performance_data = defaultdict(dict)

    # Load timing data from result files
    if results_dir.exists():
        for result_file in results_dir.glob("*_output.txt"):
            # Parse filename: {impl}_{size}_output.txt
            parts = result_file.stem.split('_')
            if len(parts) >= 3:
                impl = '_'.join(parts[:-2])  # Handle impl names with underscores
                size = parts[-2] + parts[-1]  # e.g., "10MB"

                try:
                    with open(result_file, 'r') as f:
                        content = f.read()

                    # Extract timing information (assuming format from implementations)
                    lines = content.strip().split('\n')
                    timing_info = {}

                    for line in lines:
                        if 'Time:' in line or 'time' in line.lower():
                            # Try to extract time in various formats
                            import re
                            time_match = re.search(r'(\d+\.?\d*)\s*(ms|seconds?|s)', line, re.IGNORECASE)
                            if time_match:
                                time_val = float(time_match.group(1))
                                unit = time_match.group(2).lower()
                                if 'ms' in unit:
                                    timing_info['elapsed_seconds'] = time_val / 1000
                                elif 's' in unit:
                                    timing_info['elapsed_seconds'] = time_val

                    if 'elapsed_seconds' in timing_info:
                        performance_data[size][impl] = timing_info

                except Exception as e:
                    print(f"Error reading {result_file}: {e}")

    return performance_data

def calculate_throughput(performance_data):
    """Calculate throughput for each implementation"""

    # File sizes in MB
    file_sizes = {
        '10MB': 10,
        '100MB': 100,
        '500MB': 500
    }

    throughput_data = defaultdict(dict)

    for size, implementations in performance_data.items():
        if size in file_sizes:
            file_size_mb = file_sizes[size]

            for impl, data in implementations.items():
                if 'elapsed_seconds' in data and data['elapsed_seconds'] > 0:
                    throughput = file_size_mb / data['elapsed_seconds']
                    throughput_data[size][impl] = throughput

    return throughput_data

def generate_comparison_report(performance_data, throughput_data):
    """Generate performance comparison report"""

    print("="*100)
    print("PERFORMANCE COMPARISON REPORT")
    print("="*100)

    datasets = ['10MB', '100MB', '500MB']

    for dataset in datasets:
        if dataset not in performance_data:
            continue

        print(f"\n--- {dataset} Dataset ---")

        # Get implementations sorted by throughput
        impl_throughput = throughput_data.get(dataset, {})
        if not impl_throughput:
            print("No throughput data available")
            continue

        sorted_impls = sorted(impl_throughput.items(), key=lambda x: x[1], reverse=True)

        print("<25")
        print("-" * 80)

        baseline_throughput = None
        for impl, throughput in sorted_impls:
            timing = performance_data[dataset].get(impl, {})

            if baseline_throughput is None:
                baseline_throughput = throughput
                speedup = 1.0
            else:
                speedup = throughput / baseline_throughput if baseline_throughput > 0 else 0

            elapsed = timing.get('elapsed_seconds', 0)

            print("<25"
        # Summary statistics
        throughputs = list(impl_throughput.values())
        if throughputs:
            print("
Summary:"            print(".1f"            print(".1f"            print(".1f"            print(".1f"            print(".1f"
def generate_speedup_analysis(throughput_data):
    """Generate speedup analysis across datasets"""

    print("\n" + "="*100)
    print("SPEEDUP ANALYSIS ACROSS DATASETS")
    print("="*100)

    datasets = ['10MB', '100MB', '500MB']
    implementations = set()

    # Collect all implementations
    for dataset in datasets:
        if dataset in throughput_data:
            implementations.update(throughput_data[dataset].keys())

    implementations = sorted(implementations)

    print("<20")
    print("-" * 100)

    for impl in implementations:
        speedups = []
        for dataset in datasets:
            if dataset in throughput_data and impl in throughput_data[dataset]:
                throughput = throughput_data[dataset][impl]
                # Use 10MB as baseline for scaling analysis
                baseline_10mb = throughput_data.get('10MB', {}).get(impl, 0)
                if baseline_10mb > 0:
                    speedup = throughput / baseline_10mb
                    speedups.append(".1f")
                else:
                    speedups.append("N/A")
            else:
                speedups.append("N/A")

        print("<20"
def main():
    """Main comparison function"""

    # Load data
    performance_data = load_performance_data()
    throughput_data = calculate_throughput(performance_data)

    if not performance_data:
        print("No performance data found. Run experiments first.")
        return 1

    # Generate reports
    generate_comparison_report(performance_data, throughput_data)
    generate_speedup_analysis(throughput_data)

    return 0

if __name__ == "__main__":
    sys.exit(main())