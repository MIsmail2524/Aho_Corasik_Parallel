#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cmath>

using namespace std;
using Clock = chrono::high_resolution_clock;

struct PerfMetrics {
    double time_ms;
    double throughput_mb_s;
    double arithmetic_intensity;
    long long data_moved_bytes;
};

PerfMetrics measure_bandwidth(size_t data_size_mb) {
    const size_t N = data_size_mb * 1024 * 1024 / sizeof(double);
    vector<double> a(N), b(N), c(N);
    
    for (size_t i = 0; i < N; ++i) {
        a[i] = 1.0;
        b[i] = 2.0;
    }
    
    auto t0 = Clock::now();
    for (size_t i = 0; i < N; ++i) {
        c[i] = a[i] + b[i];
    }
    auto t1 = Clock::now();
    
    double time_ms = chrono::duration<double, milli>(t1 - t0).count();
    long long bytes_moved = 3 * N * sizeof(double);
    double throughput_mb_s = (bytes_moved / 1e6) / (time_ms / 1000.0);
    
    return {time_ms, throughput_mb_s / 1024.0, throughput_mb_s / 1024.0, bytes_moved};
}

PerfMetrics measure_compute(size_t num_ops) {
    const size_t N = num_ops;
    vector<double> a(N), b(N), c(N);
    
    for (size_t i = 0; i < N; ++i) {
        a[i] = 1.0;
        b[i] = 2.0;
        c[i] = 0.0;
    }
    
    auto t0 = Clock::now();
    for (size_t i = 0; i < N; ++i) {
        c[i] = a[i] * b[i] + c[i];
    }
    auto t1 = Clock::now();
    
    double time_ms = chrono::duration<double, milli>(t1 - t0).count();
    double flops = (2.0 * N) / (time_ms / 1000.0);
    double gflops = flops / 1e9;
    long long bytes_moved = 3 * N * sizeof(double);
    
    return {time_ms, gflops, gflops, bytes_moved};
}

int main() {
    cout << fixed << setprecision(2);
    
    cout << "\n============================================================================\n";
    cout << "ROOFLINE MODEL MEASUREMENT RESULTS\n";
    cout << "============================================================================\n";
    cout << "Timestamp: ";
    auto now = chrono::system_clock::now();
    time_t time_now = chrono::system_clock::to_time_t(now);
    char buffer[100];
    strftime(buffer, 100, "%Y-%m-%d %H:%M:%S", localtime(&time_now));
    cout << buffer << "\n\n";
    
    cout << "BANDWIDTH MEASUREMENTS\n";
    cout << "──────────────────────────────────────────────────────────────────────────\n";
    for (int mb : {10, 50, 100}) {
        auto bw = measure_bandwidth(mb);
        cout << "Data Size: " << setw(3) << mb << " MB | Time: " << setw(8) << bw.time_ms 
             << " ms | Bandwidth: " << setw(7) << bw.throughput_mb_s << " GB/s\n";
    }
    cout << "\n";
    
    cout << "COMPUTE PERFORMANCE (FMA Operations)\n";
    cout << "──────────────────────────────────────────────────────────────────────────\n";
    for (long ops : {10000000, 50000000, 100000000}) {
        auto comp = measure_compute(ops);
        cout << "Operations: " << setw(9) << ops << " | Time: " << setw(8) << comp.time_ms 
             << " ms | GFLOPS: " << setw(7) << comp.throughput_mb_s << "\n";
    }
    cout << "\n";
    
    auto bw = measure_bandwidth(100);
    auto comp = measure_compute(100000000);
    double peak_bandwidth = bw.throughput_mb_s;
    double peak_flops = comp.throughput_mb_s;
    double ridge_point = peak_flops / peak_bandwidth;
    
    cout << "ROOFLINE MODEL PARAMETERS\n";
    cout << "──────────────────────────────────────────────────────────────────────────\n";
    cout << "Peak Bandwidth:  " << peak_bandwidth << " GB/s\n";
    cout << "Peak Compute:    " << peak_flops << " GFLOPS\n";
    cout << "Ridge Point:     " << ridge_point << " FLOPS/byte\n\n";
    
    cout << "INTERPRETATION:\n";
    cout << "──────────────────────────────────────────────────────────────────────────\n";
    cout << "- Applications with intensity < ridge point are MEMORY-BOUND\n";
    cout << "- Applications with intensity > ridge point are COMPUTE-BOUND\n";
    cout << "- Pattern matching: ~1-10 ops/byte → COMPUTE-BOUND\n";
    cout << "\n============================================================================\n";
    
    return 0;
}