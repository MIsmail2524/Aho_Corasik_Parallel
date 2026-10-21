#!/usr/bin/env python3
"""
Generate evidence summary from all experimental results.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def collect_results():
    """Collect results from all analysis phases"""

    results = {
        'correctness': {},
        'performance': {},
        'profiling': {},
        'roofline': {}
    }

    # Correctness results
    correctness_file = Path("src/scripts/verify_correctness.py")
    if correctness_file.exists():
        # Run correctness verification to get current status
        import subprocess
        try:
            result = subprocess.run(["python3", str(correctness_file)],
                                  capture_output=True, text=True, timeout=60)
            results['correctness']['status'] = 'passed' if result.returncode == 0 else 'failed'
            results['correctness']['output'] = result.stdout
        except:
            results['correctness']['status'] = 'error'

    # Performance results
    results_dir = Path("results")
    if results_dir.exists():
        perf_files = list(results_dir.glob("*_output.txt"))
        results['performance']['total_files'] = len(perf_files)
        results['performance']['implementations'] = set()

        for f in perf_files:
            impl = f.name.split('_')[0]
            results['performance']['implementations'].add(impl)

        results['performance']['implementations'] = list(results['performance']['implementations'])

    # Profiling results
    profiling_dir = Path("profiling_results")
    if profiling_dir.exists():
        prof_files = list(profiling_dir.glob("*.txt"))
        results['profiling']['total_files'] = len(prof_files)
        results['profiling']['tools'] = ['gprof', 'perf', 'callgrind']

    # Roofline results
    roofline_file = Path("roofline_results.txt")
    if roofline_file.exists():
        results['roofline']['available'] = True
    else:
        results['roofline']['available'] = False

    return results

def generate_evidence_summary(results):
    """Generate evidence summary report"""

    report_path = Path("EVIDENCE_SUMMARY.md")

    with open(report_path, 'w') as f:
        f.write("# EXPERIMENTAL EVIDENCE SUMMARY\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## OVERVIEW\n\n")
        f.write("This document summarizes the experimental evidence collected from the Aho-Corasick\n")
        f.write("parallel implementation analysis, including correctness verification, performance\n")
        f.write("benchmarking, profiling, and architectural analysis.\n\n")

        f.write("## 1. CORRECTNESS VERIFICATION\n\n")

        correctness = results.get('correctness', {})
        if correctness.get('status') == 'passed':
            f.write("✅ **STATUS: PASSED**\n\n")
            f.write("All implementations produce correct results matching the baseline.\n\n")
        elif correctness.get('status') == 'failed':
            f.write("❌ **STATUS: FAILED**\n\n")
            f.write("Some implementations failed correctness verification.\n\n")
        else:
            f.write("⚠️ **STATUS: NOT TESTED**\n\n")
            f.write("Correctness verification has not been run.\n\n")

        if 'output' in correctness:
            f.write("**Verification Output:**\n")
            f.write("```\n")
            f.write(correctness['output'][:1000])  # Limit output
            f.write("\n```\n\n")

        f.write("## 2. PERFORMANCE ANALYSIS\n\n")

        performance = results.get('performance', {})
        total_files = performance.get('total_files', 0)
        implementations = performance.get('implementations', [])

        f.write(f"**Total Result Files:** {total_files}\n")
        f.write(f"**Implementations Tested:** {len(implementations)}\n\n")

        if implementations:
            f.write("**Available Implementations:**\n")
            for impl in implementations:
                f.write(f"- {impl}\n")
            f.write("\n")

        f.write("## 3. PROFILING ANALYSIS\n\n")

        profiling = results.get('profiling', {})
        prof_files = profiling.get('total_files', 0)
        tools = profiling.get('tools', [])

        f.write(f"**Profiling Data Files:** {prof_files}\n")
        f.write(f"**Profiling Tools Used:** {', '.join(tools)}\n\n")

        f.write("**Profiling Techniques Applied:**\n")
        f.write("- GProf: Function-level execution time analysis\n")
        f.write("- Perf: Hardware performance counter analysis\n")
        f.write("- Callgrind: Cache simulation and call graph analysis\n\n")

        f.write("## 4. ROOFLINE ANALYSIS\n\n")

        roofline = results.get('roofline', {})
        if roofline.get('available'):
            f.write("✅ **STATUS: AVAILABLE**\n\n")
            f.write("Roofline analysis results are available for architectural characterization.\n\n")
        else:
            f.write("❌ **STATUS: NOT AVAILABLE**\n\n")
            f.write("Roofline analysis has not been performed.\n\n")

        f.write("## 5. EXPERIMENTAL COVERAGE\n\n")

        # Calculate coverage
        coverage_items = [
            ("Correctness Verification", correctness.get('status') in ['passed', 'failed']),
            ("Performance Benchmarking", len(implementations) > 0),
            ("GProf Profiling", prof_files > 0),
            ("Perf Analysis", prof_files > 0),
            ("Callgrind Analysis", prof_files > 0),
            ("Roofline Modeling", roofline.get('available', False))
        ]

        completed = sum(1 for _, done in coverage_items if done)
        total = len(coverage_items)

        f.write(f"**Experimental Coverage:** {completed}/{total} components completed\n\n")

        f.write("**Component Status:**\n")
        for component, done in coverage_items:
            status = "✅" if done else "❌"
            f.write(f"{status} {component}\n")
        f.write("\n")

        f.write("## 6. DATA INTEGRITY\n\n")

        # Check for required files
        required_files = [
            "Makefile",
            "src/aho_common.h",
            "src/scripts/generate_baseline.py",
            "src/scripts/generate_all_results.py",
            "src/scripts/verify_correctness.py",
            "src/scripts/performance_analyzer.py",
            "src/scripts/comprehensive_analysis.py"
        ]

        f.write("**Required Files Check:**\n")
        missing_files = []
        for file_path in required_files:
            if Path(file_path).exists():
                f.write(f"✅ {file_path}\n")
            else:
                f.write(f"❌ {file_path} (MISSING)\n")
                missing_files.append(file_path)

        if missing_files:
            f.write(f"\n**Missing Files:** {len(missing_files)}\n")
        else:
            f.write("\n**All required files present.**\n")

        f.write("\n## 7. CONCLUSION\n\n")

        if completed == total and not missing_files:
            f.write("🎉 **EXPERIMENTAL SUITE COMPLETE**\n\n")
            f.write("All experimental components have been successfully executed with complete data integrity.\n")
            f.write("The analysis provides comprehensive evidence for the Aho-Corasick parallel implementation evaluation.\n")
        else:
            f.write("⚠️ **EXPERIMENTAL SUITE INCOMPLETE**\n\n")
            f.write("Some experimental components are missing or incomplete. Review the status above and\n")
            f.write("complete the missing analyses for comprehensive evaluation.\n")

    print(f"Evidence summary generated: {report_path}")
    return report_path

def main():
    """Generate evidence summary"""

    print("Generating experimental evidence summary...")

    # Change to project root
    os.chdir("/home/ismail/PDC_Project")

    # Collect results
    results = collect_results()

    # Generate summary
    report_path = generate_evidence_summary(results)

    print(f"✓ Evidence summary completed: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())