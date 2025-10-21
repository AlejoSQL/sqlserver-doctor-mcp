---
name: sql-server-config-check
description: Check and verify SQL Server configuration health including version information and critical configuration settings
---

# SQL Server Configuration Check

Check and verify SQL Server configuration health including version information and critical configuration settings.

## When to Use This Skill

Invoke this skill when the user asks to:
- "Check SQL Server configuration"
- "Verify server settings"
- "Is my SQL Server configured correctly?"
- "Configuration health check"
- "Review server configuration"
- "Check if SQL Server is properly configured"

## Workflow

⚠️ **CRITICAL REQUIREMENT**: This skill requires using the **WebSearch tool** in Step 2 to check for the latest patches and security updates. Do not skip the web search - it is mandatory for a complete configuration health check.

Execute the following steps in order:

### 1. Check SQL Server Version

Call the `get_server_version` MCP tool from the SQL Server Doctor server to retrieve:
- SQL Server version string
- Server instance name
- Edition information

**Present the version information clearly:**
- Extract and highlight the SQL Server edition (e.g., Enterprise, Standard, Express, Developer)
- Extract the version number and build (e.g., 15.0.4261.1)
- Identify the SQL Server year (e.g., 2019, 2022)

### 2. Check for Latest Patches and Security Updates

⚠️ **MANDATORY STEP - You MUST use the WebSearch tool for this step**

**Step 2a: Perform First Web Search**

Use the WebSearch tool with this query format:
```
"SQL Server [year from step 1] latest cumulative update October 2025"
```

**Concrete examples:**
- For SQL Server 2019: `"SQL Server 2019 latest cumulative update October 2025"`
- For SQL Server 2022: `"SQL Server 2022 latest cumulative update October 2025"`
- For SQL Server 2017: `"SQL Server 2017 latest cumulative update October 2025"`

**Step 2b: Perform Second Web Search**

Use the WebSearch tool again with this query format:
```
"SQL Server [year] build version numbers"
```

**Concrete examples:**
- For SQL Server 2019: `"SQL Server 2019 build version numbers"`
- For SQL Server 2022: `"SQL Server 2022 build version numbers"`

**Step 2c: Extract Information from Search Results**

From the web search results, identify and extract:
- **Latest Cumulative Update (CU) number** - e.g., "CU25" or "CU28"
- **Latest build number** - e.g., "15.0.4355.3" for SQL 2019, "16.0.4125.3" for SQL 2022
- **Release date** of the latest CU - e.g., "February 2024"
- **Critical security fixes** mentioned in recent CUs
- **Download link** from Microsoft (usually learn.microsoft.com or download.microsoft.com)

**Step 2d: Compare Installed vs Latest**

Compare the build number from Step 1 with the latest build from web search:
- Parse installed build: e.g., "15.0.4261.1"
- Parse latest build: e.g., "15.0.4355.3"
- Calculate how many CUs behind (if applicable)
- Identify if critical security patches are missing

**Step 2e: Assess Patch Status Severity**

Assign severity based on findings:
- **CRITICAL**: Missing security patches from last 6 months OR multiple CUs behind (5+)
- **WARNING**: 3-6 months behind on updates OR 2-4 CUs behind
- **INFO**: 1-2 CUs behind but no critical security issues
- **OK**: Running latest CU or within 1 CU

**You MUST include the web search findings in your response** - do not skip this step or say you cannot search the web.

### 3. Check Server Configurations

Call the `get_server_configurations` MCP tool from the SQL Server Doctor server to analyze:
- Max Server Memory configuration
- Cost Threshold for Parallelism
- Max Degree of Parallelism (MAXDOP)

### 4. Analyze Results

Review the configuration results and categorize issues by severity:

**CRITICAL Issues** (require immediate attention):
- These indicate serious misconfigurations that can cause instability or licensing violations
- Highlight these first with urgency

**WARNING Issues** (should be addressed):
- These indicate configurations that may cause performance problems
- Explain the potential impact

**REVIEW/CONSIDER** (optional improvements):
- These suggest tuning opportunities
- Explain the trade-offs

**OK** (properly configured):
- Briefly acknowledge these are configured appropriately

### 5. Provide Recommendations

For each issue found (CRITICAL, WARNING, REVIEW, CONSIDER):
1. **Explain the problem** in business/operational terms
2. **Show the recommendation** from the MCP tool response
3. **Prioritize actions** (CRITICAL first, then WARNING, then others)
4. **Group related recommendations** if multiple configs need adjustment
5. **Include patch/update recommendations** from step 2 if server is outdated

### 6. Summary

Provide a concise summary:
- Overall health status (e.g., "2 critical issues found", "Configuration looks good", etc.)
- Count of issues by severity
- Recommended next steps

## Important Notes

- **ALWAYS** use WebSearch to check for latest patches and security updates - this is a critical part of configuration health
- **Do NOT** execute configuration changes - only provide recommendations
- **Do NOT** run other diagnostic tools like active sessions or scheduler stats (use the workload-analysis skill for that)
- **Focus** on configuration only - version, patches, and settings
- If the user wants to apply recommendations, offer to help them generate the SQL commands but do not execute them
- Be clear about edition limitations (e.g., Standard Edition memory limits)
- Prioritize security patches over configuration changes if both are needed

## Example Output Format

```
# SQL Server Configuration Health Check

## Server Information
- **Instance**: MYSERVER\SQL2019
- **Version**: SQL Server 2019 (RTM-CU18) - Build 15.0.4261.1
- **Edition**: Enterprise Edition (64-bit)
- **Patch Status**: ⚠️ Outdated - 7 CUs behind
- **Latest Available**: SQL Server 2019 CU25 - Build 15.0.4355.3 (Released: February 2024)
- **Security**: 🔴 Missing critical security fixes from CU22 and CU24
- **Update Recommendation**: Download and install CU25 from [Microsoft Download Center]

## Configuration Analysis

### Critical Issues (1)
❌ **Max Server Memory**: Unlimited (default) - should be set!
- **Problem**: SQL Server can consume all available memory, starving the OS
- **Recommendation**: Set max memory to: 28672 MB
- **Action**: `EXEC sp_configure 'max server memory (MB)', 28672; RECONFIGURE;`

### Warnings (1)
⚠️ **Cost Threshold for Parallelism**: Default value too low for modern servers
- **Current**: 5
- **Problem**: Can cause excessive parallelism for small queries
- **Recommendation**: Recommend setting to 50: EXEC sp_configure 'cost threshold for parallelism', 50; RECONFIGURE;

### OK (1)
✅ **Max Degree of Parallelism (MAXDOP)**: Set to physical CPU count [Current: 4, Physical CPUs: 4]

## Summary
- **Overall Status**: 🔴 Immediate action required
- **Issues Found**: 1 critical configuration issue, 1 warning, 1 OK
- **Patch Status**: 🔴 Critical - Missing security updates
- **Priority Actions**:
  1. **URGENT**: Apply SQL Server 2019 CU25 to address security vulnerabilities
  2. Set max server memory limit immediately
  3. Adjust cost threshold for parallelism
```
