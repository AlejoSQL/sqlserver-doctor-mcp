# SQL Server Doctor MCP Server

A Model Context Protocol (MCP) server for SQL Server tuning, diagnostics, and performance analysis. This server exposes SQL Server management capabilities to LLM applications.

### Example Usage

Ask your LLM client questions to troubleshoot and diagnose SQL Server issues:

**Configuration checks:**
- "Check my SQL Server configuration"
- "Is my SQL Server properly configured?"
- "Verify server settings"

**General troubleshooting:**
- "Users are complaining about slow queries, what's happening?"
- "Is something blocking my database?"

**Workload analysis:**
- "Analyze current SQL Server workload"
- "What queries are currently running?"
- "Which query is using the most CPU?"
- "Is there CPU pressure on the server?"
- "Show me any blocked sessions"

## Features

Currently implemented tools:
- **get_server_version** - Get SQL Server version and instance information
- **list_databases** - List all databases with state, recovery model, and compatibility level
- **get_server_configurations** - Analyze critical server configurations (max memory, MAXDOP, cost threshold) with recommendations
- **get_active_sessions** - Monitor currently executing queries with CPU usage, wait stats, and blocking information
- **get_scheduler_stats** - Monitor CPU queue depth and detect CPU pressure with automatic interpretation

## Prerequisites

- Python 3.10 or higher
- SQL Server (any edition)
- ODBC Driver for SQL Server (Driver 17 recommended for macOS)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/sqlserver-doctor-mcp.git
   cd sqlserver-doctor-mcp
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your SQL Server connection details:

   **For SQL Server Authentication:**
   ```env
   SQL_SERVER_HOST=your-server.database.windows.net
   SQL_SERVER_PORT=1433
   SQL_SERVER_DATABASE=master
   SQL_SERVER_USER=your_username
   SQL_SERVER_PASSWORD=your_password
   SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server
   ```

   **For Windows Authentication (local):**
   ```env
   SQL_SERVER_HOST=localhost
   SQL_SERVER_PORT=1433
   SQL_SERVER_DATABASE=master
   SQL_SERVER_USER=
   SQL_SERVER_PASSWORD=
   SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server
   ```

## Usage with Claude Code

### Setup

1. In Claude Code, open MCP settings using the `/mcp edit` command

2. Add this configuration (replace `/path/to/` with your actual project path):

   ```json
   {
     "mcpServers": {
       "sqlserver-doctor": {
         "command": "/path/to/sqlserver-doctor-mcp/venv/bin/python3",
         "args": ["-m", "sqlserver_doctor.main"],
         "cwd": "/path/to/sqlserver-doctor-mcp"
       }
     }
   }
   ```

   **Important Notes:**
   - Use the **full path** to your venv's Python (e.g., `/Users/yourname/sqlserver-doctor-mcp/venv/bin/python3`)
   - On Windows, use: `"C:\\path\\to\\sqlserver-doctor-mcp\\venv\\Scripts\\python.exe"`
   - The server will automatically load settings from your `.env` file

3. Save the configuration and reload MCP servers in Claude Code

### Available Tools

Once connected, Claude can use these tools:

- **get_server_version()** - Returns SQL Server version and instance name
- **list_databases()** - Returns list of all databases with metadata (name, state, recovery model, compatibility level)
- **get_server_configurations()** - Returns configuration diagnostics and recommendations:
  - Max Server Memory analysis (with edition limits)
  - Cost Threshold for Parallelism evaluation
  - Max Degree of Parallelism (MAXDOP) assessment
  - Severity levels (OK, WARNING, CRITICAL, REVIEW, CONSIDER)
  - Context-rich messages with server specifications
  - Actionable SQL recommendations
- **get_active_sessions()** - Returns currently executing queries with detailed performance metrics:
  - SQL query text
  - Session ID, status, and command type
  - CPU time and elapsed time
  - Disk reads and logical reads
  - Wait time and wait type
  - Blocking session information
  - Client host, program, and login details
- **get_scheduler_stats()** - Returns CPU scheduler statistics with automatic interpretation:
  - Runnable task counts (CPU queue depth)
  - Work queue counts
  - Pending I/O operations
  - CPU pressure detection (tasks waiting for CPU)
  - Automatic interpretation of results

## Diagnostic Skills

This repository includes two diagnostic skills that provide intelligent workflows for using the MCP tools:

### 1. SQL Server Configuration Check (`sql-server-config-check`)

Verifies SQL Server configuration health by checking version and critical settings.

**Triggers on questions like:**
- "Check my SQL Server configuration"
- "Is my SQL Server properly configured?"
- "Verify server settings"

**What it does:**
1. Gets SQL Server version and edition
2. Analyzes max memory, MAXDOP, and cost threshold settings
3. Categorizes issues by severity (CRITICAL → WARNING → REVIEW → OK)
4. Provides prioritized, actionable recommendations

### 2. SQL Server Workload Analysis (`sql-server-workload-analysis`)

Analyzes current workload and resource pressure to identify performance bottlenecks.

**Triggers on questions like:**
- "Analyze SQL Server workload"
- "What's causing slow performance?"
- "Find blocking queries"
- "Is there CPU pressure?"

**What it does:**
1. Analyzes active sessions (blocking, long-running queries, resource consumption)
2. Checks CPU and I/O pressure via scheduler stats
3. Correlates findings (e.g., high CPU with specific sessions)
4. Explains wait types in plain language
5. Provides immediate actions, investigation steps, and preventive measures

### Using the Skills

**Option 1: Project-Local (Recommended)**

The skills in `.claude/skills/` work automatically when you're working in this project directory. No additional setup needed!

**Option 2: Global Installation**

To use these skills across all projects, copy them to your global Claude skills directory:

**macOS/Linux:**
```bash
cp .claude/skills/*.md ~/.config/claude/skills/
```

**Windows:**
```powershell
Copy-Item .claude\skills\*.md "$env:APPDATA\Claude\skills\"
```

Once installed (either way), Claude will automatically use these skills when you ask matching questions!

## Project Structure

```
sqlserver-doctor-mcp/
├── .claude/
│   └── skills/
│       ├── sql-server-config-check.md      # Configuration health check skill
│       └── sql-server-workload-analysis.md # Workload analysis skill
├── src/
│   └── sqlserver_doctor/
│       ├── __init__.py
│       ├── server.py          # FastMCP instance and tools
│       ├── main.py            # Entry point
│       └── utils/
│           ├── __init__.py
│           ├── connection.py  # SQL Server connection management
│           └── logger.py      # Logging configuration
├── tests/                     # Unit tests
├── pyproject.toml            # Project configuration
├── .env.example              # Example environment variables
└── README.md
```

## Roadmap

Future enhancements:
- Additional configuration checks (tempdb, database settings)
- Wait statistics analysis and trending
- Index fragmentation detection
- Query plan analysis
- Database health checks (file growth, backup status)
- Performance counter monitoring
- Deadlock detection and analysis
- Additional diagnostic skills for specialized scenarios

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
