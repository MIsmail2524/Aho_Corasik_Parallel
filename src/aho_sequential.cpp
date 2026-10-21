#include "aho_common.h"
#include <fstream>
#include <sstream>

using namespace std;

vector<Match> search_sequential(const AhoCorasick& ac, const string& text) {
    vector<Match> results;
    int state = 0;
    
    for (size_t i = 0; i < text.size(); ++i) {
        state = ac.go(state, (unsigned char)text[i]);
        for (int ki : ac.output[state])
            results.push_back({(int)i, ki});
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
    auto matches = search_sequential(ac, text);
    auto end = chrono::high_resolution_clock::now();
    
    double elapsed_ms = chrono::duration<double, milli>(end - start).count();
    
    cout << "\n=== Sequential Aho-Corasick (Baseline DFA) ===" << endl;
    cout << "Text size : " << text.size() / 1024 / 1024 << " MB" << endl;
    cout << "Keywords  : " << keywords.size() << endl;
    cout << "States    : " << ac.num_states << endl;
    cout << "Time      : " << elapsed_ms << " ms" << endl;
    cout << "Matches   : " << matches.size() << endl;
    cout << "Throughput: " << (text.size() / 1024.0 / 1024.0) / (elapsed_ms / 1000.0) << " MB/s" << endl;
    
    return 0;
}