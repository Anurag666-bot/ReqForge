# ReqForge Architecture and Integration Plan

This document outlines the architecture of the existing ReconForge repository and defines the plan for building ReqForge as a complementary terminal-first HTTP security testing framework.

## 1. ReconForge Audit Summary

### 1.1 Overall Architecture
ReconForge follows a modular architecture with a shared core engine used by both CLI and web interfaces. The main components are:

- **Models**: Data representations (Asset, Endpoint, DNSRecord, Technology, Finding, Scan)
- **Core**: Orchestration engine, scope validation, context, scheduler
- **Discovery**: Subdomain discovery, DNS enumeration, endpoint discovery, robots.txt, sitemap analysis
- **Scanners**: HTTP scanning, header analysis, TLS analysis, technology detection
- **Analysis**: Finding correlation, risk assessment, deduplication
- **Storage**: SQLite database with SQLAlchemy ORM, repository pattern
- **Utils**: Hashing, timing, URL utilities
- **API**: FastAPI backend with REST endpoints and WebSocket for live updates
- **Reporting**: JSON, HTML, and terminal reporters
- **CLI**: Typer-based command-line interface

### 1.2 Key Data Models
ReconForge already defines several key data models that will be relevant for shared use:

- **Asset**: Represents a discovered asset (domain, subdomain, IP, etc.) with hostname, IP addresses, URL, timestamps, tags, and metadata.
- **Endpoint**: Represents a discovered endpoint with URL, type, source, status code, content type, method, parameters, headers, etc.
- **Finding**: Represents a security finding with title, description, severity, confidence, asset, category, evidence, impact, remediation, references, tags, and metadata.
- **Scan**: Represents a completed scan with target, mode, status, timestamps, relationships to assets, endpoints, DNS records, technologies, and findings.
- **Technology**: Represents a detected technology with name, category, confidence, evidence, hostname, version, and metadata.
- **DNSRecord**: Represents a DNS record with hostname, record type, value, TTL, priority, port, weight, source, validity, tags, and metadata.

### 1.3 Scope Enforcement
ReconForge has a robust scope validation engine (`reconforge.core.scope.Scope`) that:
- Supports allowed/blocked domains with wildcard support
- Extracts hostnames from URLs
- Validates targets against scope rules
- Provides a global scope instance
- Includes URL normalization for consistent comparison

### 1.4 Storage
ReconForge uses SQLite with SQLAlchemy ORM. The storage layer includes:
- Database initialization and connection management
- Repository pattern for saving and retrieving scans
- Relationships between scan and its assets/endpoints/findings/etc.

## 2. Division of Responsibilities

### 2.1 What Should Stay in ReconForge
ReconForge should remain focused on reconnaissance and asset discovery:
- Passive and active subdomain discovery
- DNS enumeration and record gathering
- HTTP/HTTPS probing for live host detection
- Port scanning (if implemented in future)
- Technology detection via HTTP response analysis
- Robots.txt and sitemap analysis
- Endpoint discovery through crawling and brute-forcing
- Attack-surface mapping and asset relationship tracking
- Recon-specific findings (e.g., subdomain takeover, exposed endpoints, technology version disclosures)
- Reconnaissance reporting (JSON, HTML, terminal)
- Live dashboard for attack surface visualization

### 2.2 What Should Move to Shared Libraries
The following components should be extracted into shared libraries to avoid duplication:

1. **Data Models**: Common definitions for:
   - Target, Scope
   - Asset, Domain, Subdomain, IP, Port
   - URL, Endpoint, Parameter
   - Technology
   - HTTPRequest, HTTPResponse (to be defined)
   - Finding, Evidence
   - Scan, Run
   - Tag, Note
   These should be designed to be extensible and usable by both ReconForge and ReqForge.

2. **Scope Engine**: The scope validation logic from `reconforge.core.scope` should be shared, allowing both tools to enforce the same scope policies.

3. **Utilities**: Hashing, timing, URL normalization/parsing utilities.

4. **Base Storage Layer**: While each tool may have its own database, a common interface for data persistence (e.g., base repository classes) could be shared.

5. **Configuration Management**: Common configuration loading (though each tool may have different settings).

### 2.3 What Should Belong to ReqForge
ReqForge will focus on HTTP security testing and will include:

- **Request Handling**: 
  - Raw HTTP request parser (compatible with Burp/Suite format)
  - Request builder and modifier
  - HTTP client with timeout, retry, proxy support
  
- **Replay Engine**:
  - Execute saved requests and display responses
  - Support for multiple output formats (terminal, JSON, quiet/verbose)
  
- **Mutation Engine**:
  - Controlled mutation of requests (method, headers, cookies, query parameters, path, body)
  - Support for parameter-specific mutation with value lists
  - Generation of mutated requests with unique IDs
  
- **Differential Response Engine**:
  - Compare baseline and mutated responses
  - Analyze differences in status, size, headers, JSON structure, body similarity, timing, redirects
  - Produce neutral, observation-focused comparisons
  
- **Testing Framework**:
  - Pluggable test profiles (authentication, authorization, parameter behavior, etc.)
  - Behavioral comparison-based testing (not automatic exploitation)
  
- **Evidence System**:
  - Save interesting requests/responses as evidence
  - Attach notes, tags, screenshots/path references
  
- **Request History**:
  - Store request metadata locally with replay/export capabilities
  
- **Finding Management**:
  - Track HTTP-specific findings with states (OBSERVED, INTERESTING, NEEDS_REVIEW, CONFIRMED, FALSE_POSITIVE)
  
- **Scope Integration**:
  - Use shared scope engine to enforce boundaries before any request
  
- **Burp Suite Integration**:
  - Import/export raw HTTP requests
  - Proxy support for traffic forwarding through Burp
  - HAR support where practical
  
- **Terminal UI**:
  - Rich-based output with tables, panels, progress bars
  - JSON/quiet/verbose modes
  
- **Configuration**:
  - TOML-based configuration (~/.config/reqforge/config.toml)

### 2.4 What Should Be Integrated Through an API/File Format
The primary integration points between ReconForge and ReqForge will be:

1. **ReconForge → ReqForge**: 
   - Export discovered endpoints/assets from ReconForge in a shared JSON format
   - ReqForge imports this data to populate its target list for testing
   - Example workflow:
     ```bash
     reconforge scan example.com --export recon.json
     reqforge import recon.json
     reqforge targets example.com   # show imported targets
     reqforge select endpoint 01    # choose an endpoint to test
     reqforge create-request endpoint 01  # generate a base request for mutation
     ```

2. **ReqForge → ReconForge**:
   - Optionally, ReqForge could export interesting endpoints or findings back to ReconForge for correlation
   - Less critical for initial version but possible future enhancement

3. **Burp Suite Integration**:
   - Both directions via file-based import/export of HTTP requests
   - Proxy support for ReqForge to send traffic through Burp for manual inspection
   - Future: Potential Burp extension for tighter integration

## 3. Shared Data Model Proposal

We propose a common JSON-based data format for exchanging information between tools. Each object will have:
- `id`: Stable unique identifier (UUID v4 preferred)
- `created_at`, `updated_at`: Timestamps
- `source`: Which tool created the object (e.g., "reconforge", "reqforge")
- `target`: The target domain/scope this object relates to
- `tags`: List of string tags for categorization
- `metadata`: Free-form key-value storage for tool-specific properties

### 3.1 Core Objects

#### Target
```json
{
  "id": "target_01H...",
  "type": "target",
  "value": "example.com",
  "source": "reconforge",
  "target": "example.com",
  "tags": ["in-scope"],
  "metadata": {}
}
```

#### Scope
```json
{
  "id": "scope_01H...",
  "type": "scope",
  "value": ["example.com", "*.example.com"],
  "source": "reconforge",
  "target": "example.com",
  "tags": [],
  "metadata": {
    "allow_subdomains": true,
    "blocked_domains": ["admin.example.com"]
  }
}
```

#### Asset
```json
{
  "id": "asset_01H...",
  "type": "asset",
  "hostname": "api.example.com",
  "ip_addresses": ["93.184.216.34"],
  "url": "https://api.example.com",
  "source": "reconforge",
  "target": "example.com",
  "tags": ["discovered", "subdomain"],
  "metadata": {
    "first_seen": "2026-09-18T10:00:00Z",
    "last_seen": "2026-09-18T10:00:00Z",
    "is_active": true,
    "scope_validated": true
  }
}
```

#### Endpoint
```json
{
  "id": "endpoint_01H...",
  "type": "endpoint",
  "url": "https://api.example.com/users",
  "method": "GET",
  "source": "reconforge",
  "target": "example.com",
  "tags": ["api", "discovered"],
  "metadata": {
    "endpoint_type": "api",
    "status_code": 200,
    "content_type": "application/json",
    "content_length": 1234,
    "discovered_at": "2026-09-18T10:00:00Z",
    "last_tested": null,
    "is_accessible": true,
    "parameters": {"page": {"type": "integer"}},
    "headers": {"Accept": "application/json"}
  }
}
```

#### Parameter
```json
{
  "id": "param_01H...",
  "type": "parameter",
  "name": "user_id",
  "location": "query",  // query, header, cookie, path, body-json, body-form
  "data_type": "integer",
  "source": "reconforge",
  "target": "example.com",
  "tags": [],
  "metadata": {}
}
```

#### Technology
```json
{
  "id": "tech_01H...",
  "type": "technology",
  "name": "nginx",
  "category": "web_server",
  "confidence": 0.95,
  "evidence": ["Server: nginx/1.18.0"],
  "hostname": "example.com",
  "source": "reconforge",
  "target": "example.com",
  "tags": [],
  "metadata": {
    "version": "1.18.0",
    "first_seen": "2026-09-18T10:00:00Z",
    "last_seen": "2026-09-18T10:00:00Z"
  }
}
```

#### HTTPRequest
```json
{
  "id": "req_01H...",
  "type": "http_request",
  "method": "POST",
  "url": "https://example.com/api/login",
  "source": "reqforge",
  "target": "example.com",
  "tags": ["baseline"],
  "metadata": {
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer {{TOKEN}}"
    },
    "body": {
      "username": "{{USER}}",
      "password": "{{PASSWORD}}"
    },
    "http_version": "HTTP/1.1"
  }
}
```

#### HTTPResponse
```json
{
  "id": "resp_01H...",
  "type": "http_response",
  "request_id": "req_01H...",
  "source": "reqforge",
  "target": "example.com",
  "tags": [],
  "metadata": {
    "status_code": 200,
    "status_text": "OK",
    "headers": {
      "Content-Type": "application/json",
      "Set-Cookie": "session=abc123"
    },
    "body": "{\"success\":true}",
    "body_size": 23,
    "elapsed_time": 184,
    "redirect_count": 0,
    "timestamp": "2026-09-18T10:00:00Z"
  }
}
```

#### Finding
```json
{
  "id": "finding_01H...",
  "type": "finding",
  "title": "Reflected XSS in search parameter",
  "description": "The search parameter reflects user input without proper escaping.",
  "severity": "MEDIUM",
  "confidence": 0.8,
  "asset": "asset_01H...",  // or endpoint ID
  "category": "xss",
  "source": "reqforge",
  "target": "example.com",
  "tags": ["requires-manual-verification"],
  "metadata": {
    "evidence": ["req_01H...", "resp_01H..."],
    "impact": "Possible execution of arbitrary JavaScript in victim's browser",
    "remediation": "Implement proper output encoding",
    "references": ["https://owasp.org/www-community/attacks/xss/"],
    "timestamp": "2026-09-18T10:00:00Z",
    "state": "INTERESTING"  // OBSERVED, INTERESTING, NEEDS_REVIEW, CONFIRMED, FALSE_POSITIVE
  }
}
```

#### Evidence
```json
{
  "id": "evidence_01H...",
  "type": "evidence",
  "source": "reqforge",
  "target": "example.com",
  "tags": ["xss-test"],
  "metadata": {
    "request": "req_01H...",
    "response": "resp_01H...",
    "timestamp": "2026-09-18T10:00:00Z",
    "mutation": "changed search parameter to <script>alert(1)</script>",
    "comparison": {
      "baseline": "resp_01H...",
      "mutated": "resp_02H..."
    },
    "notes": "Parameter reflects input in JSON response",
    "screenshots": []
  }
}
```

#### Scan / Run
```json
{
  "id": "scan_01H...",
  "type": "scan",
  "source": "reqforge",
  "target": "example.com",
  "tags": ["daily-test"],
  "metadata": {
    "start_time": "2026-09-18T10:00:00Z",
    "end_time": "2026-09-18T10:05:00Z",
    "duration_seconds": 300,
    "requests_sent": 150,
    "findings_generated": 3,
    "profile_used": "authentication"
  }
}
```

### 3.2 ID Generation
IDs should be UUID version 4 for global uniqueness, prefixed by object type for readability (e.g., `asset_`, `endpoint_`, `req_`). This makes IDs human-readable while ensuring uniqueness.

### 3.3 Extensibility
The `metadata` field allows each tool to store additional properties without breaking the shared format. Tools should ignore unknown metadata fields when consuming data from other tools.

## 4. ReqForge Component Architecture

Based on the user's requirements and the audit of ReconForge, we propose the following component structure for ReqForge:

```
reqforge/
│
├── cli/                 # Command-line interface (Typer-based)
├── core/                # Core orchestration and context
├── http/                # HTTP client, request/response handling
├── mutation/            # Request mutation engine
├── diff/                # Differential response analysis
├── testing/             # Pluggable testing framework
├── scope/               # Scope validation (shared library)
├── storage/             # Local history and evidence storage (SQLite)
├── evidence/            # Evidence management
├── findings/            # Finding management
├── history/             # Request history management
├── integrations/        # External tool integrations
│   └── burp/            # Burp Suite specific utilities
├── output/              # Terminal formatting, reporting
├── config/              # Configuration management
└── tests/               # Unit and integration tests
```

### 4.1 Key Components Details

#### CLI (`cli/`)
- Typer-based interface with commands: `request`, `replay`, `mutate`, `compare`, `test`, `inspect`, `import`, `export`, `history`, `evidence`, `finding`, `scope`, `config`
- Automatic help generation with examples
- Support for `--json`, `--quiet`, `--verbose`, `--no-color` flags

#### Core (`core/`)
- Engine orchestrating workflows (similar to ReconForge but focused on HTTP testing)
- Context management for scan/run state
- Shared scope validation (imported from shared library)

#### HTTP (`http/`)
- Request parser for raw HTTP format (Burp-compatible)
- Request builder for creating requests from components
- Async HTTP client based on `httpx` with:
  - Timeout, retry, redirect handling
  - Proxy support (for Burp integration)
  - SSL verification
  - User-agent rotation
  - Request/response logging (with secret redaction)

#### Mutation (`mutation/`)
- Mutation categories: method, header, cookie, query parameter, path, body (JSON, form, raw)
- Template-based mutation using placeholders (e.g., `{{USER}}`)
- Value list generation for parameter sweeping
- Preservation of original request structure

#### Diff (`diff/`)
- Response comparison engine
- Status code difference
- Header comparison (added/removed/changed)
- Body similarity (using libraries like `difflib` or custom)
- JSON structure comparison (key presence/value types)
- Timing analysis
- Redirect chain comparison
- Reflection detection (checking if input appears in output)

#### Testing (`testing/`)
- Profile-based test execution (access-control, authentication, etc.)
- Each profile defines a set of mutations to apply
- Results framework capturing request, mutation, response, comparison, observation
- Confidence scoring based on difference significance

#### Scope (`scope/`)
- Imported shared scope validation library
- Provides `is_allowed()`, `validate()`, `normalize_url()` functions

#### Storage (`storage/`)
- SQLite database for local persistence
- Tables for: request history, evidence, findings, scans, targets
- Repository pattern for data access
- Migration schema for version updates

#### Evidence (`evidence/`)
- Creation and management of evidence records
- Association with requests, responses, mutations, comparisons
- Tagging and note-taking capabilities
- Export to JSON/filesystem

#### Findings (`findings/`)
- Tracking of HTTP-specific findings
- State management (OBSERVED → INTERESTING → NEEDS_REVIEW → CONFIRMED/FALSE_POSITIVE)
- Assignment of severity and confidence
- Evidence linking

#### History (`history/`)
- Storage of executed requests with metadata
- Replay, export, and inspection capabilities
- Filtering by target, status code, time, tags

#### Integrations (`integrations/burp/`)
- Utilities for importing/exporting Burp Suite request files
- Proxy configuration helpers
- Format converters (if needed)

#### Output (`output/`)
- Rich-based terminal rendering
- Tables, panels, progress bars, spinners
- Structured logging with severity colors
- JSON output formatter
- Report generation (summary, detailed)

#### Config (`config/`)
- TOML configuration file at `~/.config/reqforge/config.toml`
- Runtime configuration with environment variable override
- Sections: timeout, retries, concurrency, rate limit, user agent, proxy, scope, storage, redaction rules

## 5. Integration Workflow Examples

### 5.1 Basic ReconForge → ReqForge Flow
```bash
# Step 1: Run reconnaissance with ReconForge
reconforge scan example.com --export recon.json

# Step 2: Import discovered assets/endpoints into ReqForge
reqforge import recon.json

# Step 3: List imported targets
reqforge targets example.com

# Step 4: Select an endpoint for testing
reqforge select endpoint 03

# Step 5: Inspect the endpoint details
reqforge inspect endpoint 03

# Step 6: Generate a base request from the endpoint
reqforge create-request endpoint 03 > baseline.req

# Step 7: Review and customize the base request (optional)
# Edit baseline.req to add authentication headers, etc.

# Step 8: Replay the baseline request
reqforge replay baseline.req

# Step 9: Create mutations (e.g., test parameter values)
reqforge mutate baseline.req \
    --parameter user_id \
    --values 100,101,102 \
    --output mutations/

# Step 10: Compare responses differentially
reqforge compare baseline.req mutations/001.req

# Step 11: Run a test profile (e.g., authentication bypass)
reqforge test baseline.req --profile authentication

# Step 12: Save interesting results as evidence
reqforge evidence create RQ-003

# Step 13: View findings
reqforge finding list
reqforge finding show F-001
```

### 5.2 Burp Suite Integration
```bash
# Send a request through Burp for manual inspection
reqforge replay request.req --proxy http://127.0.0.1:8080

# Import a request from Burp
cp ~/Burp/Suite/requests/somereq.req ./imported.req
reqforge inspect imported.req

# Export a request to Burp for manual testing
reqforge export RQ-003 --format burp > burp_request.req
# Then load burp_request.req in Burp's Repeater or Intruder
```

### 5.3 Scope Enforcement
```bash
# Add scope constraints
reqforge scope add example.com
reqforge scope add "*.example.com"
reqforge scope block admin.example.com

# Check if a URL is in scope
reqforge scope check https://api.example.com/users
# Output: [ALLOW] api.example.com

# Attempt to test out-of-scope target (should be blocked)
reqforge replay request.req --url https://evil.com/
# Output: [BLOCK] evil.com - Reason: Target is outside configured scope.
```

## 6. Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Project setup, configuration, logging
- Shared data models (if creating separate shared repo) or initial models in ReqForge
- SQLite storage layer
- Basic CLI structure

### Phase 2: Request Handling (Weeks 3-4)
- Raw HTTP request/response parser
- HTTP client with timeout/retry
- Basic replay command
- Initial CLI commands: `request`, `replay`, `history`

### Phase 3: Mutation and Diff (Weeks 5-6)
- Mutation engine for headers, query parameters, body
- Differential response comparison
- Commands: `mutate`, `compare`

### Phase 4: Scope and Safety (Week 7)
- Integrated scope validation
- Rate limiting and concurrency control
- Secret redaction in logs
- Safety defaults (timeouts, size limits)

### Phase 5: ReconForge Integration (Week 8)
- Import/export functions for shared JSON format
- Target listing and selection from ReconForge data
- Example: `reqforge import recon.json`

### Phase 6: Evidence and Findings (Week 9)
- Evidence creation and management
- Finding tracking with states
- Commands: `evidence`, `finding`

### Phase 7: Testing Framework (Week 10)
- Pluggable test profiles
- Behavioral comparison-based tests
- Command: `test`

### Phase 8: Burp Integration (Week 11)
- Proxy support for traffic forwarding
- HAR import/export where practical
- Documentation for Burp workflow

### Phase 9: Polish and Documentation (Week 12)
- Terminal UI enhancements with Rich
- JSON output for all commands
- Comprehensive documentation
- Security review and hardening

## 7. Next Steps

Having completed the audit of ReconForge and produced this architecture/integration plan, the next step is to begin implementing ReqForge starting with Phase 1.

We will:
1. Set up the project structure in `/home/anurag/Desktop/ReqForge`
2. Initialize a Git repository
3. Create the configuration and logging systems
4. Implement the shared data models (or import from a shared library if we create one)
5. Build the SQLite storage layer
6. Scaffold the CLI with basic commands

We will follow the user's development process of working in small milestones, implementing, testing, running static checks, and updating documentation at each step.

## 8. Conclusion

This plan defines a clear separation of concerns where ReconForge focuses on reconnaissance and asset discovery, while ReqForge focuses on HTTP security testing, manipulation, and analysis. The shared data model and scope engine enable seamless integration between the tools, allowing security professionals to flow from asset discovery to targeted testing without duplicating effort. Burp Suite integration provides a bridge for manual validation and advanced testing when needed.

By adhering to the principles of modularity, reuse, and clear boundaries, we aim to build a professional, maintainable, and useful security testing ecosystem.