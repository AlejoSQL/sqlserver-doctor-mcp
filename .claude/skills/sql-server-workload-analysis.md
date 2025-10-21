---
name: sql-server-workload-analysis
description: Analyze current SQL Server workload, resource pressure, and identify performance bottlenecks
---

# SQL Server Workload Analysis

Analyze current SQL Server workload, resource pressure, and identify performance bottlenecks.

## When to Use This Skill

Invoke this skill when the user asks to:
- "Analyze SQL Server workload"
- "Check current performance"
- "What's running on SQL Server?"
- "Find blocking queries"
- "Check for CPU pressure"
- "Diagnose slow performance"
- "What queries are running?"
- "Is there resource contention?"

## Workflow

Execute the following steps in order:

### 1. Check Active Sessions

Call the `get_active_sessions` MCP tool from the SQL Server Doctor server to retrieve:
- Currently executing queries
- Session details (CPU, elapsed time, reads)
- Blocking information
- Wait statistics

**Analyze the sessions for:**
- **Blocking chains**: Sessions with `blocking_session_id` set
- **Long-running queries**: High `elapsed_seconds` values
- **High CPU consumers**: Sessions with high `cpu_seconds`
- **High I/O operations**: Sessions with high `reads` or `logical_reads`
- **Wait issues**: Sessions with significant `wait_time` and concerning `last_wait_type`

### 2. Check Scheduler Statistics

Call the `get_scheduler_stats` MCP tool from the SQL Server Doctor server to assess:
- CPU pressure (runnable tasks waiting for CPU)
- I/O pressure (pending disk operations)
- Number of schedulers (CPU cores)

**Interpret the results:**
- Review the `interpretation` field for CPU and I/O pressure levels
- Check `cpu_pressure_detected` flag
- Examine `avg_runnable_per_scheduler` for queue depth

### 3. Correlate Findings

Connect the dots between active sessions and resource pressure:
- If CPU pressure is detected, identify which sessions are consuming CPU
- If I/O pressure exists, identify sessions with high read counts
- If blocking is detected, trace the blocking chain to the root blocker
- Identify patterns (e.g., same program causing issues, specific database)

### 4. Provide Analysis

Structure your findings:

**Workload Summary:**
- Number of active sessions
- Overall resource utilization assessment
- Any immediate concerns

**Resource Pressure:**
- CPU pressure status and severity
- I/O pressure status and severity
- Correlation to active workload

**Session Highlights:**
- Top CPU consumers (if any)
- Top I/O consumers (if any)
- Long-running queries (if any)
- Blocking situations (if any)

**Wait Analysis:**
- Common wait types observed
- What they indicate (e.g., LCK_M_X = lock contention, PAGEIOLATCH = I/O waits)

### 5. Recommendations

Based on findings, provide actionable recommendations:

**Immediate Actions** (if critical issues found):
- Kill blocking sessions (provide session IDs)
- Investigate runaway queries
- Address severe resource contention

**Investigation Steps**:
- Queries to review for optimization
- Indexes that might be missing
- Areas requiring deeper analysis

**Preventive Measures**:
- Workload patterns to watch
- Configuration adjustments to consider
- Monitoring to implement

## Important Notes

- **Do NOT** kill sessions or modify queries without user approval
- **Do NOT** check configurations (use the config-check skill for that)
- **Focus** on current workload and resource utilization
- If no active sessions are found, that's normal - report "No active user queries detected"
- Explain wait types in simple terms (avoid just listing codes)
- Consider time of day - low activity might be expected during off-hours

## Common Wait Types Reference

Help the user understand wait types:
- **LCK_M_*** - Lock waits (blocking/contention)
- **PAGEIOLATCH_*** - Waiting for data pages to be read from disk
- **CXPACKET** - Parallel query coordination waits
- **SOS_SCHEDULER_YIELD** - CPU pressure, threads yielding
- **ASYNC_NETWORK_IO** - Client application not consuming results fast enough
- **WRITELOG** - Transaction log write waits

## Example Output Format

```
# SQL Server Workload Analysis

## Workload Summary
- **Active Sessions**: 3 queries currently executing
- **Overall Status**: ⚠️ Moderate CPU pressure detected
- **Immediate Concerns**: 1 blocking situation found

## Resource Pressure Analysis

### CPU Pressure
- **Status**: MODERATE CPU PRESSURE
- **Average Runnable Tasks**: 1.25 per scheduler
- **Interpretation**: Some queries are waiting for CPU time - not critical but worth monitoring
- **Total Schedulers**: 4 (CPU cores)

### I/O Pressure
- **Status**: Normal I/O activity
- **Average Pending I/O**: 0.50 per scheduler
- **Interpretation**: Disk subsystem is keeping up with demand

## Active Sessions

### 🔴 Blocking Detected
**Blocked Session**: 53 (SPID)
- **Blocked By**: Session 52
- **SQL**: `UPDATE orders SET status = 'processed'`
- **Wait Time**: 5000 ms (5 seconds)
- **Wait Type**: LCK_M_X (Exclusive lock wait)

**Blocking Session**: 52 (SPID)
- **SQL**: `SELECT * FROM users WHERE id = 123`
- **Elapsed Time**: 2.3 seconds
- **Status**: Running

### Top Resource Consumers
**Session 52**:
- **CPU**: 1.5 seconds
- **Reads**: 500 logical reads
- **Database**: MyDatabase
- **Application**: My Application

## Recommendations

### Immediate Actions
1. **Investigate blocking**: Session 52 is blocking Session 53
   - Review the query in Session 52 - it's holding locks
   - Consider killing Session 52 if it's stuck: `KILL 52`
   - Root cause: Long-running SELECT holding locks

### Investigation
1. **Review Session 52's query**: The SELECT statement may need optimization
2. **Check for missing indexes**: High logical reads suggest table scan
3. **Consider query timeout settings**: 2.3 seconds is reasonable, but locks are being held

### Preventive Measures
1. **Implement READ UNCOMMITTED or SNAPSHOT isolation** where appropriate to reduce blocking
2. **Add monitoring** for blocking chains
3. **Review application's transaction scope** - ensure transactions are short

## Summary
Your SQL Server is experiencing moderate CPU pressure with an active blocking situation. The primary concern is Session 52 which is blocking other queries. Investigate this query for optimization opportunities and consider adjusting transaction isolation levels to reduce contention.
```
