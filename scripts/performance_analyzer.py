#!/usr/bin/env python3
"""
Performance Analyzer - Saves COMPLETE results for ALL algorithms
"""

import subprocess
import os
import sys
import re
import json
import argparse
from datetime import datetime

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

def run_binary(binary, text_file, keywords, env=None, timeout=600):
    try:
        cmd = [binary, text_file] + keywords
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)
        output = result.stdout
        return {
            'time_ms': get_time_ms(output),
            'matches': get_match_count(output),
            'throughput': get_throughput(output),
            'success': True,
            'output': output
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout', 'time_ms': 0, 'matches': 0}
    except Exception as e:
        return {'success': False, 'error': str(e), 'time_ms': 0, 'matches': 0}

def save_results(results, filename):
    """Save results to JSON file"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

def save_csv(results, filename):
    """Save results to CSV format"""
    with open(filename, 'w') as f:
        f.write("Implementation,Dataset,Time(ms),Matches,Throughput(MB/s),Speedup,Status\n")
        for r in results:
            f.write(f"{r['name']},{r['dataset']},{r['time_ms']:.2f},{r['matches']},{r['throughput']:.2f},{r['speedup']:.2f},{r['status']}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datasets', nargs='+', type=int, default=[10, 100])
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🚀 AHO-CORASICK PERFORMANCE ANALYZER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Load ALL keywords
    kw_file = "inputs/keywords.txt"
    if not os.path.exists(kw_file):
        print(f"❌ Keywords file not found: {kw_file}")
        print("   Run: python3 scripts/generate_data.py")
        return 1
    
    with open(kw_file, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    print(f"\n📋 Testing with ALL {len(keywords)} keywords")
    
    # Create results directories
    os.makedirs('results', exist_ok=True)
    os.makedirs('results/timings', exist_ok=True)
    os.makedirs('results/matches', exist_ok=True)
    os.makedirs('results/outputs', exist_ok=True)
    
    all_results = []
    summary_by_dataset = {}
    
    implementations = [
        ('Naive', './aho_naive', None),
        ('Sequential', './aho_seq', None),
        ('SIMD', './aho_simd', None),
        ('OpenMP (4 threads)', './aho_omp', {'OMP_NUM_THREADS': '4'}),
        ('OpenMP+SIMD (4 threads)', './aho_openmp_simd', {'OMP_NUM_THREADS': '4'}),
        ('MPI (2 processes)', './aho_mpi', None),
    ]
    
    for size in args.datasets:
        text_file = f"inputs/text_{size}MB.txt"
        if not os.path.exists(text_file):
            print(f"⚠️ {text_file} not found")
            continue
        
        print(f"\n{'='*80}")
        print(f"📁 Dataset: {size} MB")
        print(f"{'='*80}")
        
        dataset_results = []
        naive_time = None
        naive_matches = None
        
        for name, binary, env in implementations:
            # Skip MPI if binary not found
            if name == 'MPI (2 processes)' and not os.path.exists(binary):
                print(f"  ⚠️ {name}: binary not found (skipping)")
                continue
            
            print(f"  Running {name}...", end=" ", flush=True)
            
            # Special handling for MPI
            if name == 'MPI (2 processes)':
                try:
                    cmd = ['mpirun', '-np', '2', binary, text_file] + keywords
                    start = datetime.now()
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    elapsed = (datetime.now() - start).total_seconds() * 1000
                    output = result.stdout
                    time_ms = get_time_ms(output)
                    if time_ms == 0:
                        time_ms = elapsed
                    matches = get_match_count(output)
                    throughput = get_throughput(output)
                    success = True
                except Exception as e:
                    print(f"❌ Failed: {e}")
                    continue
            else:
                if not os.path.exists(binary):
                    print(f"❌ Binary not found")
                    continue
                result = run_binary(binary, text_file, keywords, env)
                success = result['success']
                time_ms = result['time_ms']
                matches = result['matches']
                throughput = result['throughput']
                output = result.get('output', '')
            
            if success and time_ms > 0:
                print(f"✓ {time_ms:.2f} ms, {matches:,} matches")
                
                if name == 'Naive':
                    naive_time = time_ms
                    naive_matches = matches
                
                dataset_results.append({
                    'name': name,
                    'dataset': size,
                    'time_ms': time_ms,
                    'matches': matches,
                    'throughput': throughput if throughput else 0,
                    'speedup': 1.0 if name == 'Naive' else (naive_time / time_ms if naive_time and time_ms > 0 else 0),
                    'status': '✅' if matches == naive_matches or name == 'Naive' else '⚠️'
                })
                
                # Save individual timing results
                safe_name = name.replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'plus')
                timing_file = f'results/timings/{safe_name}_{size}MB.json'
                with open(timing_file, 'w') as f:
                    json.dump({
                        'algorithm': name,
                        'dataset_mb': size,
                        'time_ms': time_ms,
                        'matches': matches,
                        'throughput_mb_s': throughput if throughput else (text_file.stat().st_size / 1024 / 1024) / (time_ms / 1000),
                        'keywords_count': len(keywords),
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=2)
                
                # Save full output
                output_file = f'results/outputs/{safe_name}_{size}MB_output.txt'
                with open(output_file, 'w') as f:
                    f.write(f"Algorithm: {name}\n")
                    f.write(f"Dataset: {size} MB\n")
                    f.write(f"Keywords: {len(keywords)}\n")
                    f.write(f"Time: {time_ms:.2f} ms\n")
                    f.write(f"Matches: {matches:,}\n")
                    if throughput:
                        f.write(f"Throughput: {throughput:.2f} MB/s\n")
                    f.write("="*80 + "\n\n")
                    f.write(output)
            else:
                print(f"❌ Failed")
        
        # Calculate final speedups for this dataset
        if naive_time:
            for r in dataset_results:
                if r['name'] != 'Naive' and r['time_ms'] > 0:
                    r['speedup'] = naive_time / r['time_ms']
            
            summary_by_dataset[size] = dataset_results
            all_results.extend(dataset_results)
            
            # Display summary table for this dataset
            print(f"\n  {'─'*80}")
            print(f"  {'Implementation':<25} {'Time(ms)':<12} {'Matches':<15} {'Speedup':<12} {'Throughput':<12}")
            print(f"  {'─'*80}")
            for r in dataset_results:
                tp_str = f"{r['throughput']:.1f} MB/s" if r['throughput'] else "N/A"
                print(f"  {r['name']:<25} {r['time_ms']:<12.2f} {r['matches']:<15,} {r['speedup']:<12.2f}x {tp_str:<12}")
            print(f"  {'─'*80}")
    
    # Save all results to JSON
    if all_results:
        save_results(all_results, 'results/all_results.json')
        save_results(summary_by_dataset, 'results/summary_by_dataset.json')
        
        # Save to CSV for Excel
        save_csv(all_results, 'results/all_results.csv')
        
        # Generate comprehensive report
        report_file = 'results/COMPREHENSIVE_REPORT.txt'
        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("AHO-CORASICK PERFORMANCE ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write("SYSTEM INFORMATION:\n")
            f.write("-"*40 + "\n")
            import platform
            f.write(f"  Platform: {platform.platform()}\n")
            f.write(f"  Processor: {platform.processor()}\n")
            f.write(f"  Python: {platform.python_version()}\n\n")
            
            f.write("DATASETS:\n")
            f.write("-"*40 + "\n")
            for size in args.datasets:
                f.write(f"  {size}MB: ~{size * 1024 * 1024:,} bytes\n")
            
            f.write("\nKEYWORDS:\n")
            f.write("-"*40 + "\n")
            f.write(f"  Total keywords: {len(keywords)}\n")
            if keywords:
                f.write(f"  Range: {keywords[0]} to {keywords[-1]}\n")
            
            f.write("\nPERFORMANCE RESULTS:\n")
            f.write("-"*80 + "\n")
            for size, results in summary_by_dataset.items():
                f.write(f"\n📁 {size}MB Dataset:\n")
                f.write(f"  {'─'*70}\n")
                f.write(f"  {'Implementation':<25} {'Time(ms)':<12} {'Matches':<15} {'Speedup':<12}\n")
                f.write(f"  {'─'*70}\n")
                for r in results:
                    f.write(f"  {r['name']:<25} {r['time_ms']:<12.2f} {r['matches']:<15,} {r['speedup']:<12.2f}x\n")
                f.write(f"  {'─'*70}\n")
            
            # Find best performer
            valid_results = [r for r in all_results if r['name'] != 'Naive' and r['speedup'] > 0]
            if valid_results:
                best = min(valid_results, key=lambda x: x['time_ms'])
                f.write("\n🏆 BEST PERFORMANCE:\n")
                f.write("-"*40 + "\n")
                f.write(f"  Algorithm: {best['name']}\n")
                f.write(f"  Dataset: {best['dataset']} MB\n")
                f.write(f"  Time: {best['time_ms']:.2f} ms\n")
                f.write(f"  Speedup: {best['speedup']:.2f}x\n")
                if best['throughput']:
                    f.write(f"  Throughput: {best['throughput']:.1f} MB/s\n")
        
        print(f"\n{'='*80}")
        print("✅ ANALYSIS COMPLETE!")
        print(f"{'='*80}")
        print(f"\n📁 Results saved to:")
        print(f"  - results/all_results.json")
        print(f"  - results/all_results.csv")
        print(f"  - results/COMPREHENSIVE_REPORT.txt")
        print(f"  - results/timings/ (individual timing files)")
        print(f"  - results/outputs/ (full outputs)")
    else:
        print("\n❌ No results collected. Check your binaries and data files.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())