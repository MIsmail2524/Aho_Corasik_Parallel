#!/usr/bin/env python3
"""
Generate baseline results from Naive implementation with ALL keywords
"""

import subprocess
import os
import sys
import re
import json
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

def main():
    print("\n" + "="*70)
    print("📊 GENERATING BASELINE RESULTS (Naive Implementation)")
    print("="*70)
    
    os.makedirs("results", exist_ok=True)
    os.makedirs("baseline_matches", exist_ok=True)
    
    kw_file = "inputs/keywords.txt"
    if not os.path.exists(kw_file):
        print(f"❌ Keywords file not found: {kw_file}")
        print("Run: make data")
        return 1
    
    with open(kw_file, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    print(f"📋 Keywords: {len(keywords)} (ALL keywords)")
    
    datasets = [10, 100, 500]
    baseline_results = {}
    
    for size in datasets:
        text_file = f"inputs/text_{size}MB.txt"
        if not os.path.exists(text_file):
            print(f"⚠️ Skipping {size}MB - file not found")
            continue
        
        print(f"\n📁 Processing {size}MB dataset...")
        print(f"  Command: ./aho_naive {text_file} [200 keywords]")
        
        cmd = ['./aho_naive', text_file] + keywords
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
            output = result.stdout
            
            match_count = get_match_count(output)
            time_ms = get_time_ms(output)
            throughput = get_throughput(output)
            
            print(f"  ✓ Matches: {match_count:,}")
            print(f"  ✓ Time: {time_ms:.2f} ms")
            print(f"  ✓ Throughput: {throughput:.1f} MB/s")
            
            baseline_results[str(size)] = {
                'match_count': match_count,
                'time_ms': time_ms,
                'throughput_mb_s': throughput,
                'text_size_mb': size,
                'keywords_count': len(keywords)
            }
            
            with open(f"baseline_matches/naive_{size}MB_output.txt", 'w') as f:
                f.write(output)
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout after 1200 seconds")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    with open('results/baseline_results.json', 'w') as f:
        json.dump(baseline_results, f, indent=2)
    
    print("\n" + "="*70)
    print("✅ BASELINE GENERATION COMPLETE")
    print("="*70)
    
    # Summary
    print("\n📊 Baseline Summary:")
    for size in [10, 100, 500]:
        if str(size) in baseline_results:
            data = baseline_results[str(size)]
            print(f"  {size}MB: {data['match_count']:,} matches in {data['time_ms']:.2f} ms")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())