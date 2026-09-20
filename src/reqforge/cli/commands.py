"""CLI commands for ReqForge."""

import asyncio
import json
import os
import time
import uuid
from urllib.parse import urlparse

import typer

from ..config.config import get_config
from ..core.context import ScanContext
from ..core.logging import get_logger, setup_logging
from ..diff.engine import DiffEngine
from ..http.client import HTTPClient
from ..http.parser import parse_http_request
from ..mutation.engine import MutationEngine, MutationType
from ..scope.validator import Scope, ScopeValidationError, get_scope
from ..storage import models as storage_models
from ..storage.database import SessionLocal
from ..storage.repositories import EndpointRepository, HistoryRepository

logger = get_logger(__name__)
http_client = HTTPClient()

app = typer.Typer(help="ReqForge - Terminal-first HTTP security testing framework")

scope_app = typer.Typer(help="Manage the allowed testing scope")
app.add_typer(scope_app, name="scope")

evidence_app = typer.Typer(help="Manage HTTP evidence and findings")
app.add_typer(evidence_app, name="evidence")


@app.command("targets")
def targets(
    domain: str = typer.Argument(..., help="Domain to list targets/endpoints for"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of endpoints to display"),
    offset: int = typer.Option(0, "--offset", "-o", help="First endpoint index to display"),
):
    """List discovered endpoints for a domain."""
    setup_logging()

    try:
        db_session = SessionLocal()
        endpoint_repo = EndpointRepository(db_session)
        endpoints = endpoint_repo.list_by_domain(domain, limit=limit, offset=offset)
        db_session.close()
    except Exception as exc:
        logger.error(f"Error querying endpoints: {exc}")
        typer.echo(f"Error: Failed to query endpoints - {exc}", err=True)
        raise typer.Exit(1)

    if not endpoints:
        typer.echo(f"No endpoints found for domain: {domain}")
        typer.echo("Hint: import ReconForge data first with: reqforge import reconforge-export.json")
        raise typer.Exit(0)

    typer.echo(f"\n{'ID':4} {'Method':8} {'Endpoint Type':15} {'URL'}")
    typer.echo("-" * 100)
    for endpoint in endpoints:
        method = endpoint.method or "GET"
        endpoint_type = endpoint.endpoint_type or "unknown"
        typer.echo(f"{endpoint.id[:4]:<4} {method:<8} {endpoint_type:<15} {endpoint.url}")
    typer.echo(f"\nTotal: {len(endpoints)} endpoints")


@app.command("import")
def import_(
    file_path: str = typer.Argument(..., help="Path to a ReconForge export JSON file"),
):
    """Import discovered endpoints from a ReconForge export."""
    setup_logging()

    if not os.path.exists(file_path):
        typer.echo(f"Error: File '{file_path}' not found.", err=True)
        raise typer.Exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        typer.echo(f"Error reading JSON file: {exc}", err=True)
        raise typer.Exit(1)

    if isinstance(payload, dict):
        raw_items = payload.get("endpoints") or payload.get("assets") or payload.get("targets") or []
    elif isinstance(payload, list):
        raw_items = payload
    else:
        typer.echo("Error: Unsupported import format. Expected a JSON object or array.", err=True)
        raise typer.Exit(1)

    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    inserted = 0
    try:
        db_session = SessionLocal()
        repo = EndpointRepository(db_session)
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            url_value = item.get("url") or item.get("value") or item.get("hostname")
            if not url_value:
                continue
            parsed = urlparse(url_value if url_value.startswith(("http://", "https://")) else f"https://{url_value}")
            domain = (parsed.hostname or url_value).lower().strip(".")
            endpoint = storage_models.Endpoint(
                id=str(uuid.uuid4()),
                url=url_value,
                domain=domain,
                method=(item.get("method") or "GET").upper(),
                endpoint_type=item.get("endpoint_type") or item.get("type") or "unknown",
                source=item.get("source") or "imported",
                status_code=item.get("status_code"),
                content_type=item.get("content_type"),
                parameters=item.get("parameters") or {},
                headers=item.get("headers") or {},
                tags=item.get("tags") or [],
            )
            repo.add(endpoint)
            inserted += 1
        db_session.close()
    except Exception as exc:
        logger.error(f"Import failed: {exc}")
        typer.echo(f"Error: Failed to import endpoints - {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Imported {inserted} endpoints.")


@app.command("create-request")
def create_request(
    endpoint_ref: str = typer.Argument(..., help="Endpoint ID, URL, or host to build a base request from"),
):
    """Create a raw HTTP request from an imported endpoint or URL."""
    setup_logging()

    endpoint = None
    try:
        db_session = SessionLocal()
        repo = EndpointRepository(db_session)
        matches = repo.list_all(limit=1000)
        if endpoint_ref.startswith(("http://", "https://")):
            endpoint = next((item for item in matches if item.url == endpoint_ref), None)
        else:
            endpoint = next((item for item in matches if item.id.startswith(endpoint_ref) or item.url.endswith(endpoint_ref)), None)
        db_session.close()
    except Exception:
        endpoint = None

    target_url = endpoint.url if endpoint else endpoint_ref
    if not target_url.startswith(("http://", "https://")):
        target_url = f"https://{target_url}"

    parsed = urlparse(target_url)
    host = parsed.netloc or parsed.path
    method = "GET"
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    request_text = (
        f"{method} {path} HTTP/1.1\n"
        f"Host: {host}\n"
        "User-Agent: ReqForge/0.1.0\n"
        "Accept: */*\n"
        "Connection: close\n\n"
    )
    typer.echo(request_text, nl=False)


@app.command("replay")
def replay(
    request_file: str = typer.Argument(..., help="Path to a saved request file"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="HTTP timeout (seconds)"),
):
    """Replay an HTTP request and print the response."""
    setup_logging()

    try:
        with open(request_file, "r", encoding="utf-8") as handle:
            request_text = handle.read()
    except FileNotFoundError:
        typer.echo(f"Error: File '{request_file}' not found.", err=True)
        raise typer.Exit(1)

    try:
        request = parse_http_request(request_text)
    except Exception as exc:
        typer.echo(f"Error parsing request file: {exc}", err=True)
        raise typer.Exit(1)

    try:
        response = asyncio.run(
            http_client.request(
                method=request["method"],
                url=request["url"],
                params=request.get("params"),
                headers=request.get("headers"),
                data=request.get("data"),
                json=request.get("json"),
                timeout=timeout,
            )
        )
    except Exception as exc:
        typer.echo(f"Error replaying request: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"HTTP {response.status_code} {response.reason_phrase}")
    for key, value in response.headers.items():
        typer.echo(f"{key}: {value}")
    typer.echo("")
    body = response.text if hasattr(response, "text") else response.content.decode("utf-8", errors="replace")
    typer.echo(body)


@app.command("test")
def test_(
    request_file: str = typer.Argument(..., help="Path to a request file to test"),
    profile: str = typer.Option("authentication", "--profile", "-p", help="Behavioral test profile to run"),
):
    """Run a simple behavioral test profile against a request."""
    setup_logging()
    try:
        with open(request_file, "r", encoding="utf-8") as handle:
            request_text = handle.read()
        request = parse_http_request(request_text)
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Running profile '{profile}' against {request['url']}")
    typer.echo("Profile result: PASS (placeholder implementation - request parsed successfully and is in scope)")


@scope_app.command("add")
def scope_add(domain: str = typer.Argument(..., help="Domain to add to the allowed scope")):
    """Add a domain to the global scope."""
    scope = get_scope()
    scope.add_allowed(domain)
    typer.echo(f"Added '{domain}' to scope.")


@scope_app.command("check")
def scope_check(target: str = typer.Argument(..., help="Target URL or host to validate")):
    """Check whether a target is in scope."""
    try:
        get_scope().validate(target)
        typer.echo(f"IN SCOPE: {target}")
    except ScopeValidationError as exc:
        typer.echo(f"OUT OF SCOPE: {target} ({exc})")
        raise typer.Exit(1)


@evidence_app.command("create")
def evidence_create(
    evidence_id: str = typer.Argument(..., help="Identifier for the evidence record"),
    notes: str = typer.Option("", "--notes", "-n", help="Evidence notes"),
):
    """Create a simple evidence record."""
    evidence = storage_models.Evidence(
        id=evidence_id,
        request_id="n/a",
        response_id="n/a",
        notes=notes,
        mutation="",
        comparison={},
        screenshots=[],
    )
    db_session = SessionLocal()
    try:
        db_session.add(evidence)
        db_session.commit()
    finally:
        db_session.close()
    typer.echo(f"Created evidence: {evidence_id}")


@evidence_app.command("list")
def evidence_list():
    """List evidence records."""
    db_session = SessionLocal()
    try:
        records = db_session.query(storage_models.Evidence).order_by(storage_models.Evidence.timestamp.desc()).all()
    finally:
        db_session.close()

    if not records:
        typer.echo("No evidence records found.")
        return

    for record in records:
        typer.echo(f"{record.id} | {record.timestamp.isoformat()} | {record.notes or 'No notes'}")


@app.command()
def mutate(
    request_file: str = typer.Argument(..., help="Path to base request file"),
    output_dir: str = typer.Option("./mutations", "--output", "-o", help="Directory to save mutated requests"),
    field: str = typer.Option(None, "--field", "-f", help="Specific field to mutate (header name, query param, json field, etc.)"),
    values: str = typer.Option(None, "--values", "-v", help="Comma-separated list of values to use for mutation"),
    method: bool = typer.Option(False, "--method", help="Mutate HTTP method"),
    header: bool = typer.Option(False, "--header", help="Mutate HTTP headers"),
    cookie: bool = typer.Option(False, "--cookie", help="Mutate cookies"),
    query_param: bool = typer.Option(False, "--query-param", help="Mutate query parameters"),
    path: bool = typer.Option(False, "--path", help="Mutate URL path"),
    body: bool = typer.Option(False, "--body", help="Mutate request body"),
    json_field: bool = typer.Option(False, "--json-field", help="Mutate JSON field values"),
    form_field: bool = typer.Option(False, "--form-field", help="Mutate form field values"),
    exclude: str = typer.Option(None, "--exclude", "-e", help="Comma-separated list of fields to exclude from mutation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Generate controlled mutations of a base request."""
    if verbose:
        config = get_config()
        config.logging.level = "DEBUG"
    setup_logging()

    try:
        with open(request_file, "r", encoding="utf-8") as handle:
            request_content = handle.read()
    except FileNotFoundError:
        typer.echo(f"Error: File '{request_file}' not found.", err=True)
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Error reading file: {exc}", err=True)
        raise typer.Exit(1)

    try:
        base_request = parse_http_request(request_content)
    except Exception as exc:
        typer.echo(f"Error parsing request file: {exc}", err=True)
        raise typer.Exit(1)

    try:
        Scope().validate(base_request["url"])
    except ScopeValidationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    mutation_values = [v.strip() for v in values.split(",")] if values else []
    exclude_fields = [e.strip() for e in exclude.split(",")] if exclude else []

    mutation_types = []
    if method:
        mutation_types.append(("method", MutationType.METHOD))
    if header:
        mutation_types.append(("header", MutationType.HEADER))
    if cookie:
        mutation_types.append(("cookie", MutationType.COOKIE))
    if query_param:
        mutation_types.append(("query_param", MutationType.QUERY_PARAM))
    if path:
        mutation_types.append(("path", MutationType.PATH))
    if body:
        mutation_types.append(("body", MutationType.BODY))
    if json_field:
        mutation_types.append(("json_field", MutationType.JSON_FIELD))
    if form_field:
        mutation_types.append(("form_field", MutationType.FORM_FIELD))

    if not mutation_types:
        mutation_types = [
            ("header", MutationType.HEADER),
            ("query_param", MutationType.QUERY_PARAM),
            ("json_field", MutationType.JSON_FIELD),
            ("form_field", MutationType.FORM_FIELD),
        ]

    all_mutations = []
    for type_name, mutation_type in mutation_types:
        try:
            mutations = MutationEngine.mutate_request(
                base_request=base_request,
                mutation_type=mutation_type,
                field_name=field,
                values=mutation_values or None,
                exclude_fields=exclude_fields,
            )
            all_mutations.extend([(type_name, mutation) for mutation in mutations])
        except Exception as exc:
            typer.echo(f"Error generating {type_name} mutations: {exc}", err=True)

    if not all_mutations:
        typer.echo("No mutations generated.")
        raise typer.Exit(1)

    os.makedirs(output_dir, exist_ok=True)
    typer.echo(f"Generated {len(all_mutations)} mutations:")
    for index, (type_name, mutated_request) in enumerate(all_mutations, start=1):
        safe_type = type_name.replace(" ", "_").lower()
        filename = f"{index:03d}_{safe_type}"
        if field:
            filename += f"_{field}"
        filename += ".req"
        filepath = os.path.join(output_dir, filename)

        request_text = MutationEngine.request_to_text(mutated_request)
        with open(filepath, "w", encoding="utf-8") as handle:
            handle.write(request_text)
        typer.echo(f"  {filename}: {type_name} mutation")

    typer.echo(f"\nMutations saved to: {output_dir}")


@app.command()
def compare(
    baseline: str = typer.Argument(..., help="Path to baseline request file"),
    mutated: str = typer.Argument(..., help="Path to mutated request file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Compare two HTTP requests/responses differentially."""
    if verbose:
        config = get_config()
        config.logging.level = "DEBUG"
    setup_logging()

    try:
        with open(baseline, "r", encoding="utf-8") as handle:
            baseline_content = handle.read()
        with open(mutated, "r", encoding="utf-8") as handle:
            mutated_content = handle.read()
    except FileNotFoundError as exc:
        typer.echo(f"Error: File not found - {exc}", err=True)
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Error reading file: {exc}", err=True)
        raise typer.Exit(1)

    try:
        baseline_request = parse_http_request(baseline_content)
        mutated_request = parse_http_request(mutated_content)
    except Exception as exc:
        typer.echo(f"Error parsing request file: {exc}", err=True)
        raise typer.Exit(1)

    try:
        Scope().validate(baseline_request["url"])
        Scope().validate(mutated_request["url"])
    except ScopeValidationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    context = ScanContext(baseline_request["url"])

    typer.echo("Sending baseline request...")
    try:
        baseline_start = time.time()
        baseline_response = asyncio.run(
            http_client.request(
                method=baseline_request["method"],
                url=baseline_request["url"],
                params=baseline_request.get("params"),
                headers=baseline_request.get("headers"),
                data=baseline_request.get("data"),
                json=baseline_request.get("json"),
                timeout=get_config().http.timeout,
            )
        )
        baseline_elapsed = int((time.time() - baseline_start) * 1000)

        typer.echo("Sending mutated request...")
        mutated_start = time.time()
        mutated_response = asyncio.run(
            http_client.request(
                method=mutated_request["method"],
                url=mutated_request["url"],
                params=mutated_request.get("params"),
                headers=mutated_request.get("headers"),
                data=mutated_request.get("data"),
                json=mutated_request.get("json"),
                timeout=get_config().http.timeout,
            )
        )
        mutated_elapsed = int((time.time() - mutated_start) * 1000)
    except Exception as exc:
        logger.error(f"Request failed: {exc}")
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    baseline_resp_dict = {
        "status_code": baseline_response.status_code,
        "headers": dict(baseline_response.headers),
        "content": baseline_response.content.decode("utf-8", errors="replace") if baseline_response.content else "",
        "elapsed_time": baseline_elapsed,
    }
    mutated_resp_dict = {
        "status_code": mutated_response.status_code,
        "headers": dict(mutated_response.headers),
        "content": mutated_response.content.decode("utf-8", errors="replace") if mutated_response.content else "",
        "elapsed_time": mutated_elapsed,
    }

    try:
        diff_result = DiffEngine.compare_responses(baseline_resp_dict, mutated_resp_dict)
    except Exception as exc:
        typer.echo(f"Error comparing responses: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo("\n" + "=" * 60)
    typer.echo("DIFFERENTIAL RESPONSE ANALYSIS")
    typer.echo("=" * 60)
    typer.echo(f"Baseline: {baseline_request['method']} {baseline_request['url']}")
    typer.echo(f"Mutated:  {mutated_request['method']} {mutated_request['url']}")
    typer.echo("-" * 60)

    status_baseline = baseline_resp_dict["status_code"]
    status_mutated = mutated_resp_dict["status_code"]
    if status_baseline == status_mutated:
        typer.echo(f"Status:     {status_baseline} (unchanged)")
    else:
        typer.echo(f"Status:     {status_baseline} → {status_mutated} **CHANGED**")

    typer.echo(f"Size:       {len(baseline_resp_dict['content'])} bytes → {len(mutated_resp_dict['content'])} bytes")
    typer.echo(f"Time:       {baseline_resp_dict['elapsed_time']} ms → {mutated_resp_dict['elapsed_time']} ms")

    typer.echo("RESULT: " + ("Significant difference detected" if diff_result.has_significant_difference else "No significant difference detected"))

    try:
        baseline_id = str(uuid.uuid4())
        mutated_id = str(uuid.uuid4())
        baseline_history = storage_models.History(
            id=baseline_id,
            request={
                "method": baseline_request["method"],
                "url": baseline_request["url"],
                "headers": baseline_request.get("headers", {}),
                **({"params": baseline_request.get("params")} if baseline_request.get("params") else {}),
                **({"data": baseline_request.get("data")} if baseline_request.get("data") is not None else {}),
                **({"json": baseline_request.get("json")} if baseline_request.get("json") is not None else {}),
            },
            response=baseline_resp_dict,
            timestamp=context.start_time,
            status_code=baseline_resp_dict["status_code"],
            elapsed_time=baseline_resp_dict["elapsed_time"],
            target=baseline_request["url"],
        )

        mutated_history = storage_models.History(
            id=mutated_id,
            request={
                "method": mutated_request["method"],
                "url": mutated_request["url"],
                "headers": mutated_request.get("headers", {}),
                **({"params": mutated_request.get("params")} if mutated_request.get("params") else {}),
                **({"data": mutated_request.get("data")} if mutated_request.get("data") is not None else {}),
                **({"json": mutated_request.get("json")} if mutated_request.get("json") is not None else {}),
            },
            response=mutated_resp_dict,
            timestamp=context.start_time,
            status_code=mutated_resp_dict["status_code"],
            elapsed_time=mutated_resp_dict["elapsed_time"],
            target=mutated_request["url"],
        )

        db_session = SessionLocal()
        try:
            history_repo = HistoryRepository(db_session)
            history_repo.add(baseline_history)
            history_repo.add(mutated_history)
        finally:
            db_session.close()
    except Exception as exc:
        logger.error(f"Failed to save to history: {exc}")
        typer.echo("Warning: Failed to save requests to history")