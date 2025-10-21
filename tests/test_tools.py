"""Tests for MCP server tools."""

from unittest.mock import patch, MagicMock
from sqlserver_doctor.server import (
    get_server_version,
    list_databases,
    get_active_sessions,
    get_scheduler_stats,
    get_server_configurations,
    ServerVersionResponse,
    DatabaseListResponse,
    ActiveSessionsResponse,
    SchedulerStatsResponse,
    ServerConfigResponse,
    ConfigSeverity,
)


class TestGetServerVersion:
    """Tests for get_server_version tool."""

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_version_success(self, mock_get_connection):
        """Test successful server version retrieval."""
        # Setup mock
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "Version": "Microsoft SQL Server 2019 (RTM) - 15.0.2000.5",
                "ServerName": "TESTSERVER",
            }
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = get_server_version()

        # Verify
        assert isinstance(result, ServerVersionResponse)
        assert result.success is True
        assert result.server_name == "TESTSERVER"
        assert "SQL Server 2019" in result.version
        assert result.error is None

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_version_no_results(self, mock_get_connection):
        """Test server version with no results."""
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = []
        mock_get_connection.return_value = mock_conn

        result = get_server_version()

        assert isinstance(result, ServerVersionResponse)
        assert result.success is False
        assert result.version == ""
        assert result.server_name == ""
        assert "No results returned" in result.error

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_version_error(self, mock_get_connection):
        """Test server version with database error."""
        mock_conn = MagicMock()
        mock_conn.execute_query.side_effect = Exception("Connection timeout")
        mock_get_connection.return_value = mock_conn

        result = get_server_version()

        assert isinstance(result, ServerVersionResponse)
        assert result.success is False
        assert "Connection timeout" in result.error


class TestListDatabases:
    """Tests for list_databases tool."""

    @patch("sqlserver_doctor.server.get_connection")
    def test_list_databases_success(self, mock_get_connection):
        """Test successful database listing."""
        # Setup mock
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "name": "master",
                "database_id": 1,
                "create_date": "2021-01-01 00:00:00",
                "state_desc": "ONLINE",
                "recovery_model_desc": "SIMPLE",
                "compatibility_level": 150,
            },
            {
                "name": "tempdb",
                "database_id": 2,
                "create_date": "2021-01-01 00:00:00",
                "state_desc": "ONLINE",
                "recovery_model_desc": "SIMPLE",
                "compatibility_level": 150,
            },
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = list_databases()

        # Verify
        assert isinstance(result, DatabaseListResponse)
        assert result.success is True
        assert result.count == 2
        assert len(result.databases) == 2
        assert result.databases[0].name == "master"
        assert result.databases[1].name == "tempdb"
        assert result.error is None

    @patch("sqlserver_doctor.server.get_connection")
    def test_list_databases_empty(self, mock_get_connection):
        """Test database listing with no databases."""
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = []
        mock_get_connection.return_value = mock_conn

        result = list_databases()

        assert isinstance(result, DatabaseListResponse)
        assert result.success is True
        assert result.count == 0
        assert len(result.databases) == 0

    @patch("sqlserver_doctor.server.get_connection")
    def test_list_databases_error(self, mock_get_connection):
        """Test database listing with error."""
        mock_conn = MagicMock()
        mock_conn.execute_query.side_effect = Exception("Permission denied")
        mock_get_connection.return_value = mock_conn

        result = list_databases()

        assert isinstance(result, DatabaseListResponse)
        assert result.success is False
        assert result.count == 0
        assert len(result.databases) == 0
        assert "Permission denied" in result.error

    @patch("sqlserver_doctor.server.get_connection")
    def test_list_databases_validates_data(self, mock_get_connection):
        """Test that database info is properly validated."""
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "name": "testdb",
                "database_id": 5,
                "create_date": "2024-01-01 12:00:00",
                "state_desc": "ONLINE",
                "recovery_model_desc": "FULL",
                "compatibility_level": 160,
            }
        ]
        mock_get_connection.return_value = mock_conn

        result = list_databases()

        assert result.success is True
        db = result.databases[0]
        assert db.name == "testdb"
        assert db.database_id == 5
        assert db.state_desc == "ONLINE"
        assert db.recovery_model_desc == "FULL"
        assert db.compatibility_level == 160


class TestGetActiveSessions:
    """Tests for get_active_sessions tool."""

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_active_sessions_success(self, mock_get_connection):
        """Test successful active sessions retrieval."""
        # Setup mock
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "sql_text": "SELECT * FROM users WHERE id = 123",
                "session_id": 52,
                "status": "running",
                "command": "SELECT",
                "cpu_seconds": 1.5,
                "elapsed_seconds": 2.3,
                "reads": 100,
                "logical_reads": 500,
                "wait_time": 0,
                "last_wait_type": None,
                "blocking_session_id": None,
                "connect_time": "2025-10-14 10:30:00",
                "dop": 1,
                "host_name": "WORKSTATION01",
                "program_name": "My Application",
                "database_name": "MyDatabase",
                "login_name": "myuser",
            },
            {
                "sql_text": "UPDATE orders SET status = 'processed'",
                "session_id": 53,
                "status": "suspended",
                "command": "UPDATE",
                "cpu_seconds": 0.5,
                "elapsed_seconds": 10.2,
                "reads": 50,
                "logical_reads": 200,
                "wait_time": 5000,
                "last_wait_type": "LCK_M_X",
                "blocking_session_id": 52,
                "connect_time": "2025-10-14 10:32:00",
                "dop": 1,
                "host_name": "WORKSTATION02",
                "program_name": "Batch Processor",
                "database_name": "MyDatabase",
                "login_name": "batchuser",
            },
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = get_active_sessions()

        # Verify
        assert isinstance(result, ActiveSessionsResponse)
        assert result.success is True
        assert result.count == 2
        assert len(result.sessions) == 2
        assert result.error is None

        # Check first session
        session1 = result.sessions[0]
        assert session1.session_id == 52
        assert session1.status == "running"
        assert session1.cpu_seconds == 1.5
        assert session1.blocking_session_id is None

        # Check second session (blocked)
        session2 = result.sessions[1]
        assert session2.session_id == 53
        assert session2.status == "suspended"
        assert session2.blocking_session_id == 52
        assert session2.last_wait_type == "LCK_M_X"

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_active_sessions_empty(self, mock_get_connection):
        """Test active sessions with no active queries."""
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = []
        mock_get_connection.return_value = mock_conn

        result = get_active_sessions()

        assert isinstance(result, ActiveSessionsResponse)
        assert result.success is True
        assert result.count == 0
        assert len(result.sessions) == 0

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_active_sessions_error(self, mock_get_connection):
        """Test active sessions with database error."""
        mock_conn = MagicMock()
        mock_conn.execute_query.side_effect = Exception("Insufficient permissions")
        mock_get_connection.return_value = mock_conn

        result = get_active_sessions()

        assert isinstance(result, ActiveSessionsResponse)
        assert result.success is False
        assert result.count == 0
        assert len(result.sessions) == 0
        assert "Insufficient permissions" in result.error


class TestGetSchedulerStats:
    """Tests for get_scheduler_stats tool."""

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_scheduler_stats_no_pressure(self, mock_get_connection):
        """Test scheduler stats with no CPU pressure."""
        # Setup mock - 4 CPU cores, no runnable tasks
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "scheduler_id": 0,
                "current_tasks_count": 5,
                "runnable_tasks_count": 0,
                "work_queue_count": 0,
                "pending_disk_io_count": 0,
            },
            {
                "scheduler_id": 1,
                "current_tasks_count": 3,
                "runnable_tasks_count": 0,
                "work_queue_count": 0,
                "pending_disk_io_count": 0,
            },
            {
                "scheduler_id": 2,
                "current_tasks_count": 4,
                "runnable_tasks_count": 0,
                "work_queue_count": 0,
                "pending_disk_io_count": 0,
            },
            {
                "scheduler_id": 3,
                "current_tasks_count": 2,
                "runnable_tasks_count": 0,
                "work_queue_count": 0,
                "pending_disk_io_count": 0,
            },
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = get_scheduler_stats()

        # Verify
        assert isinstance(result, SchedulerStatsResponse)
        assert result.success is True
        assert result.scheduler_count == 4
        assert result.total_runnable_tasks == 0
        assert result.avg_runnable_per_scheduler == 0.0
        assert result.cpu_pressure_detected is False
        assert "No CPU pressure" in result.interpretation
        assert result.error is None

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_scheduler_stats_with_pressure(self, mock_get_connection):
        """Test scheduler stats with CPU pressure detected."""
        # Setup mock - CPU pressure on scheduler 1 and 2
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "scheduler_id": 0,
                "current_tasks_count": 8,
                "runnable_tasks_count": 0,
                "work_queue_count": 0,
                "pending_disk_io_count": 0,
            },
            {
                "scheduler_id": 1,
                "current_tasks_count": 10,
                "runnable_tasks_count": 2,
                "work_queue_count": 5,
                "pending_disk_io_count": 1,
            },
            {
                "scheduler_id": 2,
                "current_tasks_count": 9,
                "runnable_tasks_count": 3,
                "work_queue_count": 2,
                "pending_disk_io_count": 0,
            },
            {
                "scheduler_id": 3,
                "current_tasks_count": 6,
                "runnable_tasks_count": 0,
                "work_queue_count": 0,
                "pending_disk_io_count": 0,
            },
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = get_scheduler_stats()

        # Verify
        assert isinstance(result, SchedulerStatsResponse)
        assert result.success is True
        assert result.scheduler_count == 4
        assert result.total_runnable_tasks == 5  # 0 + 2 + 3 + 0
        assert result.avg_runnable_per_scheduler == 1.25  # 5 / 4
        assert result.cpu_pressure_detected is True
        assert "CPU PRESSURE DETECTED" in result.interpretation
        assert "5 task(s) waiting for CPU" in result.interpretation
        assert result.error is None

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_scheduler_stats_error(self, mock_get_connection):
        """Test scheduler stats with database error."""
        mock_conn = MagicMock()
        mock_conn.execute_query.side_effect = Exception("Access denied")
        mock_get_connection.return_value = mock_conn

        result = get_scheduler_stats()

        assert isinstance(result, SchedulerStatsResponse)
        assert result.success is False
        assert result.scheduler_count == 0
        assert result.total_runnable_tasks == 0
        assert result.cpu_pressure_detected is False
        assert "Access denied" in result.error


class TestGetServerConfigurations:
    """Tests for get_server_configurations tool."""

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_configurations_success(self, mock_get_connection):
        """Test successful server configurations retrieval."""
        # Setup mock with all three configurations
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "name": "cost threshold for parallelism",
                "value": 50,
                "severity": "OK",
                "message": "Good starting point [Current: 50]",
                "recommendation": None,
            },
            {
                "name": "max degree of parallelism",
                "value": 4,
                "severity": "OK",
                "message": "Set to physical CPU count [Current: 4, Physical CPUs: 4]",
                "recommendation": None,
            },
            {
                "name": "max server memory (MB)",
                "value": 16384,
                "severity": "OK",
                "message": "Configured appropriately [Configured: 16384 MB]",
                "recommendation": None,
            },
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = get_server_configurations()

        # Verify
        assert isinstance(result, ServerConfigResponse)
        assert result.success is True
        assert len(result.configurations) == 3
        assert result.error is None

        # Check that all configs are OK
        for config in result.configurations:
            assert config.severity == ConfigSeverity.OK
            assert config.recommendation is None

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_configurations_with_warnings(self, mock_get_connection):
        """Test server configurations with warnings and recommendations."""
        # Setup mock with configurations that need attention
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "name": "cost threshold for parallelism",
                "value": 5,
                "severity": "WARNING",
                "message": "Default value too low for modern servers [Current: 5]",
                "recommendation": "Recommend setting to 50: EXEC sp_configure 'cost threshold for parallelism', 50; RECONFIGURE;",
            },
            {
                "name": "max degree of parallelism",
                "value": 0,
                "severity": "WARNING",
                "message": "Unlimited parallelism can cause CXPACKET waits [CPUs: 8, Physical: 4]",
                "recommendation": "Recommend setting to: 4 (physical CPU count, max 8)",
            },
            {
                "name": "max server memory (MB)",
                "value": 2147483647,
                "severity": "CRITICAL",
                "message": "Unlimited (default) - should be set! [Server Memory: 32768 MB, Edition: Enterprise Edition]",
                "recommendation": "Set max memory to: 28672 MB",
            },
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = get_server_configurations()

        # Verify
        assert isinstance(result, ServerConfigResponse)
        assert result.success is True
        assert len(result.configurations) == 3

        # Check cost threshold
        cost_threshold = result.configurations[0]
        assert cost_threshold.name == "cost threshold for parallelism"
        assert cost_threshold.value == 5
        assert cost_threshold.severity == ConfigSeverity.WARNING
        assert "Default value too low" in cost_threshold.message
        assert cost_threshold.recommendation is not None

        # Check MAXDOP
        maxdop = result.configurations[1]
        assert maxdop.name == "max degree of parallelism"
        assert maxdop.value == 0
        assert maxdop.severity == ConfigSeverity.WARNING
        assert "Unlimited parallelism" in maxdop.message
        assert maxdop.recommendation is not None

        # Check max memory
        max_memory = result.configurations[2]
        assert max_memory.name == "max server memory (MB)"
        assert max_memory.value == 2147483647
        assert max_memory.severity == ConfigSeverity.CRITICAL
        assert "Unlimited" in max_memory.message
        assert max_memory.recommendation is not None

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_configurations_mixed_severities(self, mock_get_connection):
        """Test server configurations with different severity levels."""
        # Setup mock with REVIEW and CONSIDER severities
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = [
            {
                "name": "cost threshold for parallelism",
                "value": 20,
                "severity": "CONSIDER",
                "message": "Consider increasing to 25-50 to reduce excessive parallelism [Current: 20]",
                "recommendation": None,
            },
            {
                "name": "max degree of parallelism",
                "value": 6,
                "severity": "REVIEW",
                "message": "Check if optimal for workload [Current: 6, CPUs: 8, Physical: 4]",
                "recommendation": None,
            },
            {
                "name": "max server memory (MB)",
                "value": 16384,
                "severity": "OK",
                "message": "Configured appropriately [Configured: 16384 MB]",
                "recommendation": None,
            },
        ]
        mock_get_connection.return_value = mock_conn

        # Execute
        result = get_server_configurations()

        # Verify different severities
        assert result.success is True
        assert result.configurations[0].severity == ConfigSeverity.CONSIDER
        assert result.configurations[1].severity == ConfigSeverity.REVIEW
        assert result.configurations[2].severity == ConfigSeverity.OK

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_configurations_error(self, mock_get_connection):
        """Test server configurations with database error."""
        mock_conn = MagicMock()
        mock_conn.execute_query.side_effect = Exception("Insufficient permissions")
        mock_get_connection.return_value = mock_conn

        result = get_server_configurations()

        assert isinstance(result, ServerConfigResponse)
        assert result.success is False
        assert len(result.configurations) == 0
        assert "Insufficient permissions" in result.error

    @patch("sqlserver_doctor.server.get_connection")
    def test_get_server_configurations_empty_results(self, mock_get_connection):
        """Test server configurations with empty results."""
        mock_conn = MagicMock()
        mock_conn.execute_query.return_value = []
        mock_get_connection.return_value = mock_conn

        result = get_server_configurations()

        assert isinstance(result, ServerConfigResponse)
        assert result.success is True
        assert len(result.configurations) == 0
        assert result.error is None
