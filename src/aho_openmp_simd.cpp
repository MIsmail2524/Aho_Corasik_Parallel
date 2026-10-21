#include "aho_common.h"
#include <omp.h>
#include <immintrin.h>
#include <emmintrin.h>
#include <smmintrin.h>

using namespace std;

static void build_first_mask(const vector<string>& kw, uint8_t mask[256]) {
    memset(mask, 0, 256);
    for (const auto& k : kw)
        if (!k.empty()) mask[(unsigned char)k[0]] = 1;
}

static inline int simd_skip(const char* text, int pos, int end,
                              const uint8_t first_mask[256],
                              const vector<uint8_t>& fcs) {
    while (pos < end && ((uintptr_t)(text + pos) & 15) != 0) {
        if (first_mask[(unsigned char)text[pos]]) return pos;
        ++pos;
    }
    
    while (pos + 16 <= end) {
        __m128i chunk = _mm_load_si128((const __m128i*)(text + pos));
        __m128i hit = _mm_setzero_si128();
        for (uint8_t fc : fcs)
            hit = _mm_or_si128(hit, _mm_cmpeq_epi8(chunk, _mm_set1_epi8((char)fc)));
        int bits = _mm_movemask_epi8(hit);
        if (bits) return pos + __builtin_ctz(bits);
        pos += 16;
    }
    
    while (pos < end) {
        if (first_mask[(unsigned char)text[pos]]) return pos;
        ++pos;
    }
    return end;
}

vector<Match> search_openmp_simd(const AhoCorasick& ac, const string& text, int T = 0) {
    if (T <= 0) T = omp_get_max_threads();
    const int n = (int)text.size();
    if (n == 0) return {};
    
    const int overlap = ac.max_keyword_len() - 1;
    int cs = (n + T - 1) / T;
    if (cs < overlap + 1) cs = overlap + 1;
    
    uint8_t first_mask[256];
    build_first_mask(ac.keywords, first_mask);
    
    vector<uint8_t> fcs;
    for (int c = 0; c < 256; ++c)
        if (first_mask[c]) fcs.push_back((uint8_t)c);
    
    vector<vector<Match>> tr(T);
    
    #pragma omp parallel for num_threads(T) schedule(static)
    for (int t = 0; t < T; ++t) {
        int ps = t * cs;
        if (ps >= n) continue;
        int pe = min(ps + cs, n);
        int se = min(pe + overlap, n);
        
        int state = 0;
        int i = ps;
        
        while (i < se) {
            if (state == 0) {
                int next = simd_skip(text.c_str(), i, se, first_mask, fcs);
                if (next == se) break;
                i = next;
            }
            
            state = ac.go(state, (unsigned char)text[i]);
            for (int ki : ac.output[state]) {
                int klen = (int)ac.keywords[ki].size();
                int ms = i - klen + 1;
                if (ms >= ps && ms < pe)
                    tr[t].push_back({i, ki});
            }
            ++i;
        }
    }
    
    vector<Match> results;
    for (auto& b : tr) for (auto& m : b) results.push_back(m);
    sort(results.begin(), results.end(), match_less);
    return results;
}

string read_file(const string& path) {
    ifstream fin(path, ios::binary);
    if (!fin) return "";
    string content((istreambuf_iterator<char>(fin)), istreambuf_iterator<char>());
    return content;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <text_file> <keyword1> ..." << endl;
        return 1;
    }
    
    string text = read_file(argv[1]);
    if (text.empty()) {
        cerr << "Cannot read file: " << argv[1] << endl;
        return 1;
    }
    
    vector<string> keywords;
    for (int i = 2; i < argc; ++i) keywords.push_back(argv[i]);
    
    AhoCorasick ac;
    ac.build(keywords);
    
    int num_threads = omp_get_max_threads();
    
    auto start = chrono::high_resolution_clock::now();
    auto matches = search_openmp_simd(ac, text, num_threads);
    auto end = chrono::high_resolution_clock::now();
    
    double elapsed_ms = chrono::duration<double, milli>(end - start).count();
    
    cout << "\n=== OpenMP+SIMD Hybrid Aho-Corasick ===" << endl;
    cout << "Text size : " << text.size() / 1024 / 1024 << " MB" << endl;
    cout << "Keywords  : " << keywords.size() << endl;
    cout << "Threads   : " << num_threads << endl;
    cout << "Time      : " << elapsed_ms << " ms" << endl;
    cout << "Matches   : " << matches.size() << endl;
    cout << "Throughput: " << (text.size() / 1024.0 / 1024.0) / (elapsed_ms / 1000.0) << " MB/s" << endl;
    
    return 0;
}