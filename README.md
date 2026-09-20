# ReqForge

Terminal-first HTTP security testing framework for authorized security testing, bug bounty, and CTF competitions.

Part of the ReconForge ecosystem:

```
                 AUTHORIZED TARGET
                         │
                         ▼
                  ┌─────────────┐
                  │ ReconForge  │
                  └──────┬──────┘
                         │
                  discovered assets
                         │
                         ▼
                  ┌─────────────┐
                  │  ReqForge   │
                  └──────┬──────┘
                         │
                HTTP requests
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Automated tests        Burp Proxy
              │                     │
              └──────────┴──────────┘
                         ▼
                 Response Analysis
                         │
                         ▼
                    Evidence
                         │
                         ▼
                    Findings
                         │
                         ▼
                     Report
```

## Status

**Phase 1 Implementation Complete** ✅
- Project setup, configuration, logging
- Shared data models
- SQLite storage layer
- Basic CLI structure with request, history, replay, and scope commands
- HTTP client with async requests
- Scope validation engine
- Context management

## Features

- Raw HTTP request sending (with more request format support coming)
- Request history storage and retrieval
- Scope enforcement (shared with ReconForge)
- Basic replay functionality (to be enhanced)
- Rich terminal output with color and formatting
- JSON/quiet/verbose modes (in progress)
- Configuration via TOML file and environment variables
- Extensible architecture for mutation, differential analysis, and testing

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/your-username/reqforge.git
cd reqforge

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Using Pip (when published)

```bash
pip install reqforge
```

## Usage

```bash
# Send a simple GET request
reqforge request https://httpbin.org/get

# Send a POST request with JSON data
reqforge request https://httpbin.org/post --method POST --json '{"key":"value"}'

# Validate scope
reqforge scope check https://example.com --scope example.com,*.example.com

# View request history
reqforge history --limit 20

# Replay a request from a file (to be implemented)
# reqforge replay request.req

# Manage scope
reqforge scope add example.com
reqforge scope add "*.example.com"
reqforge scope block admin.example.com
```

## Configuration

ReqForge uses a TOML configuration file located at `~/.config/reqforge/config.toml`.

Example configuration:

```toml
[reqforge.http]
timeout = 30
retries = 3
concurrency = 20
user_agent = "ReqForge/0.1.0"
proxy = "http://127.0.0.1:8080"  # Optional: Burp or other proxy

[reqforge.scope]
allowed_domains = ["example.com", "*.example.com"]
blocked_domains = ["admin.example.com"]
allow_subdomains = true

[reqforge.storage]
database_url = "sqlite:///./reqforge.db"
echo = false

[reqforge.logging]
level = "INFO"
file = "~/.reqforge/reqforge.log"
```

Configuration can also be overridden via environment variables with the prefix `REQFORGE_` (e.g., `REQFORGE_HTTP_TIMEOUT=60`).

## Development

### Prerequisites

- Python 3.12+
- Git
- Make (optional)

### Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/reqforge.git
cd reqforge

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run test suite
pytest

# Run tests with coverage
pytest --cov=reqforge

# Run a specific test
pytest tests/test_cli.py::test_request_command
```

### Code Quality

```bash
# Check code style
ruff check .

# Format code
ruff check . --fix

# Type checking
mypy reqforge
```

## Architecture

ReqForge follows a modular architecture:

```
reqforge/
│
├── cli/                 # Command-line interface (Typer-based)
├── core/                # Core orchestration and context
├── http/                # HTTP client, request/response handling
├── mutation/            # Request mutation engine (future)
├── diff/                # Differential response analysis (future)
├── testing/             # Pluggable testing framework (future)
├── scope/               # Scope validation (shared library)
├── storage/             # Local history and evidence storage (SQLite)
├── evidence/            # Evidence management (future)
├── findings/            # Finding management (future)
├── history/             # Request history management (future)
├── integrations/        # External tool integrations
│   └── burp/            # Burp Suite specific utilities
├── output/              # Terminal formatting, reporting
├── config/              # Configuration management
└── tests/               # Unit and integration tests
```

## Data Models

ReqForge defines a shared data model for interoperability with ReconForge and other tools. Each object includes:
- `id`: Stable unique identifier (UUID v4)
- `created_at`, `updated_at`: Timestamps
- `source`: Which tool created the object
- `target`: The target domain/scope
- `tags`: List of string tags
- `metadata`: Free-form key-value storage

See [PLAN.md](PLAN.md) for the complete data model specification.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on submitting pull requests, reporting issues, and contributing to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

⚠️ **Important**: ReqForge is designed for authorized security testing only. Users must obtain explicit permission before testing any systems. Unauthorized testing is illegal and unethical.

See [SECURITY.md](SECURITY.md) for detailed security considerations and responsible use guidelines.

## Acknowledgments

- Inspired by ReconForge and other open-source security tools
- Built with Python, Typer, Rich, HTTPX, Pydantic, and SQLAlchemy