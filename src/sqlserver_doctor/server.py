"""SQL Server Doctor MCP Server - Main server implementation."""

from enum import Enum
from typing import Any
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from sqlserver_doctor.utils.connection import get_connection
from sqlserver_doctor.utils.logger import setup_logger

# Setup logger
logger = setup_logger("sqlserver_doctor.server")

# Create the FastMCP server instance
mcp = FastMCP("SQL Server Doctor")
logger.info("SQL Server Doctor MCP Server initialized")


# Response models
class ServerVersionResponse(BaseModel):
    """Response model for server version information."""

    version: str = Field(description="SQL Server version string")
    server_name: str = Field(description="SQL Server instance name")
    success: bool = Field(description="Whether the query was successful")
    error: str | None = Field(None, description="Error message if query failed")


class DatabaseInfo(BaseModel):
    """Information about a single database."""

    name: str = Field(description="Database name")
    database_id: int = Field(description="Database ID")
    create_date: str = Field(description="Database creation date")
    state_desc: str = Field(description="Database state (e.g., ONLINE, OFFLINE)")
    recovery_model_desc: str = Field(description="Recovery model (SIMPLE, FULL, BULK_LOGGED)")
    compatibility_level: int = Field(description="Database compatibility level")


class DatabaseListResponse(BaseModel):
    """Response model for database list."""

    databases: list[DatabaseInfo] = Field(description="List of databases")
    count: int = Field(description="Total number of databases")
    success: bool = Field(description="Whether the query was successful")
    error: str | None = Field(None, description="Error message if query failed")


class ActiveSessionInfo(BaseModel):
    """Information about an active SQL Server session."""

    sql_text: str = Field(description="SQL query text being executed")
    session_id: int = Field(description="Session ID")
    status: str = Field(description="Request status (running, suspended, etc.)")
    command: str = Field(description="Command type (SELECT, INSERT, etc.)")
    cpu_seconds: float = Field(description="CPU time in seconds")
    elapsed_seconds: float = Field(description="Total elapsed time in seconds")
    reads: int = Field(description="Number of disk reads")
    logical_reads: int = Field(description="Number of logical reads")
    wait_time: int = Field(description="Current wait time in milliseconds")
    last_wait_type: str | None = Field(None, description="Last wait type encountered")
    blocking_session_id: int | None = Field(None, description="Session ID causing blocking, if any")
    connect_time: str | None = Field(None, description="Connection start time")
    dop: int = Field(description="Degree of parallelism")
    host_name: str | None = Field(None, description="Client host name")
    program_name: str | None = Field(None, description="Client program name")
    database_name: str | None = Field(None, description="Database name")
    login_name: str | None = Field(None, description="Login name")


class ActiveSessionsResponse(BaseModel):
    """Response model for active sessions list."""

    sessions: list[ActiveSessionInfo] = Field(description="List of active sessions")
    count: int = Field(description="Total number of active sessions")
    success: bool = Field(description="Whether the query was successful")
    error: str | None = Field(None, description="Error message if query failed")


class SchedulerStats(BaseModel):
    """Statistics for a single SQL Server scheduler."""

    scheduler_id: int = Field(description="Scheduler ID")
    current_tasks_count: int = Field(description="Total tasks assigned to this scheduler")
    runnable_tasks_count: int = Field(
        description="Tasks waiting for CPU (CPU pressure indicator if > 0)"
    )
    work_queue_count: int = Field(description="Work items in the queue")
    pending_disk_io_count: int = Field(description="Pending I/O operations")


class SchedulerStatsResponse(BaseModel):
    """Response model for scheduler statistics."""

    schedulers: list[SchedulerStats] = Field(description="List of scheduler statistics")
    scheduler_count: int = Field(description="Number of schedulers (typically = CPU cores)")
    total_runnable_tasks: int = Field(
        description="Total tasks waiting for CPU across all schedulers"
    )
    avg_runnable_per_scheduler: float = Field(
        description="Average runnable tasks per scheduler"
    )
    cpu_pressure_detected: bool = Field(
        description="Whether CPU pressure is detected (runnable tasks > 0)"
    )
    interpretation: str = Field(description="Interpretation guide for the results")
    success: bool = Field(description="Whether the query was successful")
    error: str | None = Field(None, description="Error message if query failed")


class ConfigSeverity(str, Enum):
    """Severity levels for configuration items."""

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    REVIEW = "REVIEW"
    CONSIDER = "CONSIDER"


class ConfigItem(BaseModel):
    """Information about a single server configuration item."""

    name: str = Field(description="Configuration name")
    value: int | str = Field(description="Current configured value")
    severity: ConfigSeverity = Field(description="Severity level of the configuration status")
    message: str = Field(description="Human-readable status message with context")
    recommendation: str | None = Field(None, description="Recommended action to take, if any")


class ServerConfigResponse(BaseModel):
    """Response model for server configuration diagnostics."""

    configurations: list[ConfigItem] = Field(description="List of configuration items")
    success: bool = Field(description="Whether the query was successful")
    error: str | None = Field(None, description="Error message if query failed")


class MemoryStats(BaseModel):
    """Memory statistics and diagnostics for SQL Server."""

    server_name: str = Field(description="SQL Server instance name")
    check_timestamp: str = Field(description="Timestamp when check was performed")
    ple_seconds: int = Field(description="Page Life Expectancy in seconds")
    ple_minutes: int = Field(description="Page Life Expectancy in minutes")
    ple_status: str = Field(description="PLE status: OK, WARNING, or CRITICAL")
    memory_grants_pending: int = Field(description="Number of queries waiting for memory grants")
    grants_status: str = Field(description="Memory grants status: OK or CRITICAL")
    target_memory_mb: int = Field(description="Target server memory in MB")
    total_memory_mb: int = Field(description="Total server memory currently allocated in MB")
    memory_difference_mb: int = Field(description="Difference between target and total memory (MB)")
    memory_pressure_status: str = Field(description="Memory pressure status: OK, WATCH, or UNDER_PRESSURE")
    max_server_memory_mb: int = Field(description="Max server memory configuration setting (MB)")
    buffer_pool_committed_mb: int = Field(description="Buffer pool committed memory (MB)")
    buffer_pool_target_mb: int = Field(description="Buffer pool target memory (MB)")
    overall_assessment: str = Field(description="Overall memory health assessment with recommendations")


class MemoryStatsResponse(BaseModel):
    """Response model for memory statistics."""

    memory_stats: MemoryStats | None = Field(None, description="Memory statistics and diagnostics")
    success: bool = Field(description="Whether the query was successful")
    error: str | None = Field(None, description="Error message if query failed")


# Tools
@mcp.tool()
def get_server_version() -> ServerVersionResponse:
    """
    Get SQL Server version and instance information.

    Returns detailed version information about the connected SQL Server instance,
    including the version string and server name.
    """
    logger.info("Tool called: get_server_version")
    try:
        conn = get_connection()
        results = conn.execute_query(
            """
            SELECT
                @@VERSION AS Version,
                @@SERVERNAME AS ServerName
            """
        )

        if results:
            logger.info(f"Retrieved server version: {results[0]['ServerName']}")
            return ServerVersionResponse(
                version=results[0]["Version"],
                server_name=results[0]["ServerName"],
                success=True,
            )
        else:
            logger.warning("No results returned from server version query")
            return ServerVersionResponse(
                version="",
                server_name="",
                success=False,
                error="No results returned from query",
            )

    except Exception as e:
        logger.error(f"Error getting server version: {str(e)}")
        return ServerVersionResponse(
            version="",
            server_name="",
            success=False,
            error=str(e),
        )


@mcp.tool()
def list_databases() -> DatabaseListResponse:
    """
    List all databases on the SQL Server instance.

    Returns information about all databases including name, state, recovery model,
    and compatibility level. This is useful for understanding the server's database
    landscape and identifying databases that may need attention.
    """
    logger.info("Tool called: list_databases")
    try:
        conn = get_connection()
        results = conn.execute_query(
            """
            SELECT
                name,
                database_id,
                CONVERT(VARCHAR, create_date, 120) AS create_date,
                state_desc,
                recovery_model_desc,
                compatibility_level
            FROM sys.databases
            ORDER BY name
            """
        )

        databases = [DatabaseInfo(**db) for db in results]
        logger.info(f"Successfully retrieved {len(databases)} database(s)")

        return DatabaseListResponse(
            databases=databases,
            count=len(databases),
            success=True,
        )

    except Exception as e:
        logger.error(f"Error listing databases: {str(e)}")
        return DatabaseListResponse(
            databases=[],
            count=0,
            success=False,
            error=str(e),
        )


@mcp.tool()
def get_active_sessions() -> ActiveSessionsResponse:
    """
    Get currently active sessions and queries on the SQL Server instance.

    Returns detailed information about active sessions including currently executing
    SQL text, CPU usage, wait statistics, blocking information, and client details.
    This is useful for monitoring server activity, identifying performance issues,
    and detecting blocking situations.

    Filters out system databases (master, msdb) and the monitoring query itself.
    """
    logger.info("Tool called: get_active_sessions")
    try:
        conn = get_connection()
        results = conn.execute_query(
            """
            SELECT
                sqltext.TEXT as sql_text,
                req.session_id,
                req.status,
                req.command,
                CONVERT(NUMERIC(8,1), req.cpu_time/1000.0) as cpu_seconds,
                CONVERT(NUMERIC(8,1), req.total_elapsed_time/1000.0) as elapsed_seconds,
                req.reads,
                req.logical_reads,
                req.wait_time,
                req.last_wait_type,
                req.blocking_session_id,
                CONVERT(VARCHAR, con.connect_time, 120) as connect_time,
                req.dop,
                dm_es.host_name,
                dm_es.program_name,
                DB_NAME(req.database_id) as database_name,
                dm_es.login_name
            FROM sys.dm_exec_requests req
            LEFT OUTER JOIN sys.dm_exec_sessions dm_es ON dm_es.session_id = req.session_id
            LEFT OUTER JOIN sys.dm_exec_connections con ON con.connection_id = req.connection_id
            CROSS APPLY sys.dm_exec_sql_text(req.sql_handle) AS sqltext
            WHERE sqltext.TEXT NOT LIKE '%sqltext.TEXT%'
            AND DB_NAME(req.database_id) NOT IN ('master', 'msdb')
            """
        )

        sessions = [ActiveSessionInfo(**session) for session in results]
        logger.info(f"Successfully retrieved {len(sessions)} active session(s)")

        return ActiveSessionsResponse(
            sessions=sessions,
            count=len(sessions),
            success=True,
        )

    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        return ActiveSessionsResponse(
            sessions=[],
            count=0,
            success=False,
            error=str(e),
        )


@mcp.tool()
def get_scheduler_stats() -> SchedulerStatsResponse:
    """
    Get SQL Server scheduler statistics for CPU and Disk IO queue monitoring. Used for preassure detection.

    Returns average scheduler information including runnable tasks (CPU queue depth) and pending I/O operations. 
    This is critical for identifying CPU pressure and performance bottlenecks.

    Key metrics interpretation:
    - scheduler_count: Number of schedulers (typically = CPU cores)
    - avg_runnable_tasks: Average runnable tasks per scheduler. 0 - 0.5: No CPU pressure, 0.5-2: Mild pressure, 2-5: Moderate pressure, >5: Critical, immediate action needed
    - avg_pending_disk_io_count: Average pending I/O operations per scheduler. 0-1: Normal I/O activity, 1-5: Moderate I/O pressure, 5-10: High I/O pressure, >10: Critical I/O bottleneck, check disk subsystem

    """
    logger.info("Tool called: get_scheduler_stats")
    try:
        conn = get_connection()
        results = conn.execute_query(
            """
            SELECT
                COUNT(*) AS scheduler_count,
                AVG(1.0*runnable_tasks_count) AS avg_runnable_tasks,
                AVG(1.0*pending_disk_io_count) AS avg_pending_disk_io_count
            FROM sys.dm_os_schedulers
            WHERE scheduler_id < 255
            """
        )

        # Extract aggregated metrics from single result row
        if not results:
            raise Exception("No scheduler statistics returned")

        result = results[0]
        scheduler_count = result["scheduler_count"]
        avg_runnable = float(result["avg_runnable_tasks"])
        avg_pending_io = float(result["avg_pending_disk_io_count"])

        # Calculate total runnable tasks (approximate from average)
        total_runnable = int(avg_runnable * scheduler_count)
        cpu_pressure = avg_runnable > 0

        # Build interpretation based on updated metrics
        interpretation_parts = []

        # CPU pressure interpretation
        if avg_runnable == 0:
            interpretation_parts.append("No CPU pressure detected (avg runnable: 0)")
        elif avg_runnable <= 0.5:
            interpretation_parts.append(f"Minimal CPU pressure (avg runnable: {avg_runnable:.2f})")
        elif avg_runnable <= 2:
            interpretation_parts.append(f"MILD CPU PRESSURE (avg runnable: {avg_runnable:.2f})")
        elif avg_runnable <= 5:
            interpretation_parts.append(f"MODERATE CPU PRESSURE (avg runnable: {avg_runnable:.2f}) - Consider query optimization")
        else:
            interpretation_parts.append(f"CRITICAL CPU PRESSURE (avg runnable: {avg_runnable:.2f}) - Immediate action needed!")

        # I/O pressure interpretation
        if avg_pending_io <= 1:
            interpretation_parts.append(f"Normal I/O activity (avg pending I/O: {avg_pending_io:.2f})")
        elif avg_pending_io <= 5:
            interpretation_parts.append(f"MODERATE I/O PRESSURE (avg pending I/O: {avg_pending_io:.2f})")
        elif avg_pending_io <= 10:
            interpretation_parts.append(f"HIGH I/O PRESSURE (avg pending I/O: {avg_pending_io:.2f}) - Check disk performance")
        else:
            interpretation_parts.append(f"CRITICAL I/O BOTTLENECK (avg pending I/O: {avg_pending_io:.2f}) - Check disk subsystem immediately!")

        interpretation = " | ".join(interpretation_parts)

        logger.info(
            f"Retrieved scheduler stats: {scheduler_count} schedulers, "
            f"avg runnable: {avg_runnable:.2f}, avg pending I/O: {avg_pending_io:.2f}"
        )

        return SchedulerStatsResponse(
            schedulers=[],  # Empty list since we're returning aggregates
            scheduler_count=scheduler_count,
            total_runnable_tasks=total_runnable,
            avg_runnable_per_scheduler=avg_runnable,
            cpu_pressure_detected=cpu_pressure,
            interpretation=interpretation,
            success=True,
        )

    except Exception as e:
        logger.error(f"Error getting scheduler stats: {str(e)}")
        return SchedulerStatsResponse(
            schedulers=[],
            scheduler_count=0,
            total_runnable_tasks=0,
            avg_runnable_per_scheduler=0.0,
            cpu_pressure_detected=False,
            interpretation="",
            success=False,
            error=str(e),
        )


@mcp.tool()
def get_server_configurations() -> ServerConfigResponse:
    """
    Get SQL Server configuration diagnostics and recommendations.

    Returns configuration analysis for key SQL Server settings including:
    - Max Server Memory: Memory allocation limits and edition compliance
    - Cost Threshold for Parallelism: Parallel query execution threshold
    - Max Degree of Parallelism (MAXDOP): Maximum parallel query threads

    Each configuration includes current value, severity assessment (OK, WARNING,
    CRITICAL, REVIEW, CONSIDER), contextual message, and actionable recommendations.
    """
    logger.info("Tool called: get_server_configurations")
    try:
        conn = get_connection()
        results = conn.execute_query(
            """
            -- Max Server Memory Configuration
            SELECT
                CONVERT(VARCHAR(100), c.name) as name,
                CAST(c.value_in_use AS INT) as value,
                CONVERT(VARCHAR(20),
                    CASE
                        WHEN c.value_in_use = 2147483647 THEN 'CRITICAL'
                        WHEN CAST(SERVERPROPERTY('EngineEdition') AS INT) = 2 AND c.value_in_use > 131072 THEN 'CRITICAL'
                        WHEN c.value_in_use > (i.physical_memory_kb / 1024 * 0.9) THEN 'WARNING'
                        WHEN c.value_in_use < (i.physical_memory_kb / 1024 * 0.5)
                            AND c.value_in_use < (CASE WHEN CAST(SERVERPROPERTY('EngineEdition') AS INT) = 2 THEN 131072 ELSE 999999999 END)
                            THEN 'WARNING'
                        ELSE 'OK'
                    END
                ) as severity,
                CONVERT(VARCHAR(1000),
                    CASE
                        WHEN c.value_in_use = 2147483647 THEN
                            'Unlimited (default) - should be set! [Server Memory: ' + CAST(i.physical_memory_kb / 1024 AS VARCHAR) + ' MB, Edition: ' + CAST(SERVERPROPERTY('Edition') AS VARCHAR) + ']'
                        WHEN CAST(SERVERPROPERTY('EngineEdition') AS INT) = 2 AND c.value_in_use > 131072
                            THEN 'Exceeds Standard Edition 128 GB limit! [Configured: ' + CAST(c.value_in_use AS VARCHAR) + ' MB, Limit: 131072 MB]'
                        WHEN CAST(SERVERPROPERTY('EngineEdition') AS INT) = 2 AND c.value_in_use >= 131072
                            THEN 'At Standard Edition limit [Configured: ' + CAST(c.value_in_use AS VARCHAR) + ' MB]'
                        WHEN c.value_in_use > (i.physical_memory_kb / 1024 * 0.9)
                            THEN 'Too high - leave memory for OS [Configured: ' + CAST(c.value_in_use AS VARCHAR) + ' MB, Server Total: ' + CAST(i.physical_memory_kb / 1024 AS VARCHAR) + ' MB]'
                        WHEN c.value_in_use < (i.physical_memory_kb / 1024 * 0.5)
                            AND c.value_in_use < (CASE WHEN CAST(SERVERPROPERTY('EngineEdition') AS INT) = 2 THEN 131072 ELSE 999999999 END)
                            THEN 'Too low - SQL Server artificially limited [Configured: ' + CAST(c.value_in_use AS VARCHAR) + ' MB, Server Total: ' + CAST(i.physical_memory_kb / 1024 AS VARCHAR) + ' MB]'
                        ELSE 'Configured appropriately [Configured: ' + CAST(c.value_in_use AS VARCHAR) + ' MB]'
                    END
                ) as message,
                CONVERT(VARCHAR(1000),
                    CASE
                        WHEN c.value_in_use = 2147483647 THEN
                            CASE
                                WHEN CAST(SERVERPROPERTY('EngineEdition') AS INT) = 2 THEN
                                    'Set max memory to: ' + CAST(
                                        CASE WHEN 131072 < (i.physical_memory_kb / 1024) - 4096
                                             THEN 131072
                                             ELSE (i.physical_memory_kb / 1024) - 4096
                                        END AS VARCHAR) + ' MB (Standard Edition 128 GB limit)'
                                ELSE
                                    'Set max memory to: ' + CAST((i.physical_memory_kb / 1024) - 4096 AS VARCHAR) + ' MB'
                            END
                        WHEN CAST(SERVERPROPERTY('EngineEdition') AS INT) = 2 AND c.value_in_use > 131072 THEN
                            'Reduce to 131072 MB (128 GB - Standard Edition limit)'
                        ELSE NULL
                    END
                ) as recommendation
            FROM sys.configurations c
            CROSS JOIN sys.dm_os_sys_info i
            WHERE c.name = 'max server memory (MB)'

            UNION ALL

            -- Cost Threshold for Parallelism
            SELECT
                CONVERT(VARCHAR(100), name) as name,
                CAST(value_in_use AS INT) as value,
                CONVERT(VARCHAR(20),
                    CASE
                        WHEN value_in_use = 5 THEN 'WARNING'
                        WHEN value_in_use < 25 THEN 'CONSIDER'
                        WHEN value_in_use >= 25 AND value_in_use <= 50 THEN 'OK'
                        ELSE 'OK'
                    END
                ) as severity,
                CONVERT(VARCHAR(1000),
                    CASE
                        WHEN value_in_use = 5 THEN 'Default value too low for modern servers [Current: ' + CAST(value_in_use AS VARCHAR) + ']'
                        WHEN value_in_use < 25 THEN 'Consider increasing to 25-50 to reduce excessive parallelism [Current: ' + CAST(value_in_use AS VARCHAR) + ']'
                        WHEN value_in_use >= 25 AND value_in_use <= 50 THEN 'Good starting point [Current: ' + CAST(value_in_use AS VARCHAR) + ']'
                        ELSE 'Custom tuned [Current: ' + CAST(value_in_use AS VARCHAR) + ']'
                    END
                ) as message,
                CONVERT(VARCHAR(1000),
                    CASE
                        WHEN value_in_use = 5 THEN 'Recommend setting to 50: EXEC sp_configure ''cost threshold for parallelism'', 50; RECONFIGURE;'
                        ELSE NULL
                    END
                ) as recommendation
            FROM sys.configurations
            WHERE name = 'cost threshold for parallelism'

            UNION ALL

            -- Max Degree of Parallelism
            SELECT
                CONVERT(VARCHAR(100), c.name) as name,
                CAST(c.value_in_use AS INT) as value,
                CONVERT(VARCHAR(20),
                    CASE
                        WHEN c.value_in_use = 0 THEN 'WARNING'
                        WHEN c.value_in_use = 1 THEN 'WARNING'
                        WHEN c.value_in_use > 8 THEN 'CONSIDER'
                        WHEN c.value_in_use = (i.cpu_count / i.hyperthread_ratio) AND (i.cpu_count / i.hyperthread_ratio) <= 8
                            THEN 'OK'
                        ELSE 'REVIEW'
                    END
                ) as severity,
                CONVERT(VARCHAR(1000),
                    CASE
                        WHEN c.value_in_use = 0 THEN 'Unlimited parallelism can cause CXPACKET waits [CPUs: ' + CAST(i.cpu_count AS VARCHAR) + ', Physical: ' + CAST(i.cpu_count / i.hyperthread_ratio AS VARCHAR) + ']'
                        WHEN c.value_in_use = 1 THEN 'Parallelism disabled - multi-core not utilized [CPUs: ' + CAST(i.cpu_count AS VARCHAR) + ']'
                        WHEN c.value_in_use > 8 THEN 'Values > 8 rarely help, often hurt [Current: ' + CAST(c.value_in_use AS VARCHAR) + ', CPUs: ' + CAST(i.cpu_count AS VARCHAR) + ']'
                        WHEN c.value_in_use = (i.cpu_count / i.hyperthread_ratio) AND (i.cpu_count / i.hyperthread_ratio) <= 8
                            THEN 'Set to physical CPU count [Current: ' + CAST(c.value_in_use AS VARCHAR) + ', Physical CPUs: ' + CAST(i.cpu_count / i.hyperthread_ratio AS VARCHAR) + ']'
                        ELSE 'Check if optimal for workload [Current: ' + CAST(c.value_in_use AS VARCHAR) + ', CPUs: ' + CAST(i.cpu_count AS VARCHAR) + ', Physical: ' + CAST(i.cpu_count / i.hyperthread_ratio AS VARCHAR) + ']'
                    END
                ) as message,
                CONVERT(VARCHAR(1000),
                    CASE
                        WHEN c.value_in_use = 0 THEN
                            'Recommend setting to: ' + CAST(
                                CASE
                                    WHEN (i.cpu_count / i.hyperthread_ratio) <= 8
                                    THEN (i.cpu_count / i.hyperthread_ratio)
                                    ELSE 8
                                END AS VARCHAR
                            ) + ' (physical CPU count, max 8)'
                        ELSE NULL
                    END
                ) as recommendation
            FROM sys.configurations c
            CROSS JOIN sys.dm_os_sys_info i
            WHERE c.name = 'max degree of parallelism'

            ORDER BY name
            """
        )

        configurations = [
            ConfigItem(
                name=row["name"],
                value=row["value"],
                severity=ConfigSeverity(row["severity"]),
                message=row["message"],
                recommendation=row["recommendation"],
            )
            for row in results
        ]

        logger.info(f"Successfully retrieved {len(configurations)} configuration(s)")

        return ServerConfigResponse(
            configurations=configurations,
            success=True,
        )

    except Exception as e:
        logger.error(f"Error getting server configurations: {str(e)}")
        return ServerConfigResponse(
            configurations=[],
            success=False,
            error=str(e),
        )


@mcp.tool()
def get_memory_stats() -> MemoryStatsResponse:
    """
    Get SQL Server memory statistics to identify memory pressure issues.

    Returns comprehensive memory diagnostics including:
    - Page Life Expectancy (PLE): How long pages stay in buffer pool
      * <300 seconds: CRITICAL - severe memory pressure
      * <1000 seconds: WARNING - moderate memory pressure
      * >=1000 seconds: OK - healthy memory
    - Memory Grants Pending: Queries waiting for memory allocation (any > 0 is CRITICAL)
    - Memory Pressure: Gap between target and actual memory allocation
    - Buffer Pool: Committed and target memory usage
    - Overall Assessment: Aggregated health status with actionable recommendations

    This tool is essential for diagnosing if SQL Server needs more memory or if there
    are memory configuration issues.
    """
    logger.info("Tool called: get_memory_stats")
    try:
        conn = get_connection()
        results = conn.execute_query(
            """
            WITH memory_metrics AS (
                SELECT
                    MAX(CASE WHEN counter_name = 'Page life expectancy' AND object_name LIKE '%Buffer Node%'
                        THEN cntr_value END) AS ple_seconds,
                    MAX(CASE WHEN counter_name = 'Memory Grants Pending' AND object_name LIKE '%Memory Manager%'
                        THEN cntr_value END) AS grants_pending,
                    MAX(CASE WHEN counter_name = 'Target Server Memory (KB)'
                        THEN cntr_value/1024 END) AS target_mb,
                    MAX(CASE WHEN counter_name = 'Total Server Memory (KB)'
                        THEN cntr_value/1024 END) AS total_mb
                FROM sys.dm_os_performance_counters
                WHERE counter_name IN ('Page life expectancy', 'Memory Grants Pending',
                                      'Target Server Memory (KB)', 'Total Server Memory (KB)')
            )
            SELECT
                @@SERVERNAME AS server_name,
                CONVERT(VARCHAR, GETDATE(), 120) AS check_timestamp,

                -- PLE Metrics
                ple_seconds,
                ple_seconds/60 AS ple_minutes,
                CONVERT(VARCHAR(20),
                    CASE
                        WHEN ple_seconds < 300 THEN 'CRITICAL'
                        WHEN ple_seconds < 1000 THEN 'WARNING'
                        ELSE 'OK'
                    END
                ) AS ple_status,

                -- Memory Grants
                grants_pending AS memory_grants_pending,
                CONVERT(VARCHAR(20), CASE WHEN grants_pending > 0 THEN 'CRITICAL' ELSE 'OK' END) AS grants_status,

                -- Memory Allocation
                target_mb AS target_memory_mb,
                total_mb AS total_memory_mb,
                target_mb - total_mb AS memory_difference_mb,
                CONVERT(VARCHAR(20),
                    CASE
                        WHEN target_mb - total_mb > 1024 THEN 'UNDER_PRESSURE'
                        WHEN target_mb - total_mb > 512 THEN 'WATCH'
                        ELSE 'OK'
                    END
                ) AS memory_pressure_status,

                -- Config
                (SELECT CAST(value AS INT) FROM sys.configurations WHERE name = 'max server memory (MB)') AS max_server_memory_mb,
                (SELECT committed_kb/1024 FROM sys.dm_os_sys_info) AS buffer_pool_committed_mb,
                (SELECT committed_target_kb/1024 FROM sys.dm_os_sys_info) AS buffer_pool_target_mb,

                -- Overall Assessment
                CONVERT(VARCHAR(1000),
                    CASE
                        WHEN grants_pending > 0 THEN 'CRITICAL: Queries waiting for memory!'
                        WHEN ple_seconds < 300 AND (target_mb - total_mb) > 1024 THEN 'CRITICAL: Low PLE and memory pressure detected'
                        WHEN ple_seconds < 300 THEN 'WARNING: Low Page Life Expectancy'
                        WHEN (target_mb - total_mb) > 1024 THEN 'WARNING: SQL Server wants more memory'
                        ELSE 'OK: Memory appears healthy'
                    END
                ) AS overall_assessment
            FROM memory_metrics
            """
        )

        if results:
            stats = MemoryStats(**results[0])
            logger.info(
                f"Retrieved memory stats: PLE={stats.ple_seconds}s, "
                f"Assessment={stats.overall_assessment}"
            )
            return MemoryStatsResponse(
                memory_stats=stats,
                success=True,
            )
        else:
            logger.warning("No results returned from memory stats query")
            return MemoryStatsResponse(
                success=False,
                error="No results returned from query",
            )

    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        return MemoryStatsResponse(
            success=False,
            error=str(e),
        )
