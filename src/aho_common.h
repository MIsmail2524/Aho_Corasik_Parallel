/*
 * =============================================================================
 * aho_common.h — Shared types, DFA builder, and utilities
 * =============================================================================
 * Base Paper: "Efficient String Matching: An Aid to Bibliographic Search"
 *             Alfred V. Aho & Margaret J. Corasick, ACM 1975
 *
 * This header is included by ALL implementation variants
 * =============================================================================
 */

#pragma once

#include <iostream>
#include <iomanip>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <queue>
#include <algorithm>
#include <chrono>
#include <cassert>
#include <cstring>
#include <numeric>

// Constants
static const int ALPHA     = 256;
static const int FAIL      = -1;

// Match structure
struct Match {
    int pos;
    int keyword;
};

inline bool match_less(const Match& a, const Match& b) {
    return a.pos != b.pos ? a.pos < b.pos : a.keyword < b.keyword;
}

inline bool matches_equal(const std::vector<Match>& a,
                           const std::vector<Match>& b) {
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i)
        if (a[i].pos != b[i].pos || a[i].keyword != b[i].keyword) return false;
    return true;
}

// Timing helpers
using Clock     = std::chrono::high_resolution_clock;
using Ms        = std::chrono::duration<double, std::milli>;

inline double elapsed_ms(Clock::time_point t0, Clock::time_point t1) {
    return Ms(t1 - t0).count();
}

// AhoCorasick DFA builder
struct AhoCorasick {
    std::vector<int>              delta;
    std::vector<std::vector<int>> output;
    std::vector<std::string>      keywords;
    int                           num_states = 0;

    inline int& go(int s, int c)       { return delta[s * ALPHA + c]; }
    inline int  go(int s, int c) const { return delta[s * ALPHA + c]; }

    int new_state() {
        int id = num_states++;
        delta.insert(delta.end(), ALPHA, FAIL);
        output.push_back({});
        return id;
    }

    void build_goto() {
        for (size_t ki = 0; ki < keywords.size(); ++ki) {
            int state = 0;
            for (unsigned char c : keywords[ki]) {
                if (go(state, c) == FAIL) go(state, c) = new_state();
                state = go(state, c);
            }
            output[state].push_back(ki);
        }
        for (int c = 0; c < ALPHA; ++c)
            if (go(0, c) == FAIL) go(0, c) = 0;
    }

    void build_failure(std::vector<int>& fail_fn) {
        fail_fn.assign(num_states, 0);
        std::queue<int> q;

        for (int c = 0; c < ALPHA; ++c) {
            int s = go(0, c);
            if (s != 0) { fail_fn[s] = 0; q.push(s); }
        }
        while (!q.empty()) {
            int r = q.front(); q.pop();
            for (int c = 0; c < ALPHA; ++c) {
                int s = go(r, c);
                if (s == FAIL) continue;
                q.push(s);
                int state = fail_fn[r];
                while (go(state, c) == FAIL) state = fail_fn[state];
                fail_fn[s] = go(state, c);
                for (int ki : output[fail_fn[s]])
                    output[s].push_back(ki);
            }
        }
    }

    void build_dfa(const std::vector<int>& fail_fn) {
        std::queue<int> q;
        for (int c = 0; c < ALPHA; ++c)
            if (go(0, c) != 0) q.push(go(0, c));

        while (!q.empty()) {
            int r = q.front(); q.pop();
            for (int c = 0; c < ALPHA; ++c) {
                if (go(r, c) == FAIL)
                    go(r, c) = go(fail_fn[r], c);
                else
                    q.push(go(r, c));
            }
        }
    }

    void build(const std::vector<std::string>& kw) {
        keywords   = kw;
        num_states = 0;
        delta.clear();
        output.clear();

        new_state();
        build_goto();

        std::vector<int> fail_fn;
        build_failure(fail_fn);
        build_dfa(fail_fn);
    }

    int max_keyword_len() const {
        int m = 0;
        for (const auto& kw : keywords) m = std::max(m, (int)kw.size());
        return m;
    }

    const int* raw_delta() const { return delta.data(); }
};

// Helper functions
inline std::string generate_text(int bytes) {
    const std::string base =
        "abcdefghijklmnopqrstuvwxyz "
        "she said he had his hers here the and of in ";
    std::string txt;
    txt.reserve(bytes);
    while ((int)txt.size() < bytes) txt += base;
    txt.resize(bytes);
    return txt;
}

inline std::vector<std::string> default_keywords() {
    return {"he", "she", "his", "hers", "here", "said", "the", "and"};
}

inline void print_matches(const std::vector<Match>& M,
                           const std::vector<std::string>& kw,
                           const std::string& label,
                           int limit = 20) {
    std::cout << "\n[" << label << "]  " << M.size() << " match(es)";
    if ((int)M.size() > limit) std::cout << "  (showing first " << limit << ")";
    std::cout << ":\n";
    int show = std::min((int)M.size(), limit);
    for (int i = 0; i < show; ++i) {
        int start = M[i].pos - (int)kw[M[i].keyword].size() + 1;
        std::cout << "  start=" << std::setw(7) << start
                  << "  end="   << std::setw(7) << M[i].pos
                  << "  kw=\""  << kw[M[i].keyword] << "\"\n";
    }
}

inline bool extract_dump_matches_flag(int argc, char* argv[], std::vector<std::string>& args) {
    bool dump = false;
    args.clear();
    args.reserve(argc);
    for (int i = 0; i < argc; ++i) {
        std::string arg(argv[i]);
        if (arg == "--dump-matches") {
            dump = true;
        } else {
            args.push_back(arg);
        }
    }
    return dump;
}

inline void print_match_dump(const std::vector<Match>& M,
                             const std::vector<std::string>& kw) {
    std::cout << "MATCHES_START\n";
    for (const auto& m : M) {
        int end = m.pos;
        int start = end - (int)kw[m.keyword].size() + 1;
        std::cout << "MATCH " << m.keyword << " " << start << " " << end << " " << kw[m.keyword] << "\n";
    }
    std::cout << "MATCHES_END\n";
}

struct PerfRow {
    std::string label;
    double      time_ms;
    int         threads;
    size_t      matches;
    bool        correct;
};

inline void print_perf_table(const std::vector<PerfRow>& rows,
                              double seq_ms) {
    std::cout << "\n";
    std::cout << std::left  << std::setw(28) << "Implementation"
              << std::right << std::setw(10) << "Time(ms)"
              << std::setw(8)  << "Thrds"
              << std::setw(10) << "Speedup"
              << std::setw(12) << "Efficiency"
              << std::setw(10) << "Matches"
              << std::setw(10) << "Correct"
              << "\n";
    std::cout << std::string(88, '-') << "\n";

    for (const auto& r : rows) {
        double su  = seq_ms / r.time_ms;
        double eff = (r.threads > 0) ? (su / r.threads * 100.0) : 0.0;
        std::cout << std::left  << std::setw(28) << r.label
                  << std::right << std::setw(10) << std::fixed << std::setprecision(2) << r.time_ms
                  << std::setw(8)  << r.threads
                  << std::setw(10) << std::setprecision(2) << su
                  << std::setw(11) << std::setprecision(1) << eff << "%"
                  << std::setw(10) << r.matches
                  << std::setw(10) << (r.correct ? "PASS ✓" : "FAIL ✗")
                  << "\n";
    }
    std::cout << std::string(88, '-') << "\n";
}