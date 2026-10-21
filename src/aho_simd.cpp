#include "aho_common.h"
#include <immintrin.h>
#include <emmintrin.h>
#include <smmintrin.h>

using namespace std;

static void build_first_mask(const vector<string>& kw, uint8_t first_mask[256]) {
    memset(first_mask, 0, 256);
    for (const auto& k : kw)
        if (!k.empty()) first_mask[(unsigned char)k[0]] = 1;
}

static int simd_find_first(const char* text, int start, int end,
                            const uint8_t first_mask[256]) {
    vector<uint8_t> fcs;
    for (int c = 0; c < 256; ++c)
        if (first_mask[c]) fcs.push_back((uint8_t)c);
    
    // Scalar prologue: align to 16-byte boundary
    while (start < end && ((uintptr_t)(text + start) & 15) != 0) {
        if (first_mask[(unsigned char)text[start]]) return start;
        ++start;
    }
    
    // SIMD body
    while (start + 16 <= end) {
        __m128i chunk = _mm_load_si128((const __m128i*)(text + start));
        __m128i mask = _mm_setzero_si128();
        
        for (uint8_t fc : fcs) {
            __m128i cmp = _mm_cmpeq_epi8(chunk, _mm_set1_epi8((char)fc));
            mask = _mm_or_si128(mask, cmp);
        }
        
        int bits = _mm_movemask_epi8(mask);
        if (bits) {
            int off = __builtin_ctz(bits);
            return start + off;
        }
        start += 16;
    }
    
    // Scalar epilogue
    while (start < end) {
        if (first_mask[(unsigned char)text[start]]) return start;
        ++start;
    }
    return end;
}

vector<Match> search_simd(const AhoCorasick& ac, const string& text) {
    vector<Match> results;
    const int n = (int)text.size();
    if (n == 0) return results;
    
    uint8_t first_mask[256];
    build_first_mask(ac.keywords, first_mask);
    
    int state = 0;
    int i = 0;
    
    while (i < n) {
        if (state == 0) {
            int next = simd_find_first(text.c_str(), i, n, first_mask);
            if (next == n) break;
            i = next;
        }
        
        state = ac.go(state, (unsigned char)text[i]);
        for (int ki : ac.output[state])
            results.push_back({i, ki});
        ++i;
    }
    
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
    
    auto start = chrono::high_resolution_clock::now();
    auto matches = search_simd(ac, text);
    auto end = chrono::high_resolution_clock::now();
    
    double elapsed_ms = chrono::duration<double, milli>(end - start).count();
    
    cout << "\n=== SIMD Aho-Corasick (SSE2/SSE4.1) ===" << endl;
    cout << "Text size : " << text.size() / 1024 / 1024 << " MB" << endl;
    cout << "Keywords  : " << keywords.size() << endl;
    cout << "Time      : " << elapsed_ms << " ms" << endl;
    cout << "Matches   : " << matches.size() << endl;
    cout << "Throughput: " << (text.size() / 1024.0 / 1024.0) / (elapsed_ms / 1000.0) << " MB/s" << endl;
    
    return 0;
}