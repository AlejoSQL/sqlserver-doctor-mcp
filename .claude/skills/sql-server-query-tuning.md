---
name: sql-server-query-tuning
description: Systematically diagnose and optimize slow SQL Server queries using execution plan analysis, antipattern detection, statistics health checks, and index recommendations
---

# SQL Server Query Tuning

Systematically diagnose and optimize slow SQL Server queries through a phase-based approach that prioritizes query rewrites before index analysis.

## When to Use This Skill

Invoke this skill when the user asks to:
- "Optimize this query" or "Tune this query"
- "Why is this query slow?"
- "How can I make this query faster?"
- "Analyze query performance"
- "This query takes too long to run"
- "Find performance issues in this query"
- "Query optimization help"
- "Need help with slow SELECT"

---

# 🚨 MANDATORY WORKFLOW - FOLLOW THIS EXACT ORDER 🚨

**DO NOT SKIP PHASES. DO NOT JUMP TO INDEX RECOMMENDATIONS.**

You MUST complete each phase in order and check the STOP gates before proceeding.

## Phase Checklist (Execute in Order)

### ✅ Phase 1: Baseline (ALWAYS START HERE)
- [ ] **REQUIRED**: Call `analyze_query_execution()` with the user's query
- [ ] **REQUIRED**: Record baseline metrics (duration, logical reads, bottleneck type)
- [ ] **STOP GATE**: Is duration < 100ms? → STOP, tell user query is already fast
- [ ] If slow, continue to Phase 2

### ✅ Phase 2: Antipatterns (NEVER SKIP THIS)
- [ ] **REQUIRED**: Call `detect_query_antipatterns()` with the query
- [ ] **REQUIRED**: Review the `rewrite_priority` in response
- [ ] **STOP GATE**: Is rewrite_priority HIGH or MEDIUM? → STOP index analysis
  - Present antipatterns to user with fix recommendations
  - Ask user to test rewritten query
  - RESTART from Phase 1 with new query
- [ ] If rewrite_priority is LOW or NONE, continue to Phase 3

### ✅ Phase 3: Execution Plan Analysis
- [ ] Review `execution_plan_summary` from Phase 1
- [ ] Check for warnings (implicit conversions, missing stats)
- [ ] Identify high-cost operators (> 20% of query cost)
- [ ] Look for cardinality mismatches (estimated vs actual rows)
- [ ] **STOP GATE**: Cardinality variance > 10x? → Continue to Phase 4
- [ ] Otherwise, skip to Phase 5

### ✅ Phase 4: Statistics Health (Only if cardinality issues)
- [ ] Call `get_query_statistics_health()` for tables in query
- [ ] Check for stale statistics (days old > 30, modification % > 20%)
- [ ] Provide UPDATE STATISTICS commands
- [ ] **STOP GATE**: If statistics updated → Ask user to re-run query, RESTART Phase 1
- [ ] If statistics healthy but query still slow, continue to Phase 5

### ✅ Phase 5: Index Recommendations (ONLY AFTER PHASES 1-4 COMPLETE)
- [ ] Analyze query structure (WHERE, JOIN, ORDER BY columns)
- [ ] Apply index design principles (equality first, range next)
- [ ] **REQUIRED**: Recommend lean indexes (key columns ONLY) in HIGH priority
- [ ] **REQUIRED**: Evaluate columnstore suitability (Phase 5.5)
- [ ] **OPTIONAL**: Only mention covering indexes if ALL 6 conditions in Phase 5.6 met

### ✅ Phase 6: Summary
- [ ] Provide comprehensive summary with baseline vs expected improvement
- [ ] List recommendations in priority order
- [ ] Set realistic expectations

---

## Critical Rules (Violations Are Errors)

1. 🚨 **NEVER skip Phase 2 (antipatterns)** - query rewrites come before indexes
2. 🚨 **NEVER recommend indexes in HIGH priority with INCLUDE columns** - key columns only
3. 🚨 **NEVER recommend covering indexes without evaluating columnstore first** (Phase 5.5)
4. 🚨 **NEVER continue if query < 100ms** - stop and tell user it's already fast
5. 🚨 **NEVER recommend indexes for queries that need rewriting** - fix query first

---

## Core Principles

### 1. Query Rewrites Before Index Analysis

**CRITICAL: Query rewrites MUST come BEFORE index analysis.**

Rewriting a query can fundamentally change its execution plan, making any prior index analysis obsolete. Always analyze and fix the query itself before recommending indexes.

### 2. Trust Your Expertise

**This skill has deep SQL Server optimization knowledge. Trust it.**

- **When the skill's guidance conflicts with user assumptions, the skill is likely correct**
- Do NOT automatically defer to user beliefs about SQL Server behavior
- If a user suggests an approach that contradicts best practices (e.g., "just add more covering indexes"), **respectfully explain why that's not optimal**
- Provide objective, evidence-based guidance even if it disagrees with the user's initial assessment
- The skill should be confident in its recommendations while remaining open to clarification questions

**Example scenarios where you should push back:**
- User wants to create wide covering indexes → Explain maintenance overhead and suggest lean indexes
- User insists columnstore is always better → Explain OLTP vs OLAP trade-offs
- User wants to skip antipattern analysis → Emphasize why query rewrites come first
- User believes adding indexes always helps → Explain when indexes hurt performance (write-heavy workloads)

The goal is to educate and guide the user toward correct solutions, not to validate incorrect assumptions.

## Workflow

Execute the following phases in order with decision gates:

### Phase 1: Gather Performance Baseline

**ALWAYS START HERE**

#### 1.0 Auto-Detect Database (If Not Specified)

If the user didn't explicitly provide a database name, automatically detect it from the query:

**Step 1: Extract schema-qualified table names from query**
- Look for tables in FROM clauses, JOIN clauses
- **IMPORTANT**: Always include the schema name
- Examples:
  - `FROM PDSEDTA.F595074H` → Extract `PDSEDTA.F595074H`
  - `FROM RPT.ViewName` → Extract `RPT.ViewName`
  - `FROM Orders` → Extract `dbo.Orders` (assume dbo schema if not specified)

**Step 2: Find the database**
Call `find_object_database` with the schema-qualified table name:
```
find_object_database(object_name="PDSEDTA.F595074H")
```

**Note**: Always pass schema.table format to the tool. If the query doesn't specify a schema (e.g., just `FROM Orders`), assume `dbo` schema and call `find_object_database(object_name="dbo.Orders")`

**Response:**
```json
{
  "database_name": "RAPTOR",
  "schema_name": "PDSEDTA",
  "object_name": "F595074H",
  "object_type": "USER_TABLE",
  "full_name": "RAPTOR.PDSEDTA.F595074H",
  "success": true
}
```

**Step 3: Use the detected database**
- If user specified database → Use that
- If `find_object_database` succeeds → Use returned `database_name`
- If not found → Ask user which database to use

#### 1.1 Execute and Capture Metrics

Call the `analyze_query_execution` tool:
```
analyze_query_execution(
    query: "<user's SQL query>",
    database_name: "<from user or auto-detected>",
    include_actual_plan: true
)
```

This captures:
- Execution duration (ms)
- Logical and physical reads
- CPU time
- Row count
- Query hash and plan hash (for later plan cache analysis)

#### 1.2 Establish Baseline

Record the baseline metrics:
- **Duration**: How long the query took
- **Logical Reads**: Primary I/O indicator
- **Row Count**: Verify expected results
- **Bottleneck Type**: IO_BOUND, CPU_BOUND, WAIT_BOUND, or MEMORY_BOUND

#### Decision Gate 1
- If query runs in **< 100ms** and meets performance requirements → **STOP**
  - Tell user: "Query is already fast, no optimization needed"
  - Avoid over-optimization
- Otherwise → Continue to Phase 2

---

### Phase 2: Query Rewrite Opportunities

**CRITICAL: DO THIS BEFORE INDEX ANALYSIS**

#### 2.1 Detect Antipatterns

Call the `detect_query_antipatterns` tool:
```
detect_query_antipatterns(
    query: "<user's SQL query>",
    execution_plan_xml: "<from Phase 1 if available>"
)
```

This detects:
- **SARGability Issues**:
  - Functions on columns: `WHERE YEAR(OrderDate) = 2024`
  - Implicit type conversions
  - Leading wildcards: `LIKE '%search%'`
- **SELECT * antipattern**
- **Correlated subqueries** executing per row
- **Join problems**: Cartesian products, missing predicates
- **Other issues**: Unnecessary DISTINCT, cursors, nested views

#### 2.2 Analyze Rewrite Priority

Review the `rewrite_priority` from the response:
- **HIGH**: Critical antipatterns (non-SARGable predicates, correlated subqueries)
- **MEDIUM**: SELECT *, leading wildcards
- **LOW**: Minor optimizations
- **NONE**: No antipatterns detected

#### Decision Gate 2

**If rewrite_priority is HIGH or MEDIUM:**

1. **STOP index analysis** - do NOT proceed to Phase 5 yet
2. Present antipatterns to user with:
   - Category and severity
   - Specific location in query
   - Clear recommendation for fix
   - Estimated performance impact
3. Provide rewritten query examples if possible
4. **Ask user to test the rewritten query**
5. **RESTART from Phase 1** with the new query
6. Verify improvement before analyzing indexes

**If rewrite_priority is LOW or NONE:**
- Continue to Phase 3

**Why This Matters:**
```
❌ BAD APPROACH (Index-first):
1. Find table scan on Orders table
2. Recommend index on Orders.OrderDate
3. User creates index
4. Later discover WHERE YEAR(OrderDate) = 2024 prevents index usage
5. Index is useless → Wasted effort

✅ GOOD APPROACH (Rewrite-first):
1. Detect WHERE YEAR(OrderDate) = 2024 antipattern
2. Rewrite as: WHERE OrderDate >= '2024-01-01' AND OrderDate < '2025-01-01'
3. Now index on OrderDate will be used
4. Create correct index once
```

---

### Phase 3: Execution Plan Deep Dive

**Only if query is optimized but still slow**

#### 3.1 Analyze Plan Summary

Review the `execution_plan_summary` from Phase 1:

**Check for warnings:**
- Implicit conversions (prevents index seeks)
- No join predicates (Cartesian product)
- Missing statistics (poor cardinality estimates)

**Identify high-cost operators (> 20% of query cost):**
- Table/Index Scans on large tables
- Key Lookups (bookmark lookups) - indicates missing covering index
- Sorts - missing index or ORDER BY without supporting index
- Spools - potential for query rewrite
- Hash Joins on small datasets - might need index for Nested Loops

**Check parallelism:**
- Is MAXDOP appropriate for query?
- CXPACKET waits indicating coordination overhead
- Serial execution of expensive query (missing parallelism opportunity)

#### 3.2 Look for Cardinality Mismatches

Compare estimated vs actual rows at high-cost operators:
- **Variance > 10x**: Statistics problem → Go to Phase 4
- **Variance < 10x**: Skip to Phase 5

#### Decision Gate 3
- If cardinality mismatches > 10x → Continue to Phase 4 (Statistics)
- Otherwise → Skip to Phase 5 (Indexes)

---

### Phase 4: Statistics Health

**Only if cardinality estimation is problematic**

#### 4.1 Check Statistics Freshness

Call the `get_query_statistics_health` tool:
```
get_query_statistics_health(
    database_name: "<database>",
    table_names: ["dbo.Orders", "dbo.Customers"]  # Tables from query
)
```

#### 4.2 Analyze Statistics Issues

Review `statistics_analysis` for each table:

**Check for stale statistics:**
- **Days old > 30**: May be stale
- **Modification % > 20%**: Likely stale (many rows changed since last update)
- **Severity HIGH**: Immediate update needed

**Check sampling:**
- **Sampling % < 100%**: Statistics were sampled, not full scan
- For critical queries, consider `WITH FULLSCAN`

**Check auto-update settings:**
- `auto_update_stats_enabled: false` → Recommend enabling
- `auto_create_stats_enabled: false` → Recommend enabling

#### 4.3 Provide Update Recommendations

For statistics with `needs_update: true`, provide the exact SQL:
```sql
-- Example from recommendation field
UPDATE STATISTICS dbo.Orders WITH FULLSCAN;
```

#### Decision Gate 4
- If statistics were updated → Ask user to **re-run query** and restart from Phase 1
- If statistics are healthy but query still slow → Continue to Phase 5

---

### Phase 5: Index Analysis (Strategic LLM-Driven Approach)

**ONLY AFTER QUERY IS OPTIMIZED AND STATISTICS ARE HEALTHY**

This phase is LLM-driven - use your understanding of index design principles to make strategic recommendations.

#### 5.1 Analyze Query Structure for Index Opportunities

**Extract key information from the user's query:**

1. **WHERE clause predicates (Most Important):**
   - **Equality predicates** (WHERE col = value) → **Primary index key candidates**
   - **Range predicates** (WHERE col BETWEEN/>/< value) → Index key or INCLUDE
   - **Multiple predicates** → Key column order matters (equality first, range last)

2. **JOIN columns:**
   - JOIN predicates are excellent index key candidates
   - Both sides of JOIN should have indexes
   - Example: `JOIN Orders ON Customers.CustomerID = Orders.CustomerID` → Index on both

3. **ORDER BY/GROUP BY:**
   - Can an index eliminate expensive sort operations?
   - Index column order must exactly match ORDER BY order
   - GROUP BY columns should be in index key

4. **SELECT columns:**
   - **Use INCLUDE sparingly** - only for critical, high-frequency queries
   - Don't blindly cover every query - maintenance cost matters

**Index Design Principles (Apply These):**
1. **Equality columns first** in key (WHERE col = value)
2. **Range columns next** in key (WHERE col BETWEEN/>/< value)
3. **🚨 HARD RULE: HIGH priority recommendations = Key columns ONLY, ZERO INCLUDE columns**
4. **INCLUDE columns are a LAST RESORT** - Only after columnstore is ruled out + extreme justification
5. **Keep indexes lean** - more indexes ≠ better performance
6. **Think workload-wide** - will this index help other queries too?

#### 5.2 Review Execution Plan Operators

From `execution_plan_summary` in Phase 1:

**High-cost operators needing index help:**

1. **Table Scans on large tables:**
   - **Analysis**: Which WHERE/JOIN columns are being filtered?
   - **Recommendation**: Index on those filter columns

2. **Index Scans (full scan of index):**
   - **Analysis**: Missing filter column in index key
   - **Recommendation**: Add missing column to index key

3. **Key Lookups:**
   - **Analysis**: Index doesn't include all needed columns
   - **Recommendation**: **Be cautious** - only add INCLUDE if query is critical and frequent
   - **Avoid**: Wide covering indexes for one-off queries

4. **Sorts:**
   - **Analysis**: ORDER BY/GROUP BY causing expensive sort
   - **Recommendation**: Index with matching column order

5. **Hash Joins on small datasets:**
   - **Analysis**: Missing index preventing Nested Loop Join
   - **Recommendation**: Index inner table on join key

#### 5.3 Optional: Review Query Plan Index Hints (Use Sparingly)

You can call `analyze_missing_indexes` to see what SQL Server's optimizer suggests:

```
analyze_missing_indexes(
    database_name: "{database}",
    execution_plan_xml: "{from Phase 1}"
)
```

**⚠️ IMPORTANT: Treat query plan suggestions as HINTS ONLY, not definitive recommendations**

**Why be skeptical:**
- Query plan suggestions are **query-specific** - optimized for ONE query only
- Often suggest **wide covering indexes** with excessive INCLUDE columns
- Don't consider **overall workload** or maintenance cost
- Can lead to **index bloat** if followed blindly

**How to use plan suggestions strategically:**

1. **Extract key column ideas** (the valuable part):
   ```
   Plan says:
   CREATE INDEX IX_Orders_CustomerID
   ON Orders (CustomerID, OrderDate)
   INCLUDE (OrderTotal, Status, Notes, CreatedBy, ModifiedBy, ShippingAddress)

   You extract:
   - ✅ CustomerID (equality column) - Good key column idea
   - ✅ OrderDate (range column) - Good key column idea
   - ❌ 6 INCLUDE columns - Ignore, too query-specific
   ```

2. **Validate against query structure:**
   - Do key columns match WHERE/JOIN predicates? ✓
   - Would this index benefit other queries? (Consider workload)
   - Is the index too wide for the benefit?

3. **Design a better, focused index:**
   ```sql
   -- ❌ Plan suggestion (too wide, query-specific):
   CREATE INDEX IX_Orders_CustomerID
   ON Orders (CustomerID, OrderDate)
   INCLUDE (OrderTotal, Status, Notes, CreatedBy, ModifiedBy, ShippingAddress);

   -- ✅ Your strategic recommendation (lean, workload-aware):
   CREATE INDEX IX_Orders_CustomerID_OrderDate
   ON Orders (CustomerID, OrderDate);

   -- Reasoning:
   -- - Covers WHERE CustomerID = X AND OrderDate filtering
   -- - Benefits multiple queries with these predicates
   -- - No INCLUDE columns = lower maintenance overhead
   -- - If covering is needed later, add INCLUDE for specific critical queries
   ```

#### 5.4 Provide Strategic Index Recommendations

**Format by priority with clear reasoning:**

```markdown
### 🔴 HIGH Priority - Fundamental Indexes (Key Columns ONLY)

⚠️ **CRITICAL**: HIGH priority indexes must have ZERO INCLUDE columns. Keep indexes lean.

1. **Create Index for WHERE Filtering:**
   ```sql
   CREATE INDEX IX_Orders_CustomerID_OrderDate
   ON dbo.Orders (CustomerID, OrderDate);
   ```
   - **Reasoning**: Query filters `WHERE CustomerID = X AND OrderDate >= Y`
   - **Key columns**: CustomerID (equality first), OrderDate (range second)
   - **Why no INCLUDE**: Keep index lean for general use across queries
   - **Estimated impact**: Eliminates table scan → index seek on 1M row table
   - **Workload benefit**: Likely helps other queries filtering on these columns

2. **Add Index for JOIN:**
   ```sql
   CREATE INDEX IX_OrderItems_OrderID
   ON dbo.OrderItems (OrderID);
   ```
   - **Reasoning**: Nested loop join on OrderID
   - **Estimated impact**: Enables efficient join instead of hash join

### 🔵 LOW Priority - Database Health

1. **Review Database-Wide Index Patterns (Optional)**
   Call `analyze_missing_indexes(database_name="{database}")` to identify:
   - Unused indexes (zero reads, high updates) → Consider dropping
   - High-impact missing indexes across all queries
   - Index consolidation opportunities
```

#### 5.5 Evaluate Columnstore Suitability (LLM Analysis)

**Analyze query patterns for columnstore index suitability:**

**Check if query exhibits OLAP characteristics:**

1. **Aggregation-heavy query:**
   - Uses SUM(), AVG(), COUNT(), MIN(), MAX()
   - GROUP BY with many groups
   - Scans large portions of table

2. **Large table scans:**
   - Execution plan shows table/index scan
   - Row count > 1 million rows
   - Query reads 10%+ of table rows

3. **Limited UPDATE/DELETE workload:**
   - Table is primarily read-only or bulk-loaded
   - Few singleton inserts/updates

**If query is OLAP-like, provide columnstore guidance:**

```markdown
⚠️ **COLUMNSTORE CONSIDERATION (Requires User Validation)**

Based on this query's characteristics, table `{table_name}` **MAY** benefit from a columnstore index:

**Evidence from your query:**
- ✓ Uses aggregation functions (SUM/AVG/COUNT)
- ✓ Scans large portion of table ({estimated_rows} rows)
- ✓ GROUP BY clause present

**CRITICAL - You must verify:**
- [ ] Table has >= 1M rows (minimum for benefit)
- [ ] Overall workload is analytical OR hybrid OLTP/OLAP
- [ ] UPDATE/DELETE operations < 10% of total operations
- [ ] Bulk loads are >= 102,400 rows (or accept deltastore overhead)

**Option 1: Nonclustered Columnstore (RECOMMENDED for hybrid)**
```sql
CREATE NONCLUSTERED COLUMNSTORE INDEX NCCI_{table}_Analytics
ON {table} ({aggregation_columns}, {group_by_columns}, {filter_columns});
```
- Use when: Mix of OLTP (singleton lookups) and OLAP (analytics)
- Keeps rowstore for fast singleton operations
- Adds columnstore for fast aggregations

**Option 2: Clustered Columnstore (ONLY for pure analytical tables)**
```sql
-- WARNING: Removes all rowstore indexes, converts entire table
CREATE CLUSTERED COLUMNSTORE INDEX CCI_{table}
ON {table};
```
- Use when: Table is ONLY used for analytics, no OLTP workload
- Maximum compression (60-80%)
- Slow for singleton lookups

**This is NOT a definitive recommendation** - test in non-production first!
```

**If query is NOT OLAP-like:**
- Skip columnstore discussion
- Focus on traditional B-tree indexes (lean indexes from Phase 5.4)

---

#### 5.6 Covering Indexes - LAST RESORT ONLY

**⚠️ IMPORTANT: Only reach this section AFTER evaluating columnstore in 5.5 above**

Covering indexes (with INCLUDE columns) should be extremely rare. Do NOT recommend them unless ALL conditions below are met.

**Required Conditions (ALL must be true):**
- ✓ **Columnstore is inappropriate** - Query is OLTP point query, NOT analytical (no aggregations/large scans)
- ✓ **Extremely high frequency** - Query runs 10,000+ times per day (proven, measured from production)
- ✓ **Key lookups are primary bottleneck** - Measured via execution plan (e.g., Key Lookup operator costs > 30%)
- ✓ **Light write workload** - Table has minimal INSERT/UPDATE/DELETE activity (< 10% of operations)
- ✓ **Business-critical query** - Performance directly impacts revenue or critical user experience
- ✓ **Lean index already recommended** - You've already provided the key-only version in Phase 5.4 HIGH priority

**If and ONLY if all conditions above are met, mention as optional with heavy warnings:**

```markdown
### ⚠️ OPTIONAL - Covering Index (Last Resort)

**ONLY consider this if ALL conditions above are verified true:**

```sql
-- ⚠️ LAST RESORT: Only if query runs 10,000+ times/day
-- AND columnstore is inappropriate for OLTP workload
-- AND key lookups are proven bottleneck
CREATE INDEX IX_Orders_CustomerID_Covering
ON dbo.Orders (CustomerID, OrderDate)
INCLUDE (OrderTotal, Status);  -- Only include absolutely essential columns
```

**Critical Trade-offs:**
- ❌ **Maintenance cost**: Every INSERT/UPDATE/DELETE on Orders table pays the price
- ❌ **Storage overhead**: Index size increases significantly
- ❌ **Memory pressure**: Larger index = more buffer pool usage
- ❌ **Plan instability**: More index choices can lead to unpredictable plan changes
- ✅ **Benefit**: Eliminates key lookups for this specific query

**Before creating this index:**
1. Verify query frequency in production (10K+ runs/day minimum)
2. Confirm columnstore is not appropriate (5.5 evaluation)
3. Measure current key lookup cost in execution plan
4. Start with lean index from HIGH priority first
5. Only add INCLUDE if measured improvement justifies maintenance cost

**Phrasing for user:**
"This covering index is a last resort optimization. First implement the lean index from HIGH priority, measure the improvement, and only consider adding INCLUDE columns if key lookups remain a significant bottleneck and the query frequency justifies the maintenance overhead."
```

**If conditions are NOT met:**
- Do not mention covering indexes at all
- Stick with lean indexes from Phase 5.4
- Direct user to columnstore evaluation if query is analytical

---

### Phase 6: Advanced Tuning

**Only if query is still slow after Phases 1-5**

This phase is for complex issues beyond basic optimization.

**Potential areas to investigate:**
- Parameter sniffing (if query has parameters)
- Tempdb spills (memory grants)
- Locking/blocking issues
- Plan cache problems

**Note**: These tools are not yet implemented in Priority 1. For now, document these as potential areas for further investigation.

---

### Phase 7: Summary and Next Steps

#### 7.1 Provide Comprehensive Summary

```markdown
## Query Tuning Summary

### Current Performance
- Duration: {baseline_duration} ms
- Logical Reads: {baseline_reads}
- Bottleneck: {bottleneck_type}

### Recommendations Applied (in order)
1. ✅ Query rewrite: Fixed non-SARGable predicate
2. ✅ Statistics update: dbo.Orders
3. 🔄 Pending: Create missing index (see below)

### Expected Improvement
- Estimated duration: {baseline_duration} → {estimated_new_duration} ms ({percentage}% improvement)
- Estimated logical reads reduction: {percentage}%

### Next Steps
1. [Immediate] Create recommended index (see HIGH priority above)
2. [Monitor] Run query and measure improvement
3. [Optional] Evaluate columnstore for analytical workloads
```

#### 7.2 Set Expectations

- **Be realistic**: Index won't help if query is poorly written
- **Test in stages**: Apply one change at a time, measure results
- **Monitor impact**: Track index size and maintenance overhead
- **Avoid over-indexing**: More indexes ≠ better performance

---

## Decision Tree

```
User provides slow query
         ↓
[Phase 1: Baseline]
Execute query, capture metrics
         ↓
Duration < 100ms? ──Yes──> STOP (already fast)
         ↓ No
[Phase 2: Antipatterns]
Detect query rewrites
         ↓
Rewrite priority HIGH/MEDIUM? ──Yes──> FIX QUERY FIRST
         ↓ No                              ↓
         ↓                          RESTART Phase 1
         ↓                          with new query
[Phase 3: Execution Plan]
Analyze plan warnings, operators
         ↓
Cardinality mismatch > 10x? ──Yes──> [Phase 4: Statistics]
         ↓ No                              ↓
         ↓                          UPDATE STATISTICS
         ↓                                 ↓
         ↓                          RE-RUN QUERY
         ↓                                 ↓
[Phase 5: Indexes]                         ↓
Analyze missing indexes   <────────────────┘
         ↓
Provide prioritized recommendations
         ↓
[Phase 7: Summary]
```

---

## Important Guardrails

### What TO Do
- ✅ Always start with Phase 1 baseline
- ✅ Fix query antipatterns BEFORE recommending indexes
- ✅ Validate statistics before index recommendations
- ✅ Provide ready-to-execute SQL statements
- ✅ Estimate improvement magnitude
- ✅ Stop if query is already fast (< 100ms)
- ✅ **Focus on WHERE/JOIN columns for index keys** - these are most valuable
- ✅ **HIGH priority indexes = key columns ONLY** - zero INCLUDE columns
- ✅ **Evaluate columnstore before covering indexes** - columnstore is preferred for analytical queries
- ✅ **Keep indexes lean** - default recommendation is always key columns only
- ✅ **Think workload-wide** - will index benefit other queries?
- ✅ **Provide reasoning** for each index recommendation

### What NOT To Do
- ❌ Never skip antipattern detection
- ❌ Never recommend indexes before fixing query issues
- ❌ Never execute DDL statements - only provide SQL for user to run
- ❌ Never recommend indexes for queries that should be rewritten
- ❌ Don't over-analyze fast queries
- ❌ Don't call tools unnecessarily - follow the workflow
- ❌ **🚨 NEVER add INCLUDE columns to HIGH priority index recommendations** - they belong only in Phase 5.6 Last Resort
- ❌ **NEVER recommend covering indexes (INCLUDE) without first evaluating columnstore** (Phase 5.5)
- ❌ **NEVER recommend covering indexes unless ALL 6 conditions in Phase 5.6 are met** - they are a last resort
- ❌ **Don't blindly follow query plan covering index suggestions** - they're too query-specific and ignore maintenance costs
- ❌ **Don't suggest INCLUDE columns for analytical queries** - use columnstore instead

---

## Tool Usage Summary

### Phase 1 - Always
- `analyze_query_execution` - Baseline metrics

### Phase 2 - Always (unless query is already fast)
- `detect_query_antipatterns` - Find rewrite opportunities

### Phase 3 - Built into Phase 1 response
- Use `execution_plan_summary` from Phase 1

### Phase 4 - Only if statistics issues detected
- `get_query_statistics_health` - Check stats freshness

### Phase 5 - Strategic LLM-driven index analysis
- Analyze query structure for WHERE/JOIN/ORDER BY columns
- Apply index design principles (equality first, range next, INCLUDE sparingly)
- Think workload-wide, not query-specific
- **Optional (use sparingly)**: Call `analyze_missing_indexes(database_name, execution_plan_xml)` for:
  - Query plan hints (extract key columns only, ignore excessive INCLUDE columns)
  - Database-wide health check (unused indexes, consolidation opportunities)
- Be skeptical of covering indexes - maintenance cost vs benefit

### Phase 6 - Not yet implemented
- Future: Plan cache analysis, tempdb usage, locking analysis

---

## Example Interaction

**User**: "This query is really slow, can you help optimize it?"
```sql
SELECT * FROM dbo.Orders
WHERE YEAR(OrderDate) = 2024
```

**Assistant**:

I'll help optimize this query using a systematic approach. Let me start by analyzing its current performance.

[Calls `analyze_query_execution`]

**Baseline Performance:**
- Duration: 1,523 ms
- Logical Reads: 45,234
- Rows Returned: 12,458
- Bottleneck: IO_BOUND

Now let me check for query antipatterns before recommending indexes.

[Calls `detect_query_antipatterns`]

**⚠️ CRITICAL Issue Found - Rewrite Required**

I found a high-severity antipattern that's preventing your query from performing well:

**Issue**: Non-SARGable Predicate
- **Location**: `WHERE YEAR(OrderDate) = 2024`
- **Problem**: The `YEAR()` function on the `OrderDate` column prevents SQL Server from using any index on that column
- **Impact**: Forces a table scan of all 45,234 rows instead of an index seek

**Recommended Fix:**
Replace the WHERE clause with a date range:
```sql
SELECT * FROM dbo.Orders
WHERE OrderDate >= '2024-01-01'
  AND OrderDate < '2025-01-01'
```

Also, I noticed you're using `SELECT *` which retrieves all columns. Consider selecting only the columns you need.

**Please test the rewritten query first, then I can analyze if you need any indexes.** Creating an index on OrderDate won't help with the YEAR() function, so we need to fix the query first.

Would you like me to analyze the rewritten query?

---

## Query Tuning Quick Reference

| Symptom | Likely Cause | Phase to Focus On |
|---------|-------------|------------------|
| Table scan on large table | Missing index OR non-SARGable predicate | Phase 2, then 5 |
| High logical reads | SELECT * antipattern, missing index | Phase 2, then 5 |
| Cardinality way off | Stale statistics | Phase 4 |
| Nested loops with high execution count | Correlated subquery | Phase 2 |
| Implicit conversion warning | Data type mismatch | Phase 2 |
| Key lookups | Consider columnstore (5.5) or lean index optimization | Phase 5 |
| Execution time >> CPU time | I/O bound - likely index issue | Phase 5 |
| Already fast (< 100ms) | No optimization needed | Stop at Phase 1 |

---

## Skill Success Criteria

This skill is successful when:
- User's query performance improves measurably (duration, I/O reduction)
- Recommendations are actionable (ready-to-execute SQL provided)
- User understands WHY the query was slow
- Query antipatterns are fixed BEFORE indexes are recommended
- Columnstore warnings are clear and require user validation
- User can implement changes independently with provided SQL
