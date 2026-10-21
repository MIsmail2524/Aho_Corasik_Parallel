#include "aho_common.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <chrono>
#include <algorithm>

using namespace std;

string read_file(const string& path) {
    ifstream fin(path, ios::binary);
    if (!fin) {
        cerr << "Cannot open: " << path << endl;
        return "";
    }
    string content((istreambuf_iterator<char>(fin)), istreambuf_iterator<char>());
    return content;
}

vector<Match> search_naive(const string& text, const vector<string>& keywords) {
    vector<Match> matches;
    int n = text.size();
    
    for (int kid = 0; kid < (int)keywords.size(); kid++) {
        const string& kw = keywords[kid];
        int m = kw.size();
        
        if (m == 0 || m > n) continue;
        
        for (int i = 0; i + m <= n; i++) {
            bool found = true;
            for (int j = 0; j < m; j++) {
                if (text[i + j] != kw[j]) {
                    found = false;
                    break;
                }
            }
            if (found) {
                matches.push_back({i + m - 1, kid});
            }
        }
    }
    
    sort(matches.begin(), matches.end(), match_less);
    return matches;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <text_file> <keyword1> [keyword2 ...]" << endl;
        return 1;
    }
    
    string text = read_file(argv[1]);
    if (text.empty()) {
        cerr << "Error: Could not read text file" << endl;
        return 1;
    }
    
    vector<string> keywords;
    for (int i = 2; i < argc; i++) {
        keywords.push_back(argv[i]);
    }
    
    cout << "\n=== Naive Multi-pattern Search ===" << endl;
    cout << "Text size : " << text.size() / 1024 / 1024 << " MB (" << text.size() << " bytes)" << endl;
    cout << "Keywords  : " << keywords.size() << endl;
    
    auto start = chrono::high_resolution_clock::now();
    vector<Match> matches = search_naive(text, keywords);
    auto end = chrono::high_resolution_clock::now();
    
    double elapsed_ms = chrono::duration<double, milli>(end - start).count();
    double throughput = (text.size() / 1024.0 / 1024.0) / (elapsed_ms / 1000.0);
    
    cout << "Time      : " << elapsed_ms << " ms" << endl;
    cout << "Matches   : " << matches.size() << endl;
    cout << "Throughput: " << throughput << " MB/s" << endl;
    
    if (!matches.empty()) {
        cout << "\nFirst 10 matches:" << endl;
        for (int i = 0; i < min(10, (int)matches.size()); i++) {
            int start_pos = matches[i].pos - keywords[matches[i].keyword].size() + 1;
            cout << "  Keyword '" << keywords[matches[i].keyword] 
                 << "' at positions " << start_pos << "-" << matches[i].pos << endl;
        }
    }
    
    return 0;
}