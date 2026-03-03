#!/usr/bin/env python3
"""
Analyze Cerebras token usage to validate optimizations.

Usage:
    python analyze_cerebras_usage.py org_d4xhyytkf4dxrytcnm25wt5p-2026_03_02-2026_03_03-per_minute-usage.csv
"""

import csv
import sys
from pathlib import Path
from datetime import datetime


def analyze_usage(csv_path: str):
    """Analyze Cerebras token usage from CSV."""
    
    print("🔍 Analyzing Cerebras GLM-4.7 Token Usage...\n")
    print("="*80)
    
    total_requests = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    
    # Track per-request stats
    request_data = []
    minute_data = []
    
    # Configuration limits
    MAX_CONTEXT_TOKENS = 120000  # Our configured limit
    MAX_OUTPUT_TOKENS = 4096     # Our max_tokens setting
    CONTEXT_WINDOW = 131072      # Cerebras actual limit
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            requests = int(row['Requests'])
            input_tokens = int(row['Input Tokens'])
            output_tokens = int(row['Output Tokens'])
            total = int(row['Total Tokens'])
            
            if requests > 0:  # Only count active minutes
                total_requests += requests
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                total_tokens += total
                
                # Track per-minute stats
                minute_data.append({
                    'time': row['Time Start'],
                    'requests': requests,
                    'input': input_tokens,
                    'output': output_tokens,
                    'total': total,
                    'avg_input_per_req': input_tokens / requests if requests > 0 else 0,
                    'avg_output_per_req': output_tokens / requests if requests > 0 else 0,
                })
    
    # Calculate statistics
    avg_input_per_req = total_input_tokens / total_requests if total_requests > 0 else 0
    avg_output_per_req = total_output_tokens / total_requests if total_requests > 0 else 0
    avg_total_per_req = total_tokens / total_requests if total_requests > 0 else 0
    input_output_ratio = total_input_tokens / total_output_tokens if total_output_tokens > 0 else 0
    
    # Find peaks
    max_input_minute = max(minute_data, key=lambda x: x['input']) if minute_data else None
    max_output_minute = max(minute_data, key=lambda x: x['output']) if minute_data else None
    max_requests_minute = max(minute_data, key=lambda x: x['requests']) if minute_data else None
    
    # Check if we're staying within configured limits
    over_context_limit = [m for m in minute_data if m['avg_input_per_req'] > MAX_CONTEXT_TOKENS]
    over_output_limit = [m for m in minute_data if m['avg_output_per_req'] > MAX_OUTPUT_TOKENS]
    
    # Print summary
    print("\n📊 OVERALL STATISTICS")
    print("─" * 80)
    print(f"Total Requests:        {total_requests:,}")
    print(f"Total Input Tokens:    {total_input_tokens:,}")
    print(f"Total Output Tokens:   {total_output_tokens:,}")
    print(f"Total Tokens:          {total_tokens:,}")
    print(f"\nActive Minutes:        {len(minute_data)}")
    
    print("\n📈 AVERAGE PER REQUEST")
    print("─" * 80)
    print(f"Avg Input Tokens:      {avg_input_per_req:,.0f} tokens/request")
    print(f"Avg Output Tokens:     {avg_output_per_req:,.0f} tokens/request")
    print(f"Avg Total Tokens:      {avg_total_per_req:,.0f} tokens/request")
    print(f"Input:Output Ratio:    {input_output_ratio:.1f}:1")
    
    print("\n🎯 OPTIMIZATION VALIDATION")
    print("─" * 80)
    
    # Check context management
    print(f"\n✓ Context Management (max_context_tokens: {MAX_CONTEXT_TOKENS:,})")
    if avg_input_per_req <= MAX_CONTEXT_TOKENS:
        print(f"  ✅ Average input ({avg_input_per_req:,.0f}) is within limit")
    else:
        print(f"  ⚠️  Average input ({avg_input_per_req:,.0f}) EXCEEDS limit")
    
    if over_context_limit:
        print(f"  ⚠️  {len(over_context_limit)} minutes exceeded context limit")
        for minute in over_context_limit[:3]:  # Show first 3
            print(f"     - {minute['time']}: {minute['avg_input_per_req']:,.0f} tokens/req")
    else:
        print(f"  ✅ No minutes exceeded context limit")
    
    # Check output management
    print(f"\n✓ Output Management (max_tokens: {MAX_OUTPUT_TOKENS:,})")
    if avg_output_per_req <= MAX_OUTPUT_TOKENS:
        print(f"  ✅ Average output ({avg_output_per_req:,.0f}) is within limit")
    else:
        print(f"  ⚠️  Average output ({avg_output_per_req:,.0f}) EXCEEDS limit")
    
    if over_output_limit:
        print(f"  ⚠️  {len(over_output_limit)} minutes exceeded output limit")
    else:
        print(f"  ✅ No minutes exceeded output limit")
    
    # Check context window utilization
    print(f"\n✓ Context Window Utilization (total capacity: {CONTEXT_WINDOW:,})")
    if max_input_minute:
        max_single_input = max_input_minute['input']
        utilization = (max_single_input / CONTEXT_WINDOW) * 100
        print(f"  Peak input in 1 minute: {max_single_input:,} tokens ({utilization:.1f}% of capacity)")
        
        if utilization < 50:
            print(f"  ✅ Well below capacity - good headroom")
        elif utilization < 80:
            print(f"  ⚠️  Moderate usage - monitor closely")
        else:
            print(f"  🚨 High usage - approaching limits")
    
    # Efficiency analysis
    print("\n✓ Token Efficiency")
    if input_output_ratio > 10:
        print(f"  ⚠️  High input:output ratio ({input_output_ratio:.1f}:1)")
        print(f"     Context may be bloated or queries are very short")
    elif input_output_ratio > 5:
        print(f"  ⚙️  Moderate ratio ({input_output_ratio:.1f}:1) - typical for long contexts")
    else:
        print(f"  ✅ Good ratio ({input_output_ratio:.1f}:1) - efficient context usage")
    
    print("\n🏆 PEAK USAGE ANALYSIS")
    print("─" * 80)
    
    if max_input_minute:
        print(f"\nPeak Input Minute: {max_input_minute['time']}")
        print(f"  Requests: {max_input_minute['requests']}")
        print(f"  Input Tokens: {max_input_minute['input']:,}")
        print(f"  Avg per request: {max_input_minute['avg_input_per_req']:,.0f}")
    
    if max_output_minute:
        print(f"\nPeak Output Minute: {max_output_minute['time']}")
        print(f"  Requests: {max_output_minute['requests']}")
        print(f"  Output Tokens: {max_output_minute['output']:,}")
        print(f"  Avg per request: {max_output_minute['avg_output_per_req']:,.0f}")
    
    if max_requests_minute:
        print(f"\nPeak Request Minute: {max_requests_minute['time']}")
        print(f"  Requests: {max_requests_minute['requests']}")
        print(f"  Total Tokens: {max_requests_minute['total']:,}")
    
    # Distribution analysis
    print("\n📊 REQUEST DISTRIBUTION")
    print("─" * 80)
    
    # Categorize by input size
    small_input = sum(1 for m in minute_data if m['avg_input_per_req'] < 10000)
    medium_input = sum(1 for m in minute_data if 10000 <= m['avg_input_per_req'] < 50000)
    large_input = sum(1 for m in minute_data if 50000 <= m['avg_input_per_req'] < MAX_CONTEXT_TOKENS)
    xlarge_input = sum(1 for m in minute_data if m['avg_input_per_req'] >= MAX_CONTEXT_TOKENS)
    
    total_active = len(minute_data)
    print(f"\nBy Average Input Size per Request:")
    print(f"  Small (<10K):        {small_input:3d} minutes ({small_input/total_active*100:5.1f}%)")
    print(f"  Medium (10K-50K):    {medium_input:3d} minutes ({medium_input/total_active*100:5.1f}%)")
    print(f"  Large (50K-120K):    {large_input:3d} minutes ({large_input/total_active*100:5.1f}%)")
    print(f"  X-Large (>120K):     {xlarge_input:3d} minutes ({xlarge_input/total_active*100:5.1f}%)")
    
    # Final assessment
    print("\n" + "="*80)
    print("🎯 FINAL ASSESSMENT")
    print("="*80)
    
    issues = 0
    
    if avg_input_per_req > MAX_CONTEXT_TOKENS:
        print("❌ Average input exceeds configured limit - context compression needed")
        issues += 1
    else:
        print("✅ Context management: WORKING")
    
    if avg_output_per_req > MAX_OUTPUT_TOKENS:
        print("❌ Average output exceeds max_tokens setting")
        issues += 1
    else:
        print("✅ Output limiting: WORKING")
    
    if input_output_ratio > 50:
        print("⚠️  Very high input:output ratio - consider more aggressive compression")
        issues += 1
    else:
        print("✅ Token efficiency: ACCEPTABLE")
    
    if xlarge_input > 0:
        print(f"⚠️  {xlarge_input} minutes exceeded context budget - compression may be activating")
    else:
        print("✅ No context budget overruns")
    
    print("\n" + "="*80)
    if issues == 0:
        print("🎉 ALL OPTIMIZATIONS WORKING AS EXPECTED!")
    elif issues <= 2:
        print("⚙️  MOSTLY WORKING - Minor tuning recommended")
    else:
        print("🚨 OPTIMIZATIONS NEED ATTENTION")
    print("="*80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_cerebras_usage.py <csv_file>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"Error: File '{csv_path}' not found")
        sys.exit(1)
    
    analyze_usage(csv_path)
