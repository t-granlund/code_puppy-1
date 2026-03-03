# Cerebras API Retry Configuration

## Issue
Cerebras API occasionally returns `"Encountered a server error, please try again"` during long conversations.

## Solution: Add Retry Logic

### Option 1: Environment-based Retry

Add to your `.env`:
```bash
# Cerebras-specific retry settings
CEREBRAS_MAX_RETRIES=3
CEREBRAS_RETRY_DELAY=2
```

### Option 2: Model Config Enhancement

Update `models.json` for Cerebras-GLM-4.7:
```json
"Cerebras-GLM-4.7": {
  "type": "cerebras",
  "name": "zai-glm-4.7",
  "custom_endpoint": {
    "url": "https://api.cerebras.ai/v1",
    "api_key": "$CEREBRAS_API_KEY"
  },
  "context_length": 131072,
  "max_tokens": 4096,
  "supported_settings": ["temperature", "seed", "top_p", "top_k", "repetition_penalty"],
  "optimization_settings": {
    "enable_streaming": true,
    "use_kv_cache": true,
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "repetition_penalty": 1.0,
    "context_compression_threshold": 100000
  },
  "context_management": {
    "max_context_tokens": 120000,
    "reserve_for_response": 11072,
    "compaction_strategy": "sliding_window",
    "compress_old_messages": true,
    "min_old_message_tokens": 2048
  },
  "retry_config": {
    "max_retries": 3,
    "retry_delay": 2,
    "backoff_multiplier": 1.5,
    "retry_on_errors": ["server_error", "timeout", "rate_limit"]
  }
}
```

### Option 3: Rate Limiting

If errors persist, add rate limiting:
```json
"rate_limit_config": {
  "requests_per_minute": 20,
  "tokens_per_minute": 100000,
  "delay_between_requests": 1.0
}
```

## Testing Recovery

```bash
# Test with the same long conversation
cd /Users/tygranlund/code_puppy-1
uv run python -m code_puppy

# At the prompt:
/model Cerebras-GLM-4.7

# Run 5+ consecutive heavy queries:
# 1. Explain Python decorators in detail
# 2. Now explain metaclasses  
# 3. Explain async/await
# 4. Explain generators and iterators
# 5. Explain context managers
# 6. Explain type hints and generics
```

## Expected Behavior

With retry logic:
- First attempt fails with server error
- Automatic retry after 2s delay
- Second attempt succeeds
- User sees seamless experience

Without retry:
- User sees error message
- Must manually re-submit query
- Disrupts conversation flow
