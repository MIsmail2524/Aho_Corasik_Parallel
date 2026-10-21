#!/usr/bin/env python3
"""
Generate text files with 200 keywords embedded - ENSURES ALL keywords are inserted
"""

import random
import os
import sys

# Target match counts from your report
TARGET_MATCHES = {
    10: 1_126_838,
    100: 11_243_959,
    500: 56_240_534
}

def generate_keywords(count=200):
    """Generate keyword0 to keyword199"""
    keywords = [f"keyword{i}" for i in range(count)]
    
    with open("inputs/keywords.txt", 'w') as f:
        for kw in keywords:
            f.write(f"{kw}\n")
    
    print(f"✅ Generated {len(keywords)} keywords")
    return keywords

def generate_text_file(size_mb, filename, keywords):
    """
    Generate text file with EXACT target number of keyword occurrences
    """
    target_total = TARGET_MATCHES[size_mb]
    num_keywords = len(keywords)
    
    # Calculate occurrences per keyword
    per_keyword = target_total // num_keywords
    remainder = target_total % num_keywords
    
    print(f"  Target: {target_total:,} total matches")
    print(f"  Each keyword: {per_keyword} times + {remainder} extras")
    
    # Create insertion pool with ALL required keyword occurrences
    insertion_pool = []
    for kw in keywords:
        insertion_pool.extend([kw] * per_keyword)
    
    # Add remainder keywords
    for i in range(remainder):
        insertion_pool.append(keywords[i])
    
    # Shuffle to distribute randomly
    random.shuffle(insertion_pool)
    
    print(f"  Total keywords to insert: {len(insertion_pool):,}")
    
    filler_words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what"
    ]
    
    chars = "abcdefghijklmnopqrstuvwxyz "
    target_bytes = size_mb * 1024 * 1024
    
    # First, write ALL keywords to ensure they all appear
    with open(filename, 'w') as f:
        # Write all keywords first (guarantees they appear)
        print(f"  Writing all {len(insertion_pool):,} keywords...")
        
        # Write keywords in batches to avoid memory issues
        batch_size = 10000
        for i in range(0, len(insertion_pool), batch_size):
            batch = insertion_pool[i:i+batch_size]
            f.write(" ".join(batch) + " ")
        
        written = sum(len(kw) + 1 for kw in insertion_pool)  # +1 for space
        
        print(f"  Keywords written: {written:,} bytes")
        
        # Now fill the rest with filler text to reach target size
        print(f"  Adding filler to reach {target_bytes:,} bytes...")
        
        while written < target_bytes:
            # Write filler word
            if random.random() < 0.7:
                word = random.choice(filler_words)
                f.write(word + " ")
                written += len(word) + 1
            else:
                # Write random characters
                chunk_size = min(1024, target_bytes - written)
                chunk = ''.join(random.choices(chars, k=chunk_size))
                f.write(chunk)
                written += chunk_size
            
            # Add newlines occasionally
            if random.random() < 0.05:
                f.write("\n")
                written += 1
        
        f.write("\n")
    
    # Verify matches
    print(f"\n  Verifying {filename}...")
    with open(filename, 'r') as f:
        content = f.read()
    
    actual_matches = sum(content.count(kw) for kw in keywords)
    percentage = (actual_matches / target_total) * 100
    
    print(f"  Actual matches: {actual_matches:,} ({percentage:.1f}% of target)")
    
    if actual_matches < target_total * 0.95:
        print(f"  ⚠️ WARNING: Only achieved {percentage:.1f}% of target!")
        print(f"  Expected: {target_total:,}, Got: {actual_matches:,}")
        print(f"  Difference: {target_total - actual_matches:,} missing")
    else:
        print(f"  ✅ Success! Achieved {percentage:.1f}% of target")
    
    return actual_matches

def main():
    os.makedirs("inputs", exist_ok=True)
    
    print("\n" + "="*60)
    print("📁 GENERATING TEXT FILES WITH TARGET MATCH COUNTS")
    print("="*60)
    
    # Generate 200 keywords
    keywords = generate_keywords(200)
    print(f"  Keywords: {keywords[:5]}... to {keywords[-5:]}")
    
    # Generate text files
    datasets = [
        (10, "inputs/text_10MB.txt"),
        (100, "inputs/text_100MB.txt"),
        (500, "inputs/text_500MB.txt"),
    ]
    
    results = {}
    
    for size_mb, filename in datasets:
        print(f"\n{'─'*50}")
        print(f"📁 {size_mb}MB file: {filename}")
        print(f"{'─'*50}")
        
        # Delete old file if exists
        if os.path.exists(filename):
            os.remove(filename)
        
        actual = generate_text_file(size_mb, filename, keywords)
        results[size_mb] = actual
        
        file_size = os.path.getsize(filename) / (1024*1024)
        print(f"  Final file size: {file_size:.1f} MB")
    
    # Summary
    print("\n" + "="*60)
    print("✅ DATA GENERATION COMPLETE!")
    print("="*60)
    print("\n📊 Summary:")
    all_good = True
    for size_mb, actual in results.items():
        target = TARGET_MATCHES[size_mb]
        percentage = (actual / target) * 100
        status = "✅" if actual >= target * 0.95 else "❌"
        if actual < target * 0.95:
            all_good = False
        print(f"  {size_mb}MB: {actual:>12,} / {target:>12,} matches ({percentage:.1f}%) {status}")
    
    if not all_good:
        print("\n⚠️ WARNING: Match counts are still low!")
        print("   The issue may be that the text file size is too small to fit all keywords.")
        print("   Try generating smaller target matches or larger file size.")
    
    print("\n🚀 Next steps:")
    print("  make clean && make all")
    print("  make baseline")
    print("  make analyze")

if __name__ == "__main__":
    sys.exit(main())