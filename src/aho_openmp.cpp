#include "aho_common.h"
#include <omp.h>

using namespace std;

vector<Match> search_openmp(const AhoCorasick& ac, const string& text, int T = 0) {
    if (T <= 0) T = omp_get_max_threads();
    
    const int n = (int)text.size();
    if (n == 0) return {};
    
    const int overlap = ac.max_keyword_len() - 1;
    int cs = (n + T - 1) / T;
    if (cs < overlap + 1) cs = overlap + 1;
    
    vector<vector<Match>> tr(T);
    
    #pragma omp parallel for num_threads(T) schedule(static)
    for (int t = 0; t < T; ++t) {
        int ps = t * cs;
        if (ps >= n) continue;
        
        int pe = min(ps + cs, n);
        int se = min(pe + overlap, n);
        
        int state = 0;
        for (int i = ps; i < se; ++i) {
            state = ac.go(state, (unsigned char)text[i]);
            for (int ki : ac.output[state]) {
                int klen = (int)ac.keywords[ki].size();
                int ms = i - klen + 1;
                if (ms >= ps && ms < pe)
                    tr[t].push_back({i, ki});
            }
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
    auto matches = search_openmp(ac, text, num_threads);
    auto end = chrono::high_resolution_clock::now();
    
    double elapsed_ms = chrono::duration<double, milli>(end - start).count();
    
    cout << "\n=== OpenMP Aho-Corasick ===" << endl;
    cout << "Text size : " << text.size() / 1024 / 1024 << " MB" << endl;
    cout << "Keywords  : " << keywords.size() << endl;
    cout << "Threads   : " << num_threads << endl;
    cout << "Time      : " << elapsed_ms << " ms" << endl;
    cout << "Matches   : " << matches.size() << endl;
    cout << "Throughput: " << (text.size() / 1024.0 / 1024.0) / (elapsed_ms / 1000.0) << " MB/s" << endl;
    
    return 0;
}