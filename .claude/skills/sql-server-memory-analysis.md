---
name: sql-server-memory-analysis
description: Analyze SQL Server memory health, diagnose memory pressure, and determine if more memory is needed
---

# SQL Server Memory Analysis

Analyze SQL Server memory health, diagnose memory pressure issues, and determine if the server needs more memory.

## When to Use This Skill

Invoke this skill when the user asks to:
- "Check SQL Server memory"
- "Does SQL Server need more memory?"
- "Analyze memory pressure"
- "Check Page Life Expectancy" or "Check PLE"
- "Are there memory issues?"
- "Memory health check"
- "Why is memory low?"
- "Diagnose memory problems"
- "Memory grants pending"

## Workflow

Execute the following steps in order:

### 1. Get Memory Statistics

Call the `get_memory_stats` MCP tool from the SQL Server Doctor server to retrieve:
- Page Life Expectancy (PLE) metrics
- Memory grants pending
- Target vs actual memory allocation
- Buffer pool statistics
- Overall memory health assessment

**This is the PRIMARY tool for memory analysis - start here and only proceed to other tools if specifically needed.**

### 2. Interpret Memory Metrics

Analyze each key metric from the results:

#### Page Life Expectancy (PLE)
- **What it measures**: How long data pages stay in memory (buffer pool) before being removed
- **Status levels**:
  - `CRITICAL` (< 300 seconds / 5 minutes): Severe memory pressure - pages being removed very quickly
  - `WARNING` (300-1000 seconds): Moderate memory pressure - suboptimal but not critical
  - `OK` (≥ 1000 seconds): Healthy - pages staying in memory long enough
- **What it means**: Low PLE indicates SQL Server is constantly reading from disk because memory is insufficient

#### Memory Grants Pending
- **What it measures**: Number of queries waiting for memory to be allocated before they can execute
- **Status levels**:
  - `CRITICAL`: Any value > 0 means queries are stuck waiting for memory
  - `OK`: 0 queries waiting
- **What it means**: If > 0, SQL Server doesn't have enough memory to run queries - this is a severe issue

#### Memory Pressure Status
- **What it measures**: Gap between how much memory SQL Server wants (`target_memory_mb`) vs what it has (`total_memory_mb`)
- **Status levels**:
  - `UNDER_PRESSURE`: Difference > 1024 MB (1 GB) - SQL Server wants significantly more memory
  - `WATCH`: Difference 512-1024 MB - Minor pressure, worth monitoring
  - `OK`: Difference < 512 MB - SQL Server has what it needs
- **What it means**: Large gap indicates SQL Server is artificially constrained by max memory setting or physical RAM limits

#### Buffer Pool Statistics
- **`buffer_pool_committed_mb`**: Memory currently allocated to buffer pool
- **`buffer_pool_target_mb`**: Memory buffer pool wants to allocate
- **Max Server Memory**: Configured limit for SQL Server memory usage

### 3. Determine Root Cause

Based on the metrics, identify the primary issue:

**Scenario A: Need More Physical Memory**
- Low PLE (< 1000s) AND memory pressure status is OK or WATCH
- SQL Server has reached its configured max memory limit
- Target and total memory are close
- **Conclusion**: Server needs more physical RAM

**Scenario B: Max Memory Too Low**
- Low PLE AND memory pressure status is UNDER_PRESSURE
- Large gap between target and total memory (> 1 GB)
- Max server memory setting is limiting SQL Server
- **Conclusion**: Increase max server memory configuration (if physical RAM available)

**Scenario C: Memory Grants Bottleneck**
- Memory grants pending > 0
- Could be due to large queries consuming all available memory
- Check if max server memory is set too low
- **Conclusion**: Either increase memory or optimize queries requesting large memory grants

**Scenario D: Healthy Memory**
- PLE > 1000s
- No memory grants pending
- Memory pressure OK
- **Conclusion**: Memory is healthy, no action needed

### 4. Provide Recommendations

Based on root cause, provide clear, actionable recommendations:

**For Physical Memory Needs:**
```
SQL Server needs more physical memory:
- Current PLE: {ple_seconds}s indicates data is being constantly evicted
- Max memory is set to {max_server_memory_mb} MB and SQL has reached this limit
- Recommendation: Add more physical RAM to the server
- Target: Aim for PLE > 1000 seconds for healthy performance
```

**For Max Memory Configuration:**
```
Max memory setting is too restrictive:
- SQL Server wants {target_memory_mb} MB but only has {total_memory_mb} MB
- Gap: {memory_difference_mb} MB
- Current max memory: {max_server_memory_mb} MB
- Recommendation: Increase max server memory setting
- Suggested value: {calculated_recommendation} MB
  (Leave 4-8 GB for OS depending on server size)
```

**For Memory Grants Issue:**
```
Queries are waiting for memory grants:
- {memory_grants_pending} queries currently waiting
- This is CRITICAL - queries cannot execute until memory is available
- Immediate actions:
  1. Check for large queries consuming memory
  2. Consider increasing max server memory if headroom exists
  3. Investigate query plans for excessive memory requests
```

### 5. When to Call Additional Tools

**Only call other tools if:**

- User explicitly asks about configurations: Call `get_server_configurations` to review max memory setting
- User asks "what's causing the memory issue?": Call `get_active_sessions` to see which queries are consuming memory
- User mentions performance AND memory: You may combine with workload analysis

**Do NOT automatically call:**
- `get_scheduler_stats` - Not relevant for memory analysis
- `get_active_sessions` - Only if user asks about current queries
- `get_server_configurations` - Only if discussing max memory configuration changes
- `get_server_version` - Not relevant unless user asks

### 6. Summary

Provide a concise summary:
- Overall memory health status
- Primary concern (if any)
- Whether more physical memory is needed or configuration adjustment
- Severity level (OK, WARNING, CRITICAL)
- Recommended next steps

## Important Notes

- **Start with `get_memory_stats` ONLY** - do not call multiple tools unless specifically relevant
- **Focus on memory metrics** - avoid discussing CPU, I/O, or other resources unless user asks
- **Be clear about physical RAM vs configuration** - users often confuse these
- **Explain PLE in simple terms** - "how long data stays in memory"
- **Distinguish between needing more RAM vs needing configuration changes**
- Do NOT execute configuration changes - only provide recommendations
- If memory is healthy, say so clearly and briefly - don't over-analyze
- Consider that PLE can be misleading immediately after restart (low PLE is normal then)

## Memory Health Decision Tree

```
Start with get_memory_stats
         ↓
    PLE < 300s? ────Yes───→ CRITICAL memory pressure
         ↓                         ↓
         No                   Check memory_pressure_status
         ↓                         ↓
    PLE < 1000s? ───Yes───→ WARNING: Monitor         UNDER_PRESSURE?
         ↓                         ↓                       ↓
         No                   Need more RAM         Yes: Increase max_memory
         ↓                                               ↓
    Grants > 0? ────Yes───→ CRITICAL: Queries waiting    No: Need more physical RAM
         ↓
         No
         ↓
    Memory is OK ✓
```

## Example Output Format

```
# SQL Server Memory Health Analysis

## Memory Metrics Summary
- **Page Life Expectancy (PLE)**: 250 seconds (🔴 CRITICAL)
- **Memory Grants Pending**: 0 (✅ OK)
- **Memory Pressure**: UNDER_PRESSURE (⚠️ WARNING)
- **Target Memory**: 18,432 MB
- **Total Memory**: 16,384 MB
- **Memory Gap**: 2,048 MB (2 GB)
- **Max Server Memory**: 16,384 MB
- **Overall Assessment**: ⚠️ WARNING - SQL Server wants more memory

## Analysis

### Page Life Expectancy is Critically Low
Your PLE of **250 seconds** (4.2 minutes) indicates severe memory pressure. Data pages are being removed from memory very quickly, forcing SQL Server to constantly read from disk. This significantly impacts performance.

**Healthy PLE Target**: > 1000 seconds (16+ minutes)

### Memory Pressure Detected
SQL Server wants **2 GB more memory** than it currently has available:
- Target: 18,432 MB (what SQL wants)
- Allocated: 16,384 MB (what SQL has)
- Gap: 2,048 MB

### Root Cause
Your max server memory is set to **16,384 MB** which limits SQL Server's memory usage. SQL Server has reached this limit and cannot allocate more memory, even though it needs it.

## Recommendations

### Option 1: Increase Max Server Memory (If Physical RAM Available)
If your server has more than 16 GB of physical RAM:

1. Check available physical RAM on the server
2. Calculate new max memory: (Total RAM - 4-8 GB for OS)
3. Increase max server memory setting:
   ```sql
   -- Example if server has 32 GB total RAM
   EXEC sp_configure 'max server memory (MB)', 28672;
   RECONFIGURE;
   ```

### Option 2: Add Physical Memory (If Already at RAM Limit)
If 16 GB is all the physical RAM available:
- SQL Server needs more physical memory
- Consider upgrading server RAM
- Target: At least 24-32 GB for this workload based on memory pressure

### Priority Actions
1. **Immediate**: Check physical RAM availability on the server
2. **If RAM available**: Increase max server memory configuration
3. **If no RAM available**: Plan for hardware upgrade
4. **Monitor**: PLE should improve to > 1000s after changes

## Expected Outcome
After increasing available memory (either through configuration or hardware):
- PLE should rise to > 1000 seconds
- Memory pressure status should change to OK
- Disk I/O should decrease (less data read from disk)
- Query performance should improve noticeably

## Summary
Your SQL Server is experiencing memory pressure with critically low PLE. The server needs approximately **2-4 GB more memory**. First, verify if physical RAM is available beyond the 16 GB configured limit. If yes, increase max server memory. If no, plan for a RAM upgrade to maintain healthy performance.
```
