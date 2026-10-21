CXX = g++
MPICXX = mpicxx
CXXFLAGS = -std=c++17 -Wall -Wextra
OPTFLAGS = -O3
OPENMPFLAGS = -fopenmp
SIMDFLAGS = -msse4.1 -mavx2 -mfma

# Thread counts to test
THREADS = 1 2 4 8 16

# Datasets to test
DATASETS = 10 100 500

# Primary targets
all: aho_naive aho_seq aho_simd aho_omp aho_openmp_simd aho_mpi roofline_measurement

# Profiling targets
profile: aho_naive_gprof aho_seq_gprof aho_simd_gprof aho_omp_gprof aho_openmp_simd_gprof

# Regular binaries
aho_naive: src/aho_naive.cpp
	$(CXX) $(CXXFLAGS) -O2 -o $@ $<

aho_naive_gprof: src/aho_naive.cpp
	$(CXX) $(CXXFLAGS) -O2 -pg -o $@ $<

aho_seq: src/aho_sequential.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) -O2 -o $@ $<

aho_seq_gprof: src/aho_sequential.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) -O2 -pg -o $@ $<

aho_simd: src/aho_simd.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) $(SIMDFLAGS) -o $@ $<

aho_simd_gprof: src/aho_simd.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) $(SIMDFLAGS) -pg -o $@ $<

aho_omp: src/aho_openmp.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) $(OPENMPFLAGS) -o $@ $<

aho_omp_gprof: src/aho_openmp.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) $(OPENMPFLAGS) -pg -o $@ $<

aho_openmp_simd: src/aho_openmp_simd.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) $(OPENMPFLAGS) $(SIMDFLAGS) -o $@ $<

aho_openmp_simd_gprof: src/aho_openmp_simd.cpp src/aho_common.h
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) $(OPENMPFLAGS) $(SIMDFLAGS) -pg -o $@ $<

aho_mpi: src/aho_mpi.cpp src/aho_common.h
	$(MPICXX) $(CXXFLAGS) $(OPTFLAGS) -DUSE_MPI -o $@ $<

roofline_measurement: src/roofline_measurement.cpp
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) -o $@ $<

# Data generation
data:
	@mkdir -p inputs
	@python3 scripts/generate_data.py

# ============================================================
# SIMPLE BENCHMARK (No AWK - Uses Python)
# ============================================================

# Simple benchmark using Python script
benchmark:
	@python3 scripts/quick_benchmark.py

# Complete benchmark using Python script
full-benchmark: all
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                    COMPLETE BENCHMARK SUITE                                  ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@python3 scripts/complete_benchmark.py

# ============================================================
# MULTI-THREAD TESTING TARGETS (Simplified)
# ============================================================

# Test OpenMP with different thread counts
test-omp: all
	@echo ""
	@echo "=== OPENMP SCALABILITY TEST ==="
	@for threads in $(THREADS); do \
		echo ""; \
		echo "Threads: $$threads"; \
		echo "----------------------------------------"; \
		for size in $(DATASETS); do \
			echo -n "  $$size MB: "; \
			OMP_NUM_THREADS=$$threads ./aho_omp inputs/text_$${size}MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+' | head -1; \
		done \
	done

# Test OpenMP+SIMD with different thread counts
test-hybrid: all
	@echo ""
	@echo "=== OPENMP+SIMD HYBRID SCALABILITY TEST ==="
	@for threads in $(THREADS); do \
		echo ""; \
		echo "Threads: $$threads"; \
		echo "----------------------------------------"; \
		for size in $(DATASETS); do \
			echo -n "  $$size MB: "; \
			OMP_NUM_THREADS=$$threads ./aho_openmp_simd inputs/text_$${size}MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+' | head -1; \
		done \
	done

# Test Sequential
test-seq: all
	@echo ""
	@echo "=== SEQUENTIAL Aho-Corasick ==="
	@for size in $(DATASETS); do \
		echo -n "  $$size MB: "; \
		./aho_seq inputs/text_$${size}MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+' | head -1; \
	done

# Test SIMD
test-simd: all
	@echo ""
	@echo "=== SIMD Aho-Corasick ==="
	@for size in $(DATASETS); do \
		echo -n "  $$size MB: "; \
		./aho_simd inputs/text_$${size}MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+' | head -1; \
	done

# Test Naive
test-naive: all
	@echo ""
	@echo "=== NAIVE Baseline ==="
	@for size in $(DATASETS); do \
		echo -n "  $$size MB: "; \
		./aho_naive inputs/text_$${size}MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+' | head -1; \
	done

# Compare all single-threaded
test-all-single: all
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                    SINGLE-THREAD PERFORMANCE                                 ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Implementation         10MB        100MB       500MB"
	@echo "─────────────────────────────────────────────────────────────"
	@echo -n "Naive                 "; ./aho_naive inputs/text_10MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'; \
	                                 ./aho_naive inputs/text_100MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'; \
	                                 ./aho_naive inputs/text_500MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'
	@echo -n "Sequential           "; ./aho_seq inputs/text_10MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'; \
	                                 ./aho_seq inputs/text_100MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'; \
	                                 ./aho_seq inputs/text_500MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'
	@echo -n "SIMD                  "; ./aho_simd inputs/text_10MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'; \
	                                 ./aho_simd inputs/text_100MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'; \
	                                 ./aho_simd inputs/text_500MB.txt keyword0 keyword1 keyword2 2>&1 | grep -oP 'Time\s*:\s*\K[\d.]+'

# ============================================================
# BASELINE AND ANALYSIS
# ============================================================

# Generate baseline results
baseline: all
	@echo "Generating baseline results from Naive implementation..."
	@mkdir -p results baseline_matches
	@python3 scripts/generate_baseline.py

# Run performance analysis
analyze: baseline all
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║              PERFORMANCE ANALYSIS (10MB and 100MB)                           ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@python3 scripts/performance_analyzer.py --datasets 10 100

# Run on 10MB only
analyze-10: baseline all
	@python3 scripts/performance_analyzer.py --datasets 10

# Run on 100MB only
analyze-100: baseline all
	@python3 scripts/performance_analyzer.py --datasets 100

# Verify correctness
verify: baseline all
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         CORRECTNESS VERIFICATION SUITE                       ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@python3 scripts/verify_correctness.py

# ============================================================
# PROFILING
# ============================================================

# GProf profiling
gprof: profile
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         GPROF FUNCTION PROFILING                             ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@python3 scripts/gprof_profiler.py

# Roofline analysis
roofline: roofline_measurement
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                     EMPIRICAL ROOFLINE ANALYSIS                              ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@mkdir -p profiling_results
	@./roofline_measurement | tee profiling_results/roofline_metrics.txt

# Comprehensive profiling suite
profiling: profile
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║        COMPREHENSIVE PROFILING: GPROF + PERF + HARDWARE METRICS             ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@mkdir -p profiling_results
	@python3 scripts/profiling_suite.py

# Quick benchmark
quick-benchmark: all
	@python3 scripts/quick_benchmark.py

# ============================================================
# CLEAN
# ============================================================

clean:
	rm -f aho_naive aho_seq aho_simd aho_omp aho_openmp_simd aho_mpi
	rm -f aho_naive_gprof aho_seq_gprof aho_simd_gprof aho_omp_gprof aho_openmp_simd_gprof
	rm -f gmon.out roofline_measurement perf*.data
	rm -f *.png *.dot *.txt
	rm -rf profiling_results results matches baseline_matches __pycache__ scripts/__pycache__ inputs/__pycache__

.PHONY: all clean data baseline analyze analyze-10 analyze-100 verify gprof roofline profiling
.PHONY: test-omp test-hybrid test-seq test-simd test-naive test-all-single
.PHONY: benchmark full-benchmark quick-benchmark