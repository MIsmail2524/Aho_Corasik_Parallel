#!/usr/bin/env python3
"""
Orchestrate comprehensive profiling: gprof, perf, callgrind, and custom analysis.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_command(cmd, description="", timeout=300):
    """Run a command and return success status"""
    print(f"[*] {description}")
    print(f"    Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print("    ✓ Success")
            return True, result.stdout, result.stderr
        else:
            print(f"    ✗ Failed (exit code {result.returncode})")
            print(f"    Error: {result.stderr}")
            return False, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print("    ✗ Timeout")
        return False, "", "Timeout"
    except Exception as e:
        print(f"    ✗ Exception: {e}")
        return False, "", str(e)

def run_gprof_analysis():
    """Run gprof profiling analysis"""

    print("\n--- GPROF PROFILING ---")

    # Build profiled versions
    success, _, _ = run_command(["make", "profile"], "Building profiled implementations")
    if not success:
        return False

    # Run gprof profiling script
    success, _, _ = run_command(["python3", "src/scripts/advanced_profiler.py"], "Running advanced profiler")
    if not success:
        return False

    return True

def run_perf_analysis():
    """Run perf-based analysis"""

    print("\n--- PERF ANALYSIS ---")

    # Run reliable profiler (includes perf)
    success, _, _ = run_command(["python3", "src/scripts/reliable_profiler.py"], "Running reliable profiler")
    if not success:
        return False

    return True

def run_roofline_analysis():
    """Run roofline analysis"""

    print("\n--- ROOFLINE ANALYSIS ---")

    # Build roofline tool
    success, _, _ = run_command(["make", "roofline"], "Building roofline measurement tool")
    if not success:
        return False

    # Run roofline measurement
    success, _, _ = run_command(["./roofline_measurement"], "Running roofline measurement", timeout=600)
    if not success:
        return False

    return True

def generate_profiling_report():
    """Generate comprehensive profiling report"""

    print("\n--- GENERATING PROFILING REPORT ---")

    # Setup paths
    profiling_dir = Path("profiling_results")
    report_file = Path("PROFILING_ANALYSIS_REPORT.md")

    with open(report_file, 'w') as f:
        f.write("# COMPREHENSIVE PROFILING ANALYSIS REPORT\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## EXECUTIVE SUMMARY\n\n")
        f.write("This report provides comprehensive profiling analysis using multiple techniques:\n")
        f.write("- GProf: Function-level profiling and call graphs\n")
        f.write("- Perf: Hardware performance counters and sampling\n")
        f.write("- Callgrind: Detailed call graphs and cache simulation\n")
        f.write("- Roofline Analysis: Computational intensity and memory bandwidth limits\n\n")

        # Load and summarize results
        if profiling_dir.exists():
            f.write("## PROFILING RESULTS SUMMARY\n\n")

            # GProf results
            gprof_files = list(profiling_dir.glob("gprof_*.txt"))
            if gprof_files:
                f.write("### GProf Analysis\n\n")
                for gprof_file in gprof_files:
                    impl_name = gprof_file.stem.replace('gprof_', '')
                    f.write(f"#### {impl_name}\n\n")
                    try:
                        with open(gprof_file, 'r') as gf:
                            content = gf.read()
                            # Extract top functions
                            lines = content.split('\n')[:20]  # First 20 lines
                            f.write("```\n")
                            f.write('\n'.join(lines))
                            f.write("\n```\n\n")
                    except:
                        f.write("Error reading gprof output\n\n")

            # Perf results
            perf_files = list(profiling_dir.glob("perf_*.txt"))
            if perf_files:
                f.write("### Perf Analysis\n\n")
                for perf_file in perf_files:
                    impl_name = perf_file.stem.replace('perf_', '')
                    f.write(f"#### {impl_name}\n\n")
                    try:
                        with open(perf_file, 'r') as pf:
                            content = pf.read()
                            lines = content.split('\n')[:30]  # First 30 lines
                            f.write("```\n")
                            f.write('\n'.join(lines))
                            f.write("\n```\n\n")
                    except:
                        f.write("Error reading perf output\n\n")

            # Callgrind results
            callgrind_files = list(profiling_dir.glob("callgrind_*.txt"))
            if callgrind_files:
                f.write("### Callgrind Analysis\n\n")
                for cg_file in callgrind_files:
                    impl_name = cg_file.stem.replace('callgrind_', '')
                    f.write(f"#### {impl_name}\n\n")
                    try:
                        with open(cg_file, 'r') as cf:
                            content = cf.read()
                            lines = content.split('\n')[:25]  # First 25 lines
                            f.write("```\n")
                            f.write('\n'.join(lines))
                            f.write("\n```\n\n")
                    except:
                        f.write("Error reading callgrind output\n\n")

        f.write("## RECOMMENDATIONS\n\n")
        f.write("### Performance Optimizations\n")
        f.write("- Focus on high-cost functions identified by gprof\n")
        f.write("- Address cache misses and branch mispredictions from perf\n")
        f.write("- Optimize memory access patterns based on callgrind cache analysis\n")
        f.write("- Compare against roofline limits for algorithmic efficiency\n\n")

        f.write("### Profiling Best Practices\n")
        f.write("- Use multiple profiling tools for comprehensive analysis\n")
        f.write("- Profile on representative workloads\n")
        f.write("- Consider both time and hardware counter metrics\n")
        f.write("- Validate optimizations with before/after profiling\n\n")

    print(f"✓ Profiling report generated: {report_file}")
    return True

def main():
    """Run comprehensive profiling orchestration"""

    print("="*80)
    print("PROFILING ORCHESTRATOR")
    print("="*80)

    # Change to project root
    os.chdir("/home/ismail/PDC_Project")

    # Run all profiling analyses
    analyses = [
        ("GProf Analysis", run_gprof_analysis),
        ("Perf Analysis", run_perf_analysis),
        ("Roofline Analysis", run_roofline_analysis),
        ("Report Generation", generate_profiling_report)
    ]

    success_count = 0

    for name, analysis_func in analyses:
        print(f"\n--- {name} ---")
        if analysis_func():
            success_count += 1
        else:
            print(f"Analysis failed: {name}")

    print("\n" + "="*80)
    print("PROFILING ORCHESTRATION SUMMARY")
    print("="*80)
    print(f"Completed analyses: {success_count}/{len(analyses)}")

    if success_count == len(analyses):
        print("🎉 ALL PROFILING ANALYSES COMPLETED!")
        print("Check PROFILING_ANALYSIS_REPORT.md for detailed results")
        return 0
    else:
        print("❌ SOME ANALYSES FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())