================================================================================
                    PARALLEL AHO-CORASICK ALGORITHM
          Multi-Pattern String Matching with OpenMP, SIMD, and MPI
================================================================================

Authors: Ismail (23i-2524), M. Saim (23i-0781)
Course: Parallel and Distributed Computing - PDC Project
Repository: github.com/MIsmail2524/Aho_Corasik_Parallel

================================================================================
TABLE OF CONTENTS
================================================================================

1. Overview
2. Problem Statement
3. Algorithm Background
4. Implementations
5. Performance Results
6. Multi-Thread Scaling
7. Profiling Analysis
8. System Requirements
9. Installation & Setup
10. Usage Guide
11. Profiling Tools
12. Project Structure
13. Results Summary
14. LLM Usage Disclosure
15. Future Work
16. References
17. Team

================================================================================
1. OVERVIEW
================================================================================

This project implements and evaluates six parallel variants of the Aho-Corasick
algorithm for multi-pattern string matching, achieving up to 21x speedup on a
4-core/8-thread Intel i5-10310U CPU.

+------------------+--------------------------------------------------+----------------+
| Implementation   | Description                                      | Best Speedup   |
+------------------+--------------------------------------------------+----------------+
| Naive            | Brute force baseline (O(n·m·k))                  | 1.00x          |
| Sequential DFA   | Failure-less DFA (Algorithm 4 from paper)        | 19.64x         |
| SIMD             | SSE2/AVX2 vectorized state-0 skipping            | 10.22x         |
| OpenMP           | Thread-parallel text partitioning                | 19.07x         |
| OpenMP+SIMD      | Hybrid parallelization (best overall)            | 21.38x         |
| MPI              | Distributed memory (single-node test)            | 17.53x         |
+------------------+--------------------------------------------------+----------------+

================================================================================
2. PROBLEM STATEMENT
================================================================================

Multi-pattern string matching finds all occurrences of any keyword from a large
set in a given text.

REAL-WORLD APPLICATIONS:
------------------------
- Network Intrusion Detection: Snort scans packets against 10,000+ signatures
- Antivirus Software: Scanning files against millions of virus definitions
- DNA Sequencing: Finding gene patterns in genetic data
- Search Engines: Keyword matching in web pages
- Spam Filtering: Detecting spam patterns in emails

THE CHALLENGE:
--------------
Naive Approach: O(n x m x k)

For 500MB text, 200 keywords (avg 8 chars):
    ~ 200 x 500,000,000 x 8 = 800 BILLION comparisons!

The Aho-Corasick algorithm (1975) solves this with O(n) time, but the original
paper lacked parallelization. This project fills that gap.

================================================================================
3. ALGORITHM BACKGROUND
================================================================================

THE THREE FUNCTIONS (Aho & Corasick, 1975):
-------------------------------------------
1. Goto Function (g): Builds a trie of all keywords
2. Failure Function (f): Provides backup transitions (like KMP)
3. Output Function: Associates keyword matches with states

EXAMPLE:
--------
Keywords: {"he", "she", "his", "hers"}
Text: "ushers"

Matches found:
  - "she" at positions 1-3
  - "he" at positions 2-3
  - "hers" at positions 2-5

GAPS ADDRESSED:
---------------
+--------------------------+----------------------------------------------+
| Original Limitation      | Our Solution                                 |
+--------------------------+----------------------------------------------+
| No parallelization       | OpenMP, SIMD, MPI implementations            |
| Memory explosion (DFA)   | Two-level DFA (hot/cold states)              |
| Static keyword set       | Double-buffer updates (design)               |
| Exact matching only      | Approximate matching (future work)           |
+--------------------------+----------------------------------------------+

================================================================================
4. IMPLEMENTATIONS
================================================================================

IMPLEMENTATION 1: NAIVE (BASELINE)
-----------------------------------
Triple-nested loops for correctness verification. O(n·m·k) time complexity.
Used ONLY as ground truth for verification.

IMPLEMENTATION 2: SEQUENTIAL DFA (ALGORITHM 4)
----------------------------------------------
Precomputes ALL transitions so search requires exactly ONE lookup per character.
O(n) time, perfect for caching. DFA fits in L1 cache.

IMPLEMENTATION 3: SIMD VECTORIZED
---------------------------------
When the automaton is at state 0 (majority of time), SSE2 instructions scan
16 bytes at once to find keyword-starting characters, skipping non-matching
text instantly.

IMPLEMENTATION 4: OPENMP PARALLEL
---------------------------------
Text is divided into chunks with overlap (max_keyword_len - 1) to handle
cross-boundary patterns. Each thread processes its chunk independently.

IMPLEMENTATION 5: OPENMP+SIMD HYBRID
------------------------------------
Combines outer OpenMP thread-level parallelism with inner SIMD data-level
parallelism. Best overall performance.

IMPLEMENTATION 6: MPI DISTRIBUTED
---------------------------------
Text is distributed across MPI processes; results are gathered at rank 0.
Designed for clusters, NOT for single-node systems.

================================================================================
5. PERFORMANCE RESULTS
================================================================================

500MB DATASET (200 keywords):
+------------------+---------+------------+---------+----------------+
| Implementation   | Threads | Time (ms)  | Speedup | Throughput     |
+------------------+---------+------------+---------+----------------+
| Naive            | 1       | 265,475    | 1.00x   | 2.1 MB/s       |
| Sequential DFA   | 1       | 21,510     | 12.34x  | 26.1 MB/s      |
| SIMD             | 1       | 31,430     | 8.45x   | 17.8 MB/s      |
| OpenMP           | 8       | 18,174     | 14.61x  | 30.8 MB/s      |
| OpenMP+SIMD      | 16      | 17,101     | 15.52x  | 32.8 MB/s      |
+------------------+---------+------------+---------+----------------+

10MB DATASET (200 keywords):
+------------------+---------+------------+---------+----------------+
| Implementation   | Threads | Time (ms)  | Speedup | Throughput     |
+------------------+---------+------------+---------+----------------+
| Naive            | 1       | 4,965      | 1.00x   | 2.3 MB/s       |
| Sequential DFA   | 1       | 253        | 19.64x  | 44.4 MB/s      |
| SIMD             | 1       | 486        | 10.22x  | 23.1 MB/s      |
| OpenMP           | 4       | 260        | 19.07x  | 43.1 MB/s      |
| OpenMP+SIMD      | 4       | 232        | 21.38x  | 48.4 MB/s      |
+------------------+---------+------------+---------+----------------+

100MB DATASET (200 keywords):
+------------------+---------+------------+---------+----------------+
| Implementation   | Threads | Time (ms)  | Speedup | Throughput     |
+------------------+---------+------------+---------+----------------+
| Naive            | 1       | 49,338     | 1.00x   | 2.3 MB/s       |
| Sequential DFA   | 1       | 3,265      | 15.11x  | 34.3 MB/s      |
| SIMD             | 1       | 6,323      | 7.80x   | 17.7 MB/s      |
| OpenMP           | 4       | 3,266      | 15.11x  | 34.3 MB/s      |
| OpenMP+SIMD      | 1       | 3,060      | 16.12x  | 36.6 MB/s      |
| MPI (2 proc)     | 2       | 4,548      | 10.85x  | 24.6 MB/s      |
+------------------+---------+------------+---------+----------------+

================================================================================
6. MULTI-THREAD SCALING
================================================================================

OPENMP SCALING (500MB Dataset):
+---------+------------+---------+------------+----------------+
| Threads | Time (ms)  | Speedup | Efficiency | Throughput     |
+---------+------------+---------+------------+----------------+
| 1       | 21,823     | 12.16x  | 100%       | 25.7 MB/s      |
| 2       | 19,822     | 13.39x  | 67%        | 28.3 MB/s      |
| 4       | 20,755     | 12.79x  | 32%        | 27.0 MB/s      |
| 8       | 18,174     | 14.61x  | 18%        | 30.8 MB/s      |
| 16      | 19,128     | 13.88x  | 9%         | 29.3 MB/s      |
+---------+------------+---------+------------+----------------+

OPENMP+SIMD SCALING (500MB Dataset):
+---------+------------+---------+------------+----------------+
| Threads | Time (ms)  | Speedup | Efficiency | Throughput     |
+---------+------------+---------+------------+----------------+
| 1       | 18,884     | 14.06x  | 100%       | 29.7 MB/s      |
| 2       | 19,289     | 13.76x  | 69%        | 29.1 MB/s      |
| 4       | 18,408     | 14.42x  | 36%        | 30.4 MB/s      |
| 8       | 17,296     | 15.35x  | 19%        | 32.4 MB/s      |
| 16      | 17,101     | 15.52x  | 10%        | 32.8 MB/s      |
+---------+------------+---------+------------+----------------+

MPI SCALING (100MB Dataset):
+-----------+------------+---------+------------+----------------+
| Processes | Time (ms)  | Speedup | Efficiency | Throughput     |
+-----------+------------+---------+------------+----------------+
| 1         | 4,535      | 10.88x  | 100%       | 24.7 MB/s      |
| 2         | 4,548      | 10.85x  | 54%        | 24.6 MB/s      |
| 4         | 5,212      | 9.47x   | 24%        | 21.5 MB/s      |
+-----------+------------+---------+------------+----------------+

NOTE: MPI performs poorly on single node due to:
      - IPC overhead (0.24s system time vs 0.01s for OpenMP)
      - Separate memory spaces (68MB vs 49MB)
      - Only 40% CPU utilization (vs 94-99% for OpenMP)
      MPI is designed for distributed clusters, NOT single-node systems.

================================================================================
7. PROFILING ANALYSIS
================================================================================

RESOURCE USAGE (10MB Dataset):
+------------------+-----------+----------+----------+-------+
| Implementation   | User Time | Sys Time | Max RSS  | CPU % |
+------------------+-----------+----------+----------+-------+
| Naive            | 5.01s     | 0.04s    | 38 MB    | 97%   |
| Sequential DFA   | 0.59s     | 0.05s    | 48 MB    | 98%   |
| SIMD             | 0.53s     | 0.02s    | 47 MB    | 99%   |
| OpenMP (4T)      | 0.50s     | 0.01s    | 49 MB    | 94%   |
| OpenMP+SIMD (4T) | 0.48s     | 0.01s    | 49 MB    | 98%   |
| MPI (2P)         | 0.42s     | 0.24s    | 68 MB    | 40%   |
+------------------+-----------+----------+----------+-------+

GPROF HOTSPOTS (Sequential DFA):
+---------------------+----------+-----------------+
| Function            | Time %   | Calls           |
+---------------------+----------+-----------------+
| search_sequential   | 33.33%   | 1               |
| match_less          | 27.78%   | 79 million      |
| introsort           | 22.22%   | 1               |
| read_file           | 16.67%   | 1               |
+---------------------+----------+-----------------+

ROOFLINE MODEL (Hardware Characterization):
+----------------------+-------------------+
| Metric               | Value             |
+----------------------+-------------------+
| Peak Bandwidth       | 16.88 GB/s        |
| Peak Compute         | 1.53 GFLOPS       |
| Ridge Point          | 0.09 FLOPS/byte   |
| Classification       | COMPUTE-BOUND     |
+----------------------+-------------------+

All implementations are compute-bound since pattern matching arithmetic
intensity (0.01-0.097 FLOPS/byte) is less than the ridge point (0.09).

================================================================================
8. SYSTEM REQUIREMENTS
================================================================================

HARDWARE:
+-------------------+-------------------+-------------------+
| Component         | Minimum           | Recommended       |
+-------------------+-------------------+-------------------+
| CPU               | 4 cores           | 8+ cores          |
| RAM               | 4 GB              | 8+ GB             |
| Storage           | 2 GB              | 10+ GB            |
+-------------------+-------------------+-------------------+

SOFTWARE:
+-------------------+-------------------+-----------------------------------+
| Tool              | Version           | Installation                      |
+-------------------+-------------------+-----------------------------------+
| g++               | 9.0+              | sudo apt install g++              |
| make              | 4.0+              | sudo apt install make             |
| OpenMP            | 4.5+              | Included with g++                 |
| MPI               | 3.0+              | sudo apt install libopenmpi-dev   |
| Python            | 3.8+              | sudo apt install python3          |
| gprof             | -                 | sudo apt install binutils         |
+-------------------+-------------------+-----------------------------------+

================================================================================
9. INSTALLATION & SETUP
================================================================================

STEP 1: Clone Repository
------------------------
git clone https://github.com/MIsmail2524/Aho_Corasik_Parallel.git
cd Aho_Corasik_Parallel

STEP 2: Build All Binaries
--------------------------
make clean
make all

STEP 3: Generate Test Data
--------------------------
make data

This creates:
  - inputs/keywords.txt (200 keywords: keyword0 to keyword199)
  - inputs/text_10MB.txt
  - inputs/text_100MB.txt
  - inputs/text_500MB.txt

STEP 4: Generate Baseline (Naive Results)
-----------------------------------------
make baseline

STEP 5: Run Performance Analysis
--------------------------------
make analyze

================================================================================
10. USAGE GUIDE
================================================================================

RUN INDIVIDUAL IMPLEMENTATIONS:
-------------------------------
# Naive baseline
./aho_naive inputs/text_10MB.txt $(cat inputs/keywords.txt)

# Sequential DFA
./aho_seq inputs/text_10MB.txt $(cat inputs/keywords.txt)

# SIMD
./aho_simd inputs/text_10MB.txt $(cat inputs/keywords.txt)

# OpenMP (4 threads)
OMP_NUM_THREADS=4 ./aho_omp inputs/text_10MB.txt $(cat inputs/keywords.txt)

# OpenMP+SIMD (4 threads)
OMP_NUM_THREADS=4 ./aho_openmp_simd inputs/text_10MB.txt $(cat inputs/keywords.txt)

# MPI (2 processes)
mpirun -np 2 ./aho_mpi inputs/text_10MB.txt $(cat inputs/keywords.txt)

MAKE COMMANDS:
+---------------------+--------------------------------------------------+
| Command             | Description                                      |
+---------------------+--------------------------------------------------+
| make all            | Build all binaries                               |
| make data           | Generate test data                               |
| make baseline       | Generate naive baseline results                  |
| make analyze        | Run performance analysis (10MB, 100MB)           |
| make analyze-10     | Run on 10MB only                                 |
| make analyze-100    | Run on 100MB only                                |
| make verify         | Verify correctness of all implementations        |
| make benchmark      | Quick benchmark                                  |
| make profiling      | Run gprof profiling                              |
| make roofline       | Run roofline analysis                            |
| make clean          | Clean all binaries and results                   |
+---------------------+--------------------------------------------------+

================================================================================
11. PROFILING TOOLS
================================================================================

QUICK BENCHMARK:
---------------
make benchmark

GPROF FUNCTION PROFILING:
------------------------
make profile      # Build profiling binaries
make profiling    # Run gprof analysis

ROOFLINE ANALYSIS:
-----------------
make roofline

COMPLETE BENCHMARK SUITE:
------------------------
make full-benchmark

Results saved to: results/benchmarks/complete_results.csv

================================================================================
12. PROJECT STRUCTURE
================================================================================

PDC_Project/
├── Makefile                    # Build automation
├── README.md                   # This file
│
├── src/                        # Source files
│   ├── aho_common.h           # Shared DFA builder
│   ├── aho_naive.cpp          # Naive baseline
│   ├── aho_sequential.cpp     # Sequential DFA
│   ├── aho_simd.cpp           # SIMD vectorized
│   ├── aho_openmp.cpp         # OpenMP parallel
│   ├── aho_openmp_simd.cpp    # Hybrid implementation
│   ├── aho_mpi.cpp            # MPI distributed
│   └── roofline_measurement.cpp # Hardware characterization
│
├── scripts/                    # Python analysis scripts
│   ├── generate_data.py       # Test data generator
│   ├── generate_baseline.py   # Baseline generation
│   ├── performance_analyzer.py # Performance analysis
│   ├── verify_correctness.py  # Correctness verification
│   ├── gprof_profiler.py      # GProf analysis
│   └── complete_benchmark.py  # Complete benchmark suite
│
├── inputs/                     # Test data (generated)
│   ├── keywords.txt           # 200 keywords
│   ├── text_10MB.txt
│   ├── text_100MB.txt
│   └── text_500MB.txt
│
├── results/                    # Results (generated)
│   ├── baseline_results.json
│   └── performance_results.csv
│
└── profiling_results/          # Profiling output
    ├── gprof_*.txt
    ├── roofline_metrics.txt
    └── graphs/

================================================================================
13. RESULTS SUMMARY
================================================================================

SPEEDUP COMPARISON:
+------------------+---------+---------+---------+
| Implementation   | 10MB    | 100MB   | 500MB   |
+------------------+---------+---------+---------+
| Naive            | 1.00x   | 1.00x   | 1.00x   |
| Sequential DFA   | 19.64x  | 15.11x  | 12.34x  |
| SIMD             | 10.22x  | 7.80x   | 8.45x   |
| OpenMP           | 19.07x  | 15.11x  | 14.61x  |
| OpenMP+SIMD      | 21.38x  | 16.12x  | 15.52x  |
| MPI              | 17.53x  | 10.85x  | N/A     |
+------------------+---------+---------+---------+

KEY FINDINGS:
------------
- Best overall: OpenMP+SIMD Hybrid (15-21x speedup)
- Algorithmic improvement: 12-20x (Naive -> Sequential DFA)
- Parallel improvement: 1.2-1.5x (Sequential -> OpenMP+SIMD)
- Optimal threads: 8 (matches physical core count on i5-10310U)
- Bottleneck: Compute-bound (roofline confirmed)
- MPI efficiency: Only 40% CPU utilization on single node

================================================================================
14. LLM USAGE DISCLOSURE
================================================================================

This project used GitHub Copilot and DeepSeek for:

1. Code generation - Initial parallel algorithm implementations
2. Debugging - Identifying off-by-one errors in OpenMP chunking
3. Documentation - Structuring this report and README
4. Profiling - Interpreting perf and gprof output

LIMITATIONS IDENTIFIED:
----------------------
- SIMD Code Hallucination: The LLM initially generated SIMD code that claimed
  unrealistic speedups; this required manual correction

- Parallel Result Verification: The LLM suggested generating separate .txt files
  for each parallel method and matching results across all methods to ensure
  algorithmic correctness

SAMPLE PROMPTS USED:
-------------------
- "Implement OpenMP parallel Aho-Corasick with chunk overlap to catch
   cross-boundary matches"
- "Explain why SIMD overhead exceeds benefits for variable-length pattern
   matching"
- "Generate roofline plot from bandwidth and compute measurements"

================================================================================
15. FUTURE WORK
================================================================================

1. GPU Acceleration with CUDA - Expected 50-100x speedup on 4,000+ cores
2. Two-level DFA for Unicode - Hot/cold state classification for memory
   efficiency (98% memory reduction)
3. Dynamic Pattern Updates - Double-buffer with background rebuild for
   zero-downtime updates
4. Approximate Matching - Edit distance <= 2 for typos and mutations

================================================================================
16. REFERENCES
================================================================================

[1] Aho, A. V., & Corasick, M. J. (1975). Efficient string matching: An aid to
    bibliographic search. Communications of the ACM, 18(6), 333-340.

[2] Knuth, D. E., Morris, J. H., & Pratt, V. R. (1977). Fast pattern matching
    in strings. SIAM journal on computing, 6(2), 323-350.

[3] Amdahl, G. M. (1967). Validity of the single processor approach. AFIPS
    Conference Proceedings, 483-485.

[4] Williams, S., Waterman, A., & Patterson, D. (2009). Roofline: An insightful
    visual performance model for multicore architectures. Communications of the
    ACM, 52(4), 65-76.

================================================================================
17. TEAM
================================================================================

+------------------+------------------+-------------------------------------+
| Name             | ID               | Role                                |
+------------------+------------------+-------------------------------------+
| Ismail           | 23i-2524         | Implementation & Performance        |
|                  |                  | Analysis                            |
| M. Saim          | 23i-0781         | Implementation & Documentation      |
+------------------+------------------+-------------------------------------+

================================================================================
18. LICENSE
================================================================================

This project is licensed under the MIT License.

================================================================================
19. ACKNOWLEDGMENTS
================================================================================

- Dr. [Instructor Name] for guidance on parallel computing concepts
- Aho and Corasick for their foundational paper
- OpenMP, MPI, and GCC communities for excellent tools

================================================================================

Repository: github.com/MIsmail2524/Aho_Corasik_Parallel

Status: Complete - All implementations verified and profiled

================================================================================