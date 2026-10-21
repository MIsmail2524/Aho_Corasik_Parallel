#!/usr/bin/env python3
"""
Save outputs from all algorithms to separate files for comparison
"""

import subprocess
import os
import sys
from datetime import datetime

def save_output(binary, text_file, keywords, output_file, env=None):
    try:
        cmd = [binary, text_file] + keywords
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        with open(output_file, 'w') as f:
            f.write(f"# {binary} - {text_file}\n")
            f.write(f"# Generated: {datetime.now()}\n")
            f.write(f"# Return code: {result.returncode}\n")
            f.write("="*80 + "\n\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr)
        
        return True, result.stdout
    except Exception as e:
        return False, str(e)

def main():
    os.makedirs("results/saved_outputs", exist_ok=True)
    
    # Load ALL keywords
    with open("inputs/keywords.txt", 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    text_file = "inputs/text_10MB.txt"
    
    implementations = [
        ('aho_naive', 'Naive'),
        ('aho_seq', 'Sequential'),
        ('aho_simd', 'SIMD'),
        ('aho_omp', 'OpenMP'),
        ('aho_openmp_simd', 'OpenMP_SIMD'),
    ]
    
    results = {}
    baseline_matches = None
    
    print("Saving outputs from all implementations...\n")
    
    for binary, name in implementations:
        if not os.path.exists(f'./{binary}'):
            print(f"⚠️ {binary} not found")
            continue
        
        output_file = f"results/saved_outputs/{name}_output.txt"
        print(f"  Running {name}...", end=" ", flush=True)
        
        env = {'OMP_NUM_THREADS': '4'} if 'OpenMP' in name else None
        success, output = save_output(f'./{binary}', text_file, keywords, output_file, env)
        
        if success:
            # Extract match count
            import re
            match = re.search(r'Matches\s*:\s*(\d+)', output)
            matches = int(match.group(1)) if match else 0
            results[name] = matches
            if name == 'Naive':
                baseline_matches = matches
            print(f"✓ {matches:,} matches")
        else:
            print(f"❌ Failed: {output}")
    
    # Compare results
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    print(f"{'Implementation':<20} {'Matches':<15} {'Status':<15}")
    print("-"*50)
    
    all_correct = True
    for name, matches in results.items():
        if name == 'Naive':
            status = "(baseline)"
        elif matches == baseline_matches:
            status = "✅ CORRECT"
        else:
            status = f"❌ INCORRECT (diff: {baseline_matches - matches})"
            all_correct = False
        print(f"{name:<20} {matches:<15,} {status:<15}")
    
    print("-"*50)
    if all_correct:
        print("\n✅ ALL implementations produce CORRECT results!")
    else:
        print("\n❌ Some implementations have INCORRECT results")
    
    print(f"\n📁 Outputs saved to: results/saved_outputs/")

if __name__ == "__main__":
    sys.exit(main())