#!/usr/bin/env python3
"""
Generate separate result files for each algorithm
Stores: timing, match count, and verification data
"""

import subprocess
import os
import sys
import json
import time
from datetime import datetime

def run_algorithm(binary, text_file, keywords):
    """Run algorithm and capture output with timing"""
    try:
        start = time.perf_counter()
        result = subprocess.run(
            [binary, text_file] + keywords,
            capture_output=True,
            text=True,
            timeout=600
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        if result.returncode == 0:
            # Parse output
            match_count = 0
            for line in result.stdout.split('\n'):
                if 'Matches:' in line or 'matches' in line.lower():
                    import re
                    m = re.search(r'(\d+)', line)
                    if m:
                        match_count = int(m.group(1))
                        break
            
            return {
                'success': True,
                'time_ms': elapsed_ms,
                'match_count': match_count,
                'output': result.stdout[:500]  # First 500 chars
            }
        else:
            return {
                'success': False,
                'error': result.stderr,
                'time_ms': elapsed_ms
            }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    print("\n" + "="*80)
    print("GENERATING SEPARATE RESULTS FOR EACH ALGORITHM")
    print("="*80)
    
    # Ensure directories
    os.makedirs('results', exist_ok=True)
    os.makedirs('results/timings', exist_ok=True)
    os.makedirs('results/matches', exist_ok=True)
    os.makedirs('results/verification', exist_ok=True)
    
    # Load keywords
    kw_file = "inputs/keywords.txt"
    if not os.path.exists(kw_file):
        print(f"❌ Keywords file not found: {kw_file}")
        return 1
    
    with open(kw_file, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    text_file = "inputs/text_10MB.txt"
    if not os.path.exists(text_file):
        print(f"❌ Text file not found: {text_file}")
        return 1
    
    file_size_mb = os.path.getsize(text_file) / (1024*1024)
    print(f"\n📁 Dataset: {text_file} ({file_size_mb:.2f} MB)")
    print(f"📋 Keywords: {len(keywords)}")
    
    # Algorithms to test
    algorithms = [
        ('aho_naive', 'Naive Sequential (Baseline)'),
        ('aho_seq', 'Optimized Sequential'),
        ('aho_simd', 'SIMD Vectorized'),
        ('aho_omp', 'OpenMP Parallel'),
        ('aho_openmp_simd', 'OpenMP + SIMD'),
    ]
    
    results = {}
    baseline_matches = None
    
    print(f"\n{'─'*80}")
    print(f"{'Algorithm':<30} {'Status':<12} {'Time (ms)':<12} {'Matches':<12}")
    print(f"{'─'*80}")
    
    for binary_name, description in algorithms:
        if not os.path.exists(f'./{binary_name}'):
            print(f"{description:<30} {'⏭️  SKIP':<12}")
            continue
        
        print(f"{description:<30} ", end='', flush=True)
        
        result = run_algorithm(f'./{binary_name}', text_file, keywords)
        results[binary_name] = result
        
        if result['success']:
            time_ms = result['time_ms']
            match_count = result['match_count']
            throughput = (file_size_mb / (time_ms / 1000)) if time_ms > 0 else 0
            
            print(f"{'✅':<12} {time_ms:<12.2f} {match_count:<12,}")
            
            # Store timing
            with open(f'results/timings/{binary_name}_timing.json', 'w') as f:
                json.dump({
                    'algorithm': binary_name,
                    'time_ms': time_ms,
                    'dataset_size_mb': file_size_mb,
                    'throughput_mb_s': throughput,
                    'keywords_count': len(keywords),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Store match count
            with open(f'results/matches/{binary_name}_matches.json', 'w') as f:
                json.dump({
                    'algorithm': binary_name,
                    'match_count': match_count,
                    'keywords_count': len(keywords),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Set baseline if this is naive
            if binary_name == 'aho_naive':
                baseline_matches = match_count
        else:
            print(f"{'❌':<12} {result.get('error', 'Unknown error'):<12}")
    
    # Verify correctness
    print(f"\n{'─'*80}")
    print("CORRECTNESS VERIFICATION")
    print(f"{'─'*80}")
    
    if baseline_matches is None:
        print("❌ Baseline (naive) did not run successfully")
        return 1
    
    print(f"Baseline matches: {baseline_matches:,}")
    
    verification_results = {}
    all_correct = True
    
    for binary_name, result in results.items():
        if not result['success']:
            verification_results[binary_name] = {'status': 'failed', 'reason': result.get('error')}
            all_correct = False
        else:
            match_count = result['match_count']
            is_correct = (match_count == baseline_matches)
            verification_results[binary_name] = {
                'status': 'correct' if is_correct else 'incorrect',
                'matches': match_count,
                'expected': baseline_matches,
                'difference': match_count - baseline_matches
            }
            
            status = '✅' if is_correct else '❌'
            print(f"{binary_name:<30} {status} {match_count:>10,} matches")
            
            if not is_correct:
                all_correct = False
    
    # Save verification report
    with open('results/verification/correctness_report.json', 'w') as f:
        json.dump({
            'baseline_algorithm': 'aho_naive',
            'baseline_matches': baseline_matches,
            'results': verification_results,
            'all_correct': all_correct,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    # Summary
    print(f"\n{'─'*80}")
    if all_correct:
        print("✅ ALL ALGORITHMS PRODUCE CORRECT RESULTS!")
    else:
        print("⚠️  SOME ALGORITHMS HAVE INCORRECT RESULTS")
    
    print(f"\nResults saved to:")
    print(f"  - Timings: results/timings/")
    print(f"  - Matches: results/matches/")
    print(f"  - Verification: results/verification/")
    
    return 0 if all_correct else 1

if __name__ == "__main__":
    sys.exit(main())
