#!/usr/bin/env python3
"""
Comprehensive combined analysis
Merges results, speedup, verification, and profiling data
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def load_all_results():
    """Load all analysis results"""
    data = {}
    
    # Load verification
    if os.path.exists('results/verification/correctness_report.json'):
        with open('results/verification/correctness_report.json', 'r') as f:
            data['verification'] = json.load(f)
    
    # Load speedup analysis
    if os.path.exists('results/analysis/speedup_analysis.json'):
        with open('results/analysis/speedup_analysis.json', 'r') as f:
            data['speedup'] = json.load(f)
    
    return data

def generate_combined_report(data):
    """Generate combined markdown report"""
    report_path = 'results/COMBINED_ANALYSIS_REPORT.md'
    
    with open(report_path, 'w') as f:
        f.write("# Combined Performance Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Verification Section
        f.write("## 1. CORRECTNESS VERIFICATION\n\n")
        if 'verification' in data:
            v = data['verification']
            f.write(f"**Baseline Algorithm:** {v.get('baseline_algorithm')}\n")
            f.write(f"**Baseline Matches:** {v.get('baseline_matches'):,}\n")
            f.write(f"**Overall Status:** {'✅ ALL CORRECT' if v.get('all_correct') else '❌ ERRORS FOUND'}\n\n")
            
            f.write("### Verification Results:\n\n")
            for algo, result in v.get('results', {}).items():
                status = '✅' if result.get('status') == 'correct' else '❌'
                if result.get('status') == 'correct':
                    f.write(f"{status} **{algo}**: {result.get('matches', 0):,} matches\n")
                else:
                    reason = result.get('reason') or result.get('status')
                    f.write(f"{status} **{algo}**: {reason}\n")
        
        # Speedup Section
        f.write("\n## 2. PERFORMANCE AND SPEEDUP ANALYSIS\n\n")
        if 'speedup' in data:
            s = data['speedup']
            baseline = s.get('baseline', {})
            
            f.write(f"**Baseline Performance:**\n")
            f.write(f"- Time: {baseline.get('time_ms', 0):.2f} ms\n")
            f.write(f"- Throughput: {baseline.get('throughput_mb_s', 0):.2f} MB/s\n\n")
            
            f.write("### Speedup Results:\n\n")
            f.write("| Algorithm | Time (ms) | Speedup | Throughput (MB/s) | Status |\n")
            f.write("|-----------|-----------|---------|-------------------|--------|\n")
            
            for algo, impl in s.get('implementations', {}).items():
                desc = impl.get('description', algo)
                time_ms = impl.get('time_ms', 0)
                speedup = impl.get('speedup', 0)
                throughput = impl.get('throughput_mb_s', 0)
                correct = '✅' if impl.get('correct') else '❌'
                anomalies = impl.get('anomalies', [])
                
                status = correct
                if anomalies:
                    status += f" ({anomalies[0][:20]})"
                
                f.write(f"| {desc:<30} | {time_ms:<9.2f} | {speedup:<7.2f}x | {throughput:<17.2f} | {status:<50} |\n")
            
            # Best performer
            impls = s.get('implementations', {})
            if impls:
                best = max(impls.items(), key=lambda x: x[1]['speedup'])
                f.write(f"\n**Best Performance:** {best[1]['description']} with {best[1]['speedup']:.2f}x speedup\n")
        
        # Anomalies Section
        f.write("\n## 3. ANOMALIES AND ISSUES\n\n")
        anomaly_found = False
        if 'speedup' in data and 'implementations' in data['speedup']:
            for algo, impl in data['speedup']['implementations'].items():
                if impl.get('anomalies'):
                    anomaly_found = True
                    f.write(f"### {impl.get('description', algo)}\n")
                    for anomaly in impl['anomalies']:
                        f.write(f"- ⚠️  {anomaly}\n")
                    f.write("\n")
        
        if not anomaly_found:
            f.write("✅ No anomalies detected\n")
        
        # Summary
        f.write("\n## 4. SUMMARY\n\n")
        all_correct = data.get('verification', {}).get('all_correct', False)
        
        if all_correct:
            f.write("✅ **All implementations produce correct results**\n\n")
        else:
            f.write("❌ **Some implementations have correctness issues**\n\n")
        
        if 'speedup' in data:
            s = data['speedup']
            impls = s.get('implementations', {})
            if impls:
                avg_speedup = sum(impl['speedup'] for impl in impls.values()) / len(impls)
                f.write(f"- Average speedup: {avg_speedup:.2f}x\n")
                max_speedup = max(impl['speedup'] for impl in impls.values())
                f.write(f"- Maximum speedup: {max_speedup:.2f}x\n")
        
        f.write("\n---\n")
        f.write("*Report generated automatically by combined analysis suite*\n")
    
    return report_path

def main():
    print("\n" + "="*80)
    print("COMBINED ANALYSIS SUITE")
    print("="*80)
    
    # Load all results
    print("\n📊 Loading analysis results...")
    data = load_all_results()
    
    if not data:
        print("❌ No analysis results found")
        print("   Run: make results && make speedup")
        return 1
    
    print("✅ Results loaded")
    
    # Generate combined report
    print("\n📝 Generating combined report...")
    report_path = generate_combined_report(data)
    print(f"✅ Report generated: {report_path}")
    
    # Display summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if 'verification' in data:
        v = data['verification']
        status = '✅ PASS' if v.get('all_correct') else '❌ FAIL'
        print(f"\nCorrectness: {status}")
    
    if 'speedup' in data:
        s = data['speedup']
        impls = s.get('implementations', {})
        if impls:
            best = max(impls.items(), key=lambda x: x[1]['speedup'])
            print(f"Best Performance: {best[1]['description']}")
            print(f"Speedup: {best[1]['speedup']:.2f}x")
            print(f"Throughput: {best[1]['throughput_mb_s']:.2f} MB/s")
    
    print("\n✅ Combined analysis complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
