# Cerebras-GLM-4.7 Optimization Update - March 3, 2026

## 📊 Analysis Results

Based on actual usage data from `org_d4xhyytkf4dxrytcnm25wt5p-2026_03_02-2026_03_03-per_minute-usage.csv`:

### Usage Statistics
- **Total Requests:** 160
- **Total Input Tokens:** 5,470,421
- **Total Output Tokens:** 79,761
- **Average Input per Request:** 34,190 tokens
- **Average Output per Request:** 499 tokens
- **Input:Output Ratio:** 68.6:1 ⚠️

### What Was Working ✅
1. **Context Management:** Average input (34K) well below limit (120K) - 71% headroom
2. **Output Limiting:** Average output (499) well below limit (4K) - 88% headroom
3. **No Overruns:** Zero requests exceeded configured limits
4. **Optimal Distribution:** 73% of requests in 10K-50K token range

### Issue Identified ⚠️
**High Input:Output Ratio (68.6:1)**
- Expected ratio for coding tasks: 5:1 to 20:1
- Actual ratio indicates context bloat
- Cause: Long conversation history accumulating without aggressive compression

---

## 🔧 Applied Optimizations

### 1. More Aggressive Context Compression

**Changed:**
```diff
"context_management": {
-  "max_context_tokens": 120000,
+  "max_context_tokens": 100000,
   "reserve_for_response": 11072,
   "compaction_strategy": "sliding_window",
   "compress_old_messages": true,
-  "min_old_message_tokens": 2048
+  "min_old_message_tokens": 1024
}
```

**Impact:**
- **max_context_tokens:** 120K → 100K (20K reduction)
  - Leaves more headroom for response
  - Triggers compression sooner
  - Reduces context bloat

- **min_old_message_tokens:** 2048 → 1024 (50% reduction)
  - Compression activates 2x sooner
  - Summarizes old messages more aggressively
  - Reduces accumulated context weight

**Expected Result:**
- Input:Output ratio should drop from 68:1 → 20-30:1
- Token usage reduction: ~30% on long conversations
- Cost savings: ~$0.16 per session (~$5/month for 30 sessions)

### 2. Earlier Compression Trigger

**Changed:**
```diff
"optimization_settings": {
   ...
-  "context_compression_threshold": 100000
+  "context_compression_threshold": 80000
}
```

**Impact:**
- Compression now triggers at 80K instead of 100K
- 20K earlier intervention prevents bloat
- Maintains conversation quality while reducing tokens

### 3. Rate Limiting (NEW)

**Added:**
```json
"rate_limit": {
  "max_requests_per_minute": 20,
  "delay_between_requests": 0.5
}
```

**Impact:**
- Prevents burst usage (observed: 29 requests/minute peak)
- Adds 500ms cooldown between requests
- Reduces API server errors from rapid-fire requests
- Protects against the observed 1.3M tokens/minute spike

---

## 📈 Expected Improvements

### Token Usage

| Metric | Before | After (Projected) | Improvement |
|--------|--------|-------------------|-------------|
| Avg Input/Request | 34,190 | ~24,000 | -30% |
| Input:Output Ratio | 68.6:1 | ~25:1 | -64% |
| Max Burst (tokens/min) | 1,330,689 | ~800,000 | -40% |
| Context Bloat | High | Moderate | Significant |

### Cost Savings

```
Current Session Cost:
- Input:  5,470,421 tokens × $0.10/1M = $0.547
- Output:    79,761 tokens × $0.10/1M = $0.008
- Total:                              = $0.555

Projected Session Cost (30% reduction):
- Input:  3,829,295 tokens × $0.10/1M = $0.383
- Output:    79,761 tokens × $0.10/1M = $0.008
- Total:                              = $0.391

Savings per Session: $0.164 (29.5%)
Monthly Savings (30 sessions): ~$5.00
```

### Performance

- ✅ **Faster responses:** Less context to process
- ✅ **Fewer errors:** Rate limiting prevents API overload
- ✅ **Better quality:** Compression removes noise, keeps relevant info
- ✅ **Longer conversations:** More efficient context = more turns possible

---

## 🧪 Testing Recommendations

### Test 1: Long Conversation (Context Compression)
```bash
cd ~/code_puppy-1
uv run python -m code_puppy

# At the prompt:
/model Cerebras-GLM-4.7

# Run 10+ consecutive queries to test compression:
1. Explain Python decorators in detail
2. Now explain metaclasses
3. Explain async/await
4. Explain generators and iterators
5. Explain context managers
6. Explain type hints and generics
7. Explain dataclasses vs Pydantic
8. Explain pytest fixtures
9. Explain FastAPI routing
10. Explain SQLAlchemy ORM
```

**Watch for:**
- Context compression messages in logs
- Compression activating around message 5-6 (earlier than before)
- No "context length exceeded" errors
- Smooth conversation flow

### Test 2: Rate Limiting (Burst Protection)
```bash
# Run rapid-fire requests
# Before: Could send 29/minute
# After: Limited to 20/minute with 500ms delay

# Observe:
# - Requests automatically throttled
# - No server errors from overload
# - Smooth pacing between requests
```

### Test 3: Token Usage Validation
```bash
# After testing session, export new usage CSV
# Run analyzer:
python analyze_cerebras_usage.py <new_csv_file>

# Compare:
# - Input:Output ratio should be ~20-30:1 (down from 68.6:1)
# - Average input should be ~24K (down from 34K)
# - Peak burst should be lower
```

---

## 📊 Before vs After Comparison

### Configuration Changes

| Setting | Before | After | Change |
|---------|--------|-------|--------|
| `max_context_tokens` | 120,000 | 100,000 | -16.7% |
| `min_old_message_tokens` | 2,048 | 1,024 | -50% |
| `context_compression_threshold` | 100,000 | 80,000 | -20% |
| `max_requests_per_minute` | ∞ | 20 | NEW |
| `delay_between_requests` | 0 | 0.5s | NEW |

### Expected Behavior Changes

**Before:**
- ❌ Context accumulated to 34K avg per request
- ❌ Input:Output ratio of 68.6:1
- ❌ Burst of 29 requests/minute possible
- ❌ Peak usage: 1.3M tokens/minute
- ⚠️ Compression activated late (at 2048 old tokens)

**After:**
- ✅ Context compressed more aggressively
- ✅ Input:Output ratio target: 20-30:1
- ✅ Rate limited to 20 requests/minute
- ✅ Peak usage: ~800K tokens/minute
- ✅ Compression activates 2x earlier (at 1024 old tokens)

---

## 🔍 Monitoring

### Key Metrics to Track

1. **Input:Output Ratio**
   - Target: 20-30:1
   - Monitor weekly
   - Alert if > 40:1

2. **Average Input per Request**
   - Target: 20-25K tokens
   - Should decrease by ~30%
   - Alert if > 35K

3. **Peak Burst Usage**
   - Target: < 1M tokens/minute
   - Should be prevented by rate limiting
   - Alert if rate limit is frequently hit

4. **Context Compression Events**
   - Should activate earlier in conversations
   - Monitor frequency
   - Ensure no quality degradation

### How to Monitor

```bash
# Export usage CSV from Cerebras dashboard
# Run analyzer weekly:
python analyze_cerebras_usage.py usage_export.csv

# Compare metrics:
# - Input:Output ratio
# - Average tokens/request
# - Peak usage
```

---

## 🚨 Rollback Plan

If optimizations cause issues:

### Symptoms of Over-Optimization
- Context compression too aggressive (lost important info)
- Rate limiting too restrictive (workflow interrupted)
- Quality degradation in responses

### Quick Rollback

```json
// Restore previous values in models.json:
"context_management": {
  "max_context_tokens": 120000,  // Restore from 100K
  "min_old_message_tokens": 2048  // Restore from 1024
},
"optimization_settings": {
  "context_compression_threshold": 100000  // Restore from 80K
},
"rate_limit": {
  // Remove this block entirely
}
```

### Partial Rollback Options

**If rate limiting too restrictive:**
```json
"rate_limit": {
  "max_requests_per_minute": 30,  // Increase from 20
  "delay_between_requests": 0.25  // Reduce from 0.5s
}
```

**If compression too aggressive:**
```json
"context_management": {
  "max_context_tokens": 110000,  // Middle ground
  "min_old_message_tokens": 1536  // Between 1024 and 2048
}
```

---

## ✅ Validation Checklist

### Post-Update Validation

- [ ] Configuration file updated successfully
- [ ] No JSON syntax errors in models.json
- [ ] Code Puppy launches without errors
- [ ] Cerebras-GLM-4.7 model selectable
- [ ] Test query completes successfully
- [ ] Long conversation (10+ turns) works without errors
- [ ] Context compression activates (check logs)
- [ ] Rate limiting prevents rapid bursts
- [ ] Response quality maintained
- [ ] Token usage analyzer shows improvements

### Success Metrics (After 1 Week)

- [ ] Input:Output ratio < 30:1
- [ ] Average input per request < 25K tokens
- [ ] Zero context overflow errors
- [ ] No rate limit interruptions (or acceptable level)
- [ ] Cost reduction of ~20-30%
- [ ] User satisfaction maintained

---

## 📝 Change Log

### Version 1.1 - March 3, 2026

**Changes:**
- Reduced `max_context_tokens` from 120K → 100K
- Reduced `min_old_message_tokens` from 2048 → 1024
- Reduced `context_compression_threshold` from 100K → 80K
- Added `rate_limit` configuration (20 req/min, 0.5s delay)

**Rationale:**
- Address high Input:Output ratio (68.6:1)
- Prevent burst usage spikes (1.3M tokens/minute observed)
- Improve token efficiency by 30%
- Reduce API errors from rapid requests

**Based on:**
- Actual usage analysis from March 2-3, 2026
- 160 requests analyzed
- 5.5M tokens processed

---

## 🔗 Related Files

- `models.json` - Updated configuration
- `analyze_cerebras_usage.py` - Token usage analyzer
- `CEREBRAS-GLM-4.7-OPTIMIZATION-VALIDATION.md` - Initial optimization docs
- `cerebras_retry_config.md` - Retry configuration guide

---

## 📧 Support

If you experience issues after this update:

1. Check logs for compression events
2. Run usage analyzer to compare metrics
3. Try partial rollback if needed
4. Review validation checklist
5. Consider adjusting thresholds incrementally

**Remember:** These are aggressive optimizations. Monitor closely for the first week and adjust as needed!
