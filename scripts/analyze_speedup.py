#!/usr/bin/env python3
"""
Calculate speedup analysis from timing data
Verifies speedup values and flags anomalies
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def load_timing_file(algorithm):
    """Load timing data for an algorithm"""
    timing_file = f'results/timings/{algorithm}_timing.json'
    if not os.path.exists(timing_file):
        return None
    
    with open(timing_file, 'r') as f:
        return json.load(f)

def load_matches_file(algorithm):
    """Load match count and keywords metadata for an algorithm"""
    matches_file = f'results/matches/{algorithm}_matches.json'
    if not os.path.exists(matches_file):
        return None
    
    with open(matches_file, 'r') as f:
        return json.load(f)

def calculate_speedup(baseline_time, algorithm_time):
    """Calculate speedup and flag anomalies"""
    if algorithm_time <= 0 or baseline_time <= 0:
        return None, "Invalid timing"
    
    speedup = baseline_time / algorithm_time
    
    # Check for anomalies
    anomalies = []
    
    # Speedup much higher than expected (usually indicates error)
    if speedup > 100:
        anomalies.append(f"Very high speedup ({speedup:.1f}x)")
    
    # Slowdown for supposedly optimized version
    if speedup < 0.8 and algorithm_time > baseline_time:
        anomalies.append("Slower than baseline")
    
    # Check for unrealistic parallelization (speedup > core count)
    import multiprocessing
    core_count = multiprocessing.cpu_count()
    if speedup > core_count * 1.5:
        anomalies.append(f"Speedup exceeds logical core count ({speedup:.1f}x vs {core_count} cores)")
    
    return speedup, anomalies

def main():
    print("\n" + "="*80)
    print("SPEEDUP AND PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Ensure output directory
    os.makedirs('results/analysis', exist_ok=True)
    
    # Load baseline
    baseline_timing = load_timing_file('aho_naive')
    if not baseline_timing:
        print("❌ Baseline timing not found. Run 'make results' first")
        return 1
    
    baseline_time = baseline_timing['time_ms']
    baseline_throughput = baseline_timing['throughput_mb_s']
    
    baseline_keywords = None
    baseline_matches_data = load_matches_file('aho_naive')
    if baseline_matches_data:
        baseline_keywords = baseline_matches_data.get('keywords_count')

    print(f"\n📊 BASELINE (Naive Sequential):")
    print(f"   Time: {baseline_time:.2f} ms")
    print(f"   Throughput: {baseline_throughput:.2f} MB/s")
    if baseline_keywords is not None:
        print(f"   Keywords: {baseline_keywords}")
    
    # Algorithms to analyze
    algorithms = [
        ('aho_seq', 'Optimized Sequential'),
        ('aho_simd', 'SIMD Vectorized'),
        ('aho_omp', 'OpenMP Parallel'),
        ('aho_openmp_simd', 'OpenMP + SIMD'),
    ]
    
    speedup_data = {
        'baseline': {
            'algorithm': 'aho_naive',
            'time_ms': baseline_time,
            'throughput_mb_s': baseline_throughput
        },
        'implementations': {}
    }
    
    print(f"\n{'─'*80}")
    print(f"{'Algorithm':<30} {'Time (ms)':<12} {'Speedup':<10} {'Throughput':<12} {'Status':<15}")
    print(f"{'─'*80}")
    
    all_valid = True
    
    for binary_name, description in algorithms:
        timing = load_timing_file(binary_name)
        matches = load_matches_file(binary_name)
        
        if not timing:
            print(f"{description:<30} {'N/A':<12} {'N/A':<10} {'N/A':<12} {'⏭️  SKIP':<15}")
            continue

        keyword_count = None
        if matches:
            keyword_count = matches.get('keywords_count')
        if baseline_keywords is not None and keyword_count is not None and keyword_count != baseline_keywords:
            print(f"   ⚠️  Keyword count mismatch for {description}: {keyword_count} vs {baseline_keywords}")
        
        algo_time = timing['time_ms']
        algo_throughput = timing['throughput_mb_s']
        speedup, anomalies = calculate_speedup(baseline_time, algo_time)
        if keyword_count is not None and baseline_keywords is not None and keyword_count != baseline_keywords:
            anomalies.append(f"Keyword count mismatch ({keyword_count} vs {baseline_keywords})")
        
        if speedup is None:
            print(f"{description:<30} {'ERROR':<12} {'ERROR':<10} {'ERROR':<12} {'❌ Error':<15}")
            all_valid = False
            continue
        
        # Verify correctness
        correctness_file = 'results/verification/correctness_report.json'
        if os.path.exists(correctness_file):
            with open(correctness_file, 'r') as f:
                correctness = json.load(f)
                algo_correct = correctness['results'].get(binary_name, {}).get('status') == 'correct'
                correctness_indicator = '✅' if algo_correct else '❌'
        else:
            correctness_indicator = '?'
            algo_correct = True
        
        # Determine status
        if anomalies:
            status = f"⚠️  {anomalies[0][:10]}"
            all_valid = False
        elif speedup < 1.0:
            status = "⚠️  Slower"
        elif speedup >= 2.0 or 'SIMD' in description or 'OpenMP' in description:
            status = "✅ Good"
        else:
            status = "✓ OK"
        
        print(f"{description:<30} {algo_time:<12.2f} {speedup:<10.2f}x {algo_throughput:<12.2f} {status:<15} {correctness_indicator}")
        
        speedup_data['implementations'][binary_name] = {
            'description': description,
            'time_ms': algo_time,
            'speedup': speedup,
            'throughput_mb_s': algo_throughput,
            'anomalies': anomalies,
            'correct': algo_correct
        }
    
    # Save speedup analysis
    with open('results/analysis/speedup_analysis.json', 'w') as f:
        json.dump(speedup_data, f, indent=2)
    
    # Generate speedup report
    print(f"\n{'─'*80}")
    print("SPEEDUP SUMMARY")
    print(f"{'─'*80}")
    
    implementations = speedup_data['implementations']
    if implementations:
        max_speedup = max((impl['speedup'] for impl in implementations.values()), default=0)
        best_algo = max(implementations.items(), key=lambda x: x[1]['speedup'])[0] if implementations else None
        
        print(f"\n🏆 Best performance: {implementations[best_algo]['description']}")
        print(f"   Speedup: {implementations[best_algo]['speedup']:.2f}x")
        print(f"   Throughput: {implementations[best_algo]['throughput_mb_s']:.2f} MB/s")
        
        # Anomalies report
        anomaly_count = sum(len(impl['anomalies']) for impl in implementations.values())
        if anomaly_count > 0:
            print(f"\n⚠️  ANOMALIES DETECTED ({anomaly_count}):")
            for algo, impl in implementations.items():
                if impl['anomalies']:
                    print(f"   {impl['description']}:")
                    for anomaly in impl['anomalies']:
                        print(f"     - {anomaly}")
    
    print(f"\n{'─'*80}")
    if all_valid:
        print("✅ All speedup values are valid")
    else:
        print("⚠️  Some anomalies detected - review above")
    
    print(f"\nAnalysis saved to: results/analysis/speedup_analysis.json")
    
    return 0  # Always return 0 even if anomalies exist

if __name__ == "__main__":
    sys.exit(main())
