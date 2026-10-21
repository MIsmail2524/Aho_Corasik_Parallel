#!/usr/bin/env python3
"""
Comprehensive profiling: gprof + perf + hardware metrics
"""

import subprocess
import os
import sys
import json
import time
from datetime import datetime

def run_gprof_profiling(binary, text_file, keywords):
    """Run gprof profiling"""
    print(f"\n  🔍 GProf profiling {binary}...")
    
    try:
        # Run with profiling
        subprocess.run(
            [f'./{binary}', text_file] + keywords,
            capture_output=True,
            timeout=300
        )
        
        # Check for gmon.out
        gmon_file = 'gmon.out'
        if os.path.exists(gmon_file):
            # Generate gprof report
            result = subprocess.run(
                ['gprof', binary, gmon_file],
                capture_output=True,
                text=True
            )
            
            # Save report
            os.makedirs('profiling_results', exist_ok=True)
            report_file = f'profiling_results/gprof_{binary}.txt'
            with open(report_file, 'w') as f:
                f.write(result.stdout)
            
            # Extract top functions
            lines = result.stdout.split('\n')
            top_functions = []
            in_flat_profile = False
            
            for line in lines:
                if '% cumulative' in line:
                    in_flat_profile = True
                    continue
                if in_flat_profile and line.strip() and not line.startswith(' '):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            percent = float(parts[0].rstrip('%'))
                            if percent > 0.1:
                                top_functions.append({
                                    'time_percent': percent,
                                    'function': ' '.join(parts[5:]) if len(parts) > 5 else 'unknown'
                                })
                        except:
                            pass
            
            return {
                'success': True,
                'report_file': report_file,
                'top_functions': top_functions[:5]
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': 'No gmon.out generated'}

def run_perf_profiling(binary, text_file, keywords):
    """Run perf profiling"""
    print(f"\n  📊 Perf profiling {binary}...")
    
    try:
        # Run with perf
        perf_data_file = f'perf_{binary}.data'
        subprocess.run(
            ['perf', 'record', '-o', perf_data_file, '--', 
             f'./{binary}', text_file] + keywords,
            capture_output=True,
            timeout=300
        )
        
        if os.path.exists(perf_data_file):
            # Generate perf report
            result = subprocess.run(
                ['perf', 'report', '-i', perf_data_file, '--stdio', '-n'],
                capture_output=True,
                text=True
            )
            
            # Save report
            os.makedirs('profiling_results', exist_ok=True)
            report_file = f'profiling_results/perf_{binary}.txt'
            with open(report_file, 'w') as f:
                f.write(result.stdout)
            
            # Extract hotspots
            hotspots = []
            lines = result.stdout.split('\n')
            
            for line in lines[:20]:
                if '%' in line and 'libpthread' not in line.lower():
                    hotspots.append(line.strip())
            
            # Cleanup
            try:
                os.remove(perf_data_file)
            except:
                pass
            
            return {
                'success': True,
                'report_file': report_file,
                'hotspots': hotspots[:5]
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': 'Perf execution failed'}

def run_hardware_metrics(binary, text_file, keywords):
    """Run perf stat for hardware metrics"""
    print(f"\n  ⚡ Hardware metrics for {binary}...")
    
    try:
        result = subprocess.run(
            ['perf', 'stat', '-e', 'cycles,instructions,cache-misses,branch-misses',
             f'./{binary}', text_file] + keywords,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Parse metrics
        metrics = {}
        for line in result.stderr.split('\n'):
            if 'cycles' in line:
                parts = line.split()
                if len(parts) > 0:
                    try:
                        cycles = int(parts[0].replace(',', ''))
                        metrics['cycles'] = cycles
                    except:
                        pass
            elif 'instructions' in line and 'cache-misses' not in line:
                parts = line.split()
                if len(parts) > 0:
                    try:
                        instr = int(parts[0].replace(',', ''))
                        metrics['instructions'] = instr
                        if 'cycles' in metrics:
                            metrics['ipc'] = instr / metrics['cycles'] if metrics['cycles'] > 0 else 0
                    except:
                        pass
            elif 'cache-misses' in line:
                parts = line.split()
                if len(parts) > 0:
                    try:
                        misses = int(parts[0].replace(',', ''))
                        metrics['cache_misses'] = misses
                    except:
                        pass
        
        return {
            'success': bool(metrics),
            'metrics': metrics
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE PROFILING SUITE")
    print("="*80)
    
    # Load keywords
    kw_file = "inputs/keywords.txt"
    if not os.path.exists(kw_file):
        print(f"❌ Keywords not found: {kw_file}")
        return 1
    
    with open(kw_file, 'r') as f:
        keywords = [line.strip() for line in f if line.strip()]
    
    text_file = "inputs/text_10MB.txt"
    if not os.path.exists(text_file):
        print(f"❌ Text file not found: {text_file}")
        return 1
    
    # Build profiled versions
    print("\n📦 Building profiled versions...")
    result = subprocess.run(['make', 'profile'], capture_output=True)
    if result.returncode != 0:
        print("❌ Build failed")
        return 1
    print("✅ Built successfully")
    
    # Algorithms to profile
    algorithms = [
        'aho_naive_gprof',
        'aho_seq_gprof',
        'aho_simd_gprof',
        'aho_omp_gprof',
        'aho_openmp_simd_gprof',
    ]
    
    profiling_data = {}
    
    for algo in algorithms:
        if not os.path.exists(f'./{algo}'):
            print(f"\n⏭️  {algo} not found, skipping")
            continue
        
        print(f"\n{'─'*80}")
        print(f"Profiling: {algo}")
        print(f"{'─'*80}")
        
        profiling_data[algo] = {}
        
        # GProf
        gprof_result = run_gprof_profiling(algo, text_file, keywords)
        if gprof_result['success']:
            print(f"  ✅ GProf report saved")
            profiling_data[algo]['gprof'] = {
                'success': True,
                'top_functions': gprof_result.get('top_functions', [])
            }
        else:
            print(f"  ⚠️  GProf failed: {gprof_result.get('error')}")
            profiling_data[algo]['gprof'] = {'success': False}
        
        # Perf (if available)
        try:
            perf_result = run_perf_profiling(algo, text_file, keywords)
            if perf_result['success']:
                print(f"  ✅ Perf report saved")
                profiling_data[algo]['perf'] = {
                    'success': True,
                    'hotspots': perf_result.get('hotspots', [])
                }
            else:
                print(f"  ⚠️  Perf not available")
                profiling_data[algo]['perf'] = {'success': False}
        except:
            profiling_data[algo]['perf'] = {'success': False}
        
        # Hardware metrics
        metrics_result = run_hardware_metrics(algo, text_file, keywords)
        if metrics_result['success']:
            print(f"  ✅ Hardware metrics captured")
            profiling_data[algo]['metrics'] = metrics_result['metrics']
        else:
            print(f"  ⚠️  Metrics unavailable")
    
    # Save profiling data
    os.makedirs('profiling_results', exist_ok=True)
    with open('profiling_results/profiling_summary.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'profiling_data': profiling_data
        }, f, indent=2)
    
    print(f"\n{'─'*80}")
    print("✅ Profiling complete!")
    print(f"Results saved to: profiling_results/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
