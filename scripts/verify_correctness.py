#!/usr/bin/env python3
"""
Correctness Verification Suite - Compares all implementations against naive baseline
"""

import subprocess
import os
import sys
import re
from datetime import datetime

def get_match_count(output):
    for line in output.split('\n'):
        match = re.search(r'Matches\s*:\s*(\d+)', line)
        if match:
            return int(match.group(1))
    return 0

def run_binary(binary, text_file, keywords, env=None):
    try:
        cmd = [binary, text_file] + keywords
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
        return get_match_count(result.stdout)
    except Exception as e:
        print(f"    Error: {e}")
        return -1

def main():
    print("\n" + "="*70)
    print("🔍 CORRECTNESS VERIFICATION SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    if not os.path.exists('./aho_naive'):
        print("❌ ./aho_naive not found. Run 'make all'")
        return 1
    
    kw_file = "inputs/keywords.txt"
    if not os.path.exists(kw_file):
        print(f"❌ Keywords file not found: {kw_file}")
        return 1
    
    with open(kw_file, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    print(f"📋 Testing with ALL {len(keywords)} keywords")
    
    # Use smaller dataset for faster verification
    text_file = "inputs/text_10MB.txt"
    if not os.path.exists(text_file):
        print(f"❌ {text_file} not found")
        return 1
    
    print(f"📁 Text file: {text_file}")
    print("-" * 50)
    
    # Get baseline from naive
    print("  Running Naive...", end=" ", flush=True)
    naive_count = run_binary('./aho_naive', text_file, keywords)
    print(f"{naive_count:,} matches")
    
    if naive_count <= 0:
        print(f"    ⚠️ Warning: No matches found!")
        return 1
    
    results = {'Naive': naive_count}
    
    # Test other implementations
    binaries = [
        ('Sequential', './aho_seq'),
        ('SIMD', './aho_simd'),
        ('OpenMP', './aho_omp'),
        ('OpenMP+SIMD', './aho_openmp_simd'),
    ]
    
    for name, binary in binaries:
        if os.path.exists(binary):
            print(f"  Running {name}...", end=" ", flush=True)
            if 'OpenMP' in name:
                env = {'OMP_NUM_THREADS': '4'}
            else:
                env = None
            count = run_binary(binary, text_file, keywords, env)
            results[name] = count
            print(f"{count:,} matches")
    
    # Compare results
    print(f"\n  📊 Comparison (baseline: {naive_count:,} matches):")
    print(f"  {'-'*50}")
    
    all_correct = True
    for name, count in results.items():
        if name == 'Naive':
            continue
        if count == naive_count:
            print(f"    ✅ {name}: MATCH ({count:,} matches)")
        else:
            diff = naive_count - count
            print(f"    ❌ {name}: MISMATCH (diff: {diff:,} matches)")
            all_correct = False
    
    print("\n" + "="*70)
    if all_correct:
        print("✅ VERIFICATION PASSED - All implementations match Naive baseline!")
    else:
        print("❌ VERIFICATION FAILED - Some implementations don't match baseline")
    print("="*70)
    
    return 0 if all_correct else 1

if __name__ == "__main__":
    sys.exit(main())