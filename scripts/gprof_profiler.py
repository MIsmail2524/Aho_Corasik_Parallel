#!/usr/bin/env python3
"""
GProf Profiling for Function-Level Analysis
"""

import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime

def run_command(cmd, timeout=60):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("\n" + "="*70)
    print("📊 GPROF FUNCTION-LEVEL PROFILING")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    os.makedirs("profiling_results", exist_ok=True)
    
    # Check if gprof binaries exist
    binaries = [
        ("aho_naive_gprof", "Naive"),
        ("aho_seq_gprof", "Sequential DFA"),
        ("aho_simd_gprof", "SIMD"),
        ("aho_omp_gprof", "OpenMP"),
        ("aho_openmp_simd_gprof", "OpenMP+SIMD"),
    ]
    
    text_file = "inputs/text_10MB.txt"
    keywords_file = "inputs/keywords.txt"
    
    with open(keywords_file, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    for binary, name in binaries:
        if not os.path.exists(binary):
            print(f"⚠️ {binary} not found (run 'make profile')")
            continue
        
        print(f"\n📁 Profiling: {name}")
        print("-" * 40)
        
        # Remove old gmon.out
        if os.path.exists("gmon.out"):
            os.remove("gmon.out")
        
        # Run to generate gmon.out
        cmd = [f"./{binary}", text_file] + keywords[:50]  # Use first 50 for speed
        _, stderr, rc = run_command(cmd, timeout=120)
        
        if os.path.exists("gmon.out"):
            # Run gprof
            gprof_cmd = ["gprof", "-b", binary, "gmon.out"]
            output, _, _ = run_command(gprof_cmd)
            
            # Save results
            out_file = f"profiling_results/gprof_{binary}_report.txt"
            with open(out_file, 'w') as f:
                f.write(f"GProf Report for {name}\n")
                f.write("="*60 + "\n\n")
                f.write(output)
            
            print(f"  ✓ Report saved: {out_file}")
            
            # Extract flat profile summary
            lines = output.split('\n')
            in_flat = False
            count = 0
            for line in lines:
                if 'Flat profile:' in line:
                    in_flat = True
                    continue
                if in_flat and line.strip() and not line.startswith('%'):
                    print(f"    {line[:80]}")
                    count += 1
                    if count >= 10:
                        break
        else:
            print(f"  ❌ No gmon.out generated")
    
    print("\n✅ GProf profiling complete!")

if __name__ == "__main__":
    sys.exit(main())