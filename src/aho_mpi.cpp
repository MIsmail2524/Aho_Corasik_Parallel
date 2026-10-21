#include "aho_common.h"
using namespace std;

#ifdef USE_MPI
#include <mpi.h>

struct SerializedAC {
    vector<int>  delta;
    vector<int>  output_sizes;
    vector<int>  output_flat;
    vector<int>  kw_lengths;
    vector<char> kw_chars;
    int          num_states;
    int          num_kw;
};

static SerializedAC serialize(const AhoCorasick& ac) {
    SerializedAC s;
    s.num_states = ac.num_states;
    s.num_kw = (int)ac.keywords.size();
    s.delta = ac.delta;
    
    for (const auto& ov : ac.output) {
        s.output_sizes.push_back((int)ov.size());
        for (int ki : ov) s.output_flat.push_back(ki);
    }
    for (const auto& kw : ac.keywords) {
        s.kw_lengths.push_back((int)kw.size());
        for (char c : kw) s.kw_chars.push_back(c);
    }
    return s;
}

static AhoCorasick deserialize(const SerializedAC& s) {
    AhoCorasick ac;
    ac.num_states = s.num_states;
    ac.delta = s.delta;
    ac.output.resize(s.num_states);
    
    int fi = 0;
    for (int st = 0; st < s.num_states; ++st) {
        int sz = s.output_sizes[st];
        for (int j = 0; j < sz; ++j)
            ac.output[st].push_back(s.output_flat[fi++]);
    }
    int ci = 0;
    for (int ki = 0; ki < s.num_kw; ++ki) {
        int len = s.kw_lengths[ki];
        ac.keywords.push_back(string(s.kw_chars.data() + ci, len));
        ci += len;
    }
    return ac;
}

static vector<Match> search_chunk(const AhoCorasick& ac,
                                   const char* chunk, int chunk_len,
                                   int primary_start, int primary_len) {
    vector<Match> results;
    int state = 0;
    int primary_end = primary_start + primary_len;
    
    for (int i = 0; i < chunk_len; ++i) {
        state = ac.go(state, (unsigned char)chunk[i]);
        for (int ki : ac.output[state]) {
            int klen = (int)ac.keywords[ki].size();
            int ms = (primary_start + i) - klen + 1;
            if (ms >= primary_start && ms < primary_end)
                results.push_back({primary_start + i, ki});
        }
    }
    return results;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <text_file> <keyword1> ..." << endl;
        return 1;
    }
    
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    string text;
    vector<string> keywords;
    AhoCorasick ac;
    
    if (rank == 0) {
        ifstream fin(argv[1], ios::binary);
        string content((istreambuf_iterator<char>(fin)), istreambuf_iterator<char>());
        text = content;
        
        for (int i = 2; i < argc; ++i) keywords.push_back(argv[i]);
        
        ac.build(keywords);
    }
    
    int text_len = text.size();
    MPI_Bcast(&text_len, 1, MPI_INT, 0, MPI_COMM_WORLD);
    
    if (rank != 0) text.resize(text_len);
    MPI_Bcast(&text[0], text_len, MPI_CHAR, 0, MPI_COMM_WORLD);
    
    int kw_count = keywords.size();
    MPI_Bcast(&kw_count, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (rank != 0) keywords.resize(kw_count);
    
    for (int i = 0; i < kw_count; ++i) {
        int len = (rank == 0) ? (int)keywords[i].size() : 0;
        MPI_Bcast(&len, 1, MPI_INT, 0, MPI_COMM_WORLD);
        if (rank != 0) keywords[i].resize(len);
        MPI_Bcast(&keywords[i][0], len, MPI_CHAR, 0, MPI_COMM_WORLD);
    }
    
    if (rank != 0) {
        // Broadcast DFA
        int ns, nk;
        MPI_Bcast(&ns, 1, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Bcast(&nk, 1, MPI_INT, 0, MPI_COMM_WORLD);
        
        int delta_sz = ns * 256;
        vector<int> delta(delta_sz);
        MPI_Bcast(delta.data(), delta_sz, MPI_INT, 0, MPI_COMM_WORLD);
        
        vector<int> output_sizes(ns);
        MPI_Bcast(output_sizes.data(), ns, MPI_INT, 0, MPI_COMM_WORLD);
        
        int of_sz = 0;
        MPI_Bcast(&of_sz, 1, MPI_INT, 0, MPI_COMM_WORLD);
        vector<int> output_flat(of_sz);
        MPI_Bcast(output_flat.data(), of_sz, MPI_INT, 0, MPI_COMM_WORLD);
        
        vector<int> kw_lengths(nk);
        MPI_Bcast(kw_lengths.data(), nk, MPI_INT, 0, MPI_COMM_WORLD);
        
        int kc_sz = 0;
        MPI_Bcast(&kc_sz, 1, MPI_INT, 0, MPI_COMM_WORLD);
        vector<char> kw_chars(kc_sz);
        MPI_Bcast(kw_chars.data(), kc_sz, MPI_CHAR, 0, MPI_COMM_WORLD);
        
        SerializedAC sac;
        sac.num_states = ns;
        sac.num_kw = nk;
        sac.delta = delta;
        sac.output_sizes = output_sizes;
        sac.output_flat = output_flat;
        sac.kw_lengths = kw_lengths;
        sac.kw_chars = kw_chars;
        ac = deserialize(sac);
    } else {
        auto sac = serialize(ac);
        int ns = sac.num_states, nk = sac.num_kw;
        MPI_Bcast(&ns, 1, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Bcast(&nk, 1, MPI_INT, 0, MPI_COMM_WORLD);
        
        int delta_sz = sac.delta.size();
        MPI_Bcast(sac.delta.data(), delta_sz, MPI_INT, 0, MPI_COMM_WORLD);
        
        MPI_Bcast(sac.output_sizes.data(), ns, MPI_INT, 0, MPI_COMM_WORLD);
        
        int of_sz = sac.output_flat.size();
        MPI_Bcast(&of_sz, 1, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Bcast(sac.output_flat.data(), of_sz, MPI_INT, 0, MPI_COMM_WORLD);
        
        MPI_Bcast(sac.kw_lengths.data(), nk, MPI_INT, 0, MPI_COMM_WORLD);
        
        int kc_sz = sac.kw_chars.size();
        MPI_Bcast(&kc_sz, 1, MPI_INT, 0, MPI_COMM_WORLD);
        MPI_Bcast(sac.kw_chars.data(), kc_sz, MPI_CHAR, 0, MPI_COMM_WORLD);
    }
    
    int overlap = ac.max_keyword_len() - 1;
    int chunk_size = (text_len + size - 1) / size;
    int ps = rank * chunk_size;
    int pe = min(ps + chunk_size, text_len);
    int se = min(pe + overlap, text_len);
    int recv_len = se - ps;

    vector<char> chunk_buf(recv_len);
    memcpy(chunk_buf.data(), text.data() + ps, recv_len);

    MPI_Barrier(MPI_COMM_WORLD);
    auto start = chrono::high_resolution_clock::now();
    auto local_matches = search_chunk(ac, chunk_buf.data(), recv_len, ps, pe - ps);

    int local_count = local_matches.size();
    vector<int> counts(size);
    MPI_Gather(&local_count, 1, MPI_INT, counts.data(), 1, MPI_INT, 0, MPI_COMM_WORLD);

    vector<Match> all_matches;
    if (rank == 0) {
        int total = 0;
        vector<int> displs(size, 0);
        for (int r = 0; r < size; ++r) {
            displs[r] = total;
            total += counts[r];
        }
        all_matches.resize(total);
        MPI_Gatherv(local_matches.data(), local_count, MPI_2INT,
                    all_matches.data(), counts.data(), displs.data(), MPI_2INT,
                    0, MPI_COMM_WORLD);
        sort(all_matches.begin(), all_matches.end(), match_less);
    } else {
        MPI_Gatherv(local_matches.data(), local_count, MPI_2INT,
                    nullptr, nullptr, nullptr, MPI_2INT, 0, MPI_COMM_WORLD);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    auto end = chrono::high_resolution_clock::now();
    double elapsed_ms = chrono::duration<double, milli>(end - start).count();

    if (rank == 0) {
        cout << "\n=== MPI Aho-Corasick (" << size << " processes) ===" << endl;
        cout << "Text size : " << text_len / 1024 / 1024 << " MB" << endl;
        cout << "Keywords  : " << keywords.size() << endl;
        cout << "Time      : " << elapsed_ms << " ms" << endl;
        cout << "Matches   : " << all_matches.size() << endl;
        cout << "Throughput: " << (text_len / 1024.0 / 1024.0) / (elapsed_ms / 1000.0) << " MB/s" << endl;
    }
    
    MPI_Finalize();
    return 0;
}

#else

int main() {
    cout << "=== MPI Aho-Corasick ===" << endl;
    cout << "This file requires MPI. Compile with:" << endl;
    cout << "  mpicxx -O3 -DUSE_MPI -std=c++17 -o aho_mpi aho_mpi.cpp" << endl;
    cout << "  mpirun -np 2 ./aho_mpi <text_file> <keyword1> ..." << endl;
    return 0;
}

#endif