#!/usr/bin/env python3
"""
Complete Benchmark Suite - Saves ALL results with speedup calculations
"""

import subprocess
import os
import sys
import re
import json
import csv
from datetime import datetime
from pathlib import Path

def get_match_count(output):
    for line in output.split('\n'):
        match = re.search(r'Matches\s*:\s*(\d+)', line)
        if match:
            return int(match.group(1))
    return 0

def get_time_ms(output):
    for line in output.split('\n'):
        match = re.search(r'Time\s*:\s*([\d.]+)\s*ms', line)
        if match:
            return float(match.group(1))
    return 0

def get_throughput(output):
    for line in output.split('\n'):
        match = re.search(r'Throughput\s*:\s*([\d.]+)\s*MB/s', line)
        if match:
            return float(match.group(1))
    return 0

def run_benchmark(name, binary, text_file, keywords, threads=None, is_mpi=False):
    """Run a single benchmark and return results"""
    
    env = None
    if threads and 'OpenMP' in name:
        env = {'OMP_NUM_THREADS': str(threads)}
    
    try:
        if is_mpi:
            cmd = ['mpirun', '-np', str(threads), binary, text_file] + keywords
        else:
            cmd = [binary, text_file] + keywords
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        output = result.stdout
        
        return {
            'success': True,
            'time_ms': get_time_ms(output),
            'matches': get_match_count(output),
            'throughput': get_throughput(output),
            'output': output
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    print("\n" + "="*80)
    print("📊 COMPLETE BENCHMARK SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Create results directory
    os.makedirs('results/complete', exist_ok=True)
    os.makedirs('results/json', exist_ok=True)
    os.makedirs('results/csv', exist_ok=True)
    os.makedirs('results/timing', exist_ok=True)
    
    # Load keywords
    with open("inputs/keywords.txt", 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    print(f"📋 Keywords: {len(keywords)}")
    
    # Datasets to test
    datasets = [
        {'size': 10, 'file': 'inputs/text_10MB.txt'},
        {'size': 100, 'file': 'inputs/text_100MB.txt'},
        {'size': 500, 'file': 'inputs/text_500MB.txt'},
    ]
    
    # Thread configurations
    thread_configs = [1, 2, 4, 8, 16]
    
    # MPI process counts
    mpi_configs = [1, 2, 4]
    
    # All results storage
    all_results = []
    
    # First, run baseline (Naive)
    print("\n📁 Running BASELINE (Naive)...")
    baseline_results = {}
    
    for ds in datasets:
        if not os.path.exists(ds['file']):
            continue
        
        print(f"  Dataset: {ds['size']} MB...", end=" ", flush=True)
        result = run_benchmark("Naive", "./aho_naive", ds['file'], keywords)
        
        if result['success'] and result['time_ms'] > 0:
            baseline_results[ds['size']] = {
                'time_ms': result['time_ms'],
                'matches': result['matches'],
                'throughput': result['throughput']
            }
            print(f"✓ {result['time_ms']:.2f} ms, {result['matches']:,} matches")
            
            # Save baseline result
            all_results.append({
                'implementation': 'Naive',
                'threads': 1,
                'dataset_mb': ds['size'],
                'time_ms': result['time_ms'],
                'matches': result['matches'],
                'throughput': result['throughput'],
                'speedup': 1.0,
                'efficiency': 100.0
            })
        else:
            print(f"❌ Failed")
    
    # Run Sequential
    print("\n📁 Running SEQUENTIAL DFA...")
    for ds in datasets:
        if not os.path.exists(ds['file']):
            continue
        
        print(f"  Dataset: {ds['size']} MB...", end=" ", flush=True)
        result = run_benchmark("Sequential", "./aho_seq", ds['file'], keywords)
        
        if result['success'] and result['time_ms'] > 0:
            baseline_time = baseline_results.get(ds['size'], {}).get('time_ms', 1)
            speedup = baseline_time / result['time_ms']
            
            all_results.append({
                'implementation': 'Sequential',
                'threads': 1,
                'dataset_mb': ds['size'],
                'time_ms': result['time_ms'],
                'matches': result['matches'],
                'throughput': result['throughput'],
                'speedup': speedup,
                'efficiency': speedup * 100
            })
            print(f"✓ {result['time_ms']:.2f} ms, {speedup:.2f}x speedup")
        else:
            print(f"❌ Failed")
    
    # Run SIMD
    print("\n📁 Running SIMD...")
    for ds in datasets:
        if not os.path.exists(ds['file']):
            continue
        
        print(f"  Dataset: {ds['size']} MB...", end=" ", flush=True)
        result = run_benchmark("SIMD", "./aho_simd", ds['file'], keywords)
        
        if result['success'] and result['time_ms'] > 0:
            baseline_time = baseline_results.get(ds['size'], {}).get('time_ms', 1)
            speedup = baseline_time / result['time_ms']
            
            all_results.append({
                'implementation': 'SIMD',
                'threads': 1,
                'dataset_mb': ds['size'],
                'time_ms': result['time_ms'],
                'matches': result['matches'],
                'throughput': result['throughput'],
                'speedup': speedup,
                'efficiency': speedup * 100
            })
            print(f"✓ {result['time_ms']:.2f} ms, {speedup:.2f}x speedup")
        else:
            print(f"❌ Failed")
    
    # Run OpenMP with different thread counts
    print("\n📁 Running OPENMP (Multi-thread)...")
    for threads in thread_configs:
        for ds in datasets:
            if not os.path.exists(ds['file']):
                continue
            
            print(f"  Threads={threads}, Dataset={ds['size']} MB...", end=" ", flush=True)
            result = run_benchmark("OpenMP", "./aho_omp", ds['file'], keywords, threads=threads)
            
            if result['success'] and result['time_ms'] > 0:
                baseline_time = baseline_results.get(ds['size'], {}).get('time_ms', 1)
                speedup = baseline_time / result['time_ms']
                efficiency = (speedup / threads) * 100
                
                all_results.append({
                    'implementation': 'OpenMP',
                    'threads': threads,
                    'dataset_mb': ds['size'],
                    'time_ms': result['time_ms'],
                    'matches': result['matches'],
                    'throughput': result['throughput'],
                    'speedup': speedup,
                    'efficiency': efficiency
                })
                print(f"✓ {result['time_ms']:.2f} ms, {speedup:.2f}x speedup, {efficiency:.1f}% efficiency")
            else:
                print(f"❌ Failed")
    
    # Run OpenMP+SIMD Hybrid with different thread counts
    print("\n📁 Running OPENMP+SIMD HYBRID (Multi-thread)...")
    for threads in thread_configs:
        for ds in datasets:
            if not os.path.exists(ds['file']):
                continue
            
            print(f"  Threads={threads}, Dataset={ds['size']} MB...", end=" ", flush=True)
            result = run_benchmark("Hybrid", "./aho_openmp_simd", ds['file'], keywords, threads=threads)
            
            if result['success'] and result['time_ms'] > 0:
                baseline_time = baseline_results.get(ds['size'], {}).get('time_ms', 1)
                speedup = baseline_time / result['time_ms']
                efficiency = (speedup / threads) * 100
                
                all_results.append({
                    'implementation': 'OpenMP+SIMD',
                    'threads': threads,
                    'dataset_mb': ds['size'],
                    'time_ms': result['time_ms'],
                    'matches': result['matches'],
                    'throughput': result['throughput'],
                    'speedup': speedup,
                    'efficiency': efficiency
                })
                print(f"✓ {result['time_ms']:.2f} ms, {speedup:.2f}x speedup, {efficiency:.1f}% efficiency")
            else:
                print(f"❌ Failed")
    
    # Run MPI with different process counts
    print("\n📁 Running MPI (Distributed)...")
    for procs in mpi_configs:
        for ds in datasets:
            if ds['size'] > 100:  # Skip 500MB for MPI (takes too long)
                continue
            if not os.path.exists(ds['file']):
                continue
            
            print(f"  Processes={procs}, Dataset={ds['size']} MB...", end=" ", flush=True)
            result = run_benchmark("MPI", "./aho_mpi", ds['file'], keywords, threads=procs, is_mpi=True)
            
            if result['success'] and result['time_ms'] > 0:
                baseline_time = baseline_results.get(ds['size'], {}).get('time_ms', 1)
                speedup = baseline_time / result['time_ms']
                efficiency = (speedup / procs) * 100
                
                all_results.append({
                    'implementation': 'MPI',
                    'threads': procs,
                    'dataset_mb': ds['size'],
                    'time_ms': result['time_ms'],
                    'matches': result['matches'],
                    'throughput': result['throughput'],
                    'speedup': speedup,
                    'efficiency': efficiency
                })
                print(f"✓ {result['time_ms']:.2f} ms, {speedup:.2f}x speedup, {efficiency:.1f}% efficiency")
            else:
                print(f"❌ Failed")
    
    # ============================================================
    # SAVE ALL RESULTS
    # ============================================================
    
    # Save as JSON
    json_file = 'results/complete/all_results.json'
    with open(json_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✅ JSON results saved: {json_file}")
    
    # Save as CSV
    csv_file = 'results/complete/all_results.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['implementation', 'threads', 'dataset_mb', 
                                                'time_ms', 'matches', 'throughput', 
                                                'speedup', 'efficiency'])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"✅ CSV results saved: {csv_file}")
    
    # Generate summary report
    report_file = 'results/complete/SUMMARY_REPORT.txt'
    with open(report_file, 'w') as f:
        f.write("="*100 + "\n")
        f.write("COMPLETE BENCHMARK SUMMARY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*100 + "\n\n")
        
        # Group by dataset
        for ds in [10, 100, 500]:
            ds_results = [r for r in all_results if r['dataset_mb'] == ds]
            if not ds_results:
                continue
            
            f.write(f"\n{'='*80}\n")
            f.write(f"DATASET: {ds} MB\n")
            f.write(f"{'='*80}\n\n")
            
            # Find baseline
            baseline = next((r for r in ds_results if r['implementation'] == 'Naive'), None)
            if baseline:
                f.write(f"Baseline (Naive): {baseline['time_ms']:.2f} ms, {baseline['matches']:,} matches\n\n")
            
            # Group by implementation
            impls = {}
            for r in ds_results:
                key = f"{r['implementation']}"
                if key not in impls:
                    impls[key] = []
                impls[key].append(r)
            
            for impl, results in impls.items():
                f.write(f"\n{impl}:\n")
                f.write(f"{'─'*60}\n")
                f.write(f"{'Threads':<10} {'Time(ms)':<12} {'Speedup':<12} {'Efficiency':<12} {'Throughput':<12}\n")
                f.write(f"{'─'*60}\n")
                for r in sorted(results, key=lambda x: x['threads']):
                    f.write(f"{r['threads']:<10} {r['time_ms']:<12.2f} {r['speedup']:<12.2f}x {r['efficiency']:<12.1f}% {r['throughput']:<12.1f}\n")
                f.write(f"{'─'*60}\n")
        
        # Best performer
        best = min([r for r in all_results if r['implementation'] != 'Naive'], 
                   key=lambda x: x['time_ms'], default=None)
        if best:
            f.write(f"\n{'='*80}\n")
            f.write("🏆 BEST OVERALL PERFORMANCE\n")
            f.write(f"{'='*80}\n")
            f.write(f"  Implementation: {best['implementation']}\n")
            f.write(f"  Threads: {best['threads']}\n")
            f.write(f"  Dataset: {best['dataset_mb']} MB\n")
            f.write(f"  Time: {best['time_ms']:.2f} ms\n")
            f.write(f"  Speedup: {best['speedup']:.2f}x\n")
            f.write(f"  Throughput: {best['throughput']:.1f} MB/s\n")
    
    print(f"✅ Summary report saved: {report_file}")
    
    # Print final summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    
    # Best speedup per dataset
    for ds in [10, 100, 500]:
        ds_results = [r for r in all_results if r['dataset_mb'] == ds and r['implementation'] != 'Naive']
        if ds_results:
            best = max(ds_results, key=lambda x: x['speedup'])
            print(f"\n{ds}MB Dataset:")
            print(f"  Best: {best['implementation']} with {best['threads']} threads")
            print(f"  Time: {best['time_ms']:.2f} ms")
            print(f"  Speedup: {best['speedup']:.2f}x")
            print(f"  Efficiency: {best['efficiency']:.1f}%")
    
    print("\n✅ Complete benchmark finished!")
    return 0

if __name__ == "__main__":
    sys.exit(main())