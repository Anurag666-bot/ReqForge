"""
HTTP request parser for ReqForge.
Supports Burp Suite compatible request format.
"""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs


class HTTPRequestParser:
    """Parses HTTP requests in Burp Suite format."""

    @staticmethod
    def parse(request_text: str) -> Dict[str, Any]:
        """
        Parse an HTTP request from text.

        Args:
            request_text: Raw HTTP request text

        Returns:
            Dictionary containing method, url, headers, params, data, json
        """
        # Split into lines and remove empty lines at start/end
        lines = [line.rstrip() for line in request_text.strip().split('\n')]

        # Find the first non-empty line (should be the request line)
        request_line_idx = 0
        while request_line_idx < len(lines) and not lines[request_line_idx].strip():
            request_line_idx += 1

        if request_line_idx >= len(lines):
            raise ValueError("No request line found")

        # Parse request line: METHOD /path HTTP/1.x or METHOD http://host/path HTTP/1.x
        request_line = lines[request_line_idx].strip()
        request_parts = request_line.split(' ', 2)
        if len(request_parts) < 3:
            raise ValueError(f"Invalid request line: {request_line}")

        method = request_parts[0].upper()
        path = request_parts[1]
        http_version = request_parts[2]

        # Check if path is already a full URL
        if path.startswith('http://') or path.startswith('https://'):
            # Path is already a full URL, use it as-is
            url = path
            # Extract host from URL for Host header if not present
            parsed_url = urlparse(url)
            host = parsed_url.netloc
        else:
            # Path is not a full URL, construct URL from Host header
            # Find where headers end (empty line)
            header_end_idx = request_line_idx + 1
            while header_end_idx < len(lines) and lines[header_end_idx].strip():
                header_end_idx += 1

            # Parse headers
            headers = {}
            for i in range(request_line_idx + 1, header_end_idx):
                line = lines[i].strip()
                if not line:
                    continue
                if ':' not in line:
                    continue  # Skip malformed lines
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

            # Get Host header
            host = headers.get('Host', '')
            if not host:
                raise ValueError("No Host header found")

            # Determine scheme from headers or default to http
            scheme = 'https' if headers.get('X-Forwarded-Proto') == 'https' or \
                            headers.get('X-Forwarded-SSL') == 'on' else 'http'

            url = f"{scheme}://{host}{path}"

        # Find where headers end (empty line) - need to recalculate if we used the full URL path
        if not (path.startswith('http://') or path.startswith('https://')):
            # We already calculated header_end_idx above
            pass
        else:
            # Need to find header end for full URL case
            header_end_idx = request_line_idx + 1
            while header_end_idx < len(lines) and lines[header_end_idx].strip():
                header_end_idx += 1

        # Parse headers (need to do this for both cases)
        headers = {}
        for i in range(request_line_idx + 1, header_end_idx):
            line = lines[i].strip()
            if not line:
                continue
            if ':' not in line:
                continue  # Skip malformed lines
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()

        # Parse body (everything after the empty line)
        body_lines = lines[header_end_idx + 1:] if header_end_idx + 1 < len(lines) else []
        body = '\n'.join(body_lines)

        # Parse URL to extract query parameters
        parsed_url = urlparse(url)
        query_params = {}
        if parsed_url.query:
            query_params = parse_qs(parsed_url.query)
            # Convert lists to single values (take first value)
            query_params = {k: v[0] if v else '' for k, v in query_params.items()}
            # Reconstruct URL without query params for the request
            url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # Parse body based on Content-Type
        data = None
        json_data = None
        content_type = headers.get('Content-Type', '').lower()

        if body:
            if 'application/json' in content_type:
                try:
                    import json
                    json_data = json.loads(body)
                except (ValueError, TypeError):
                    # If JSON parsing fails, treat as raw data
                    data = body
            elif 'application/x-www-form-urlencoded' in content_type:
                # Parse form data
                data = parse_qs(body)
                # Convert lists to single values
                data = {k: v[0] if v else '' for k, v in data.items()}
            elif 'multipart/form-data' in content_type:
                # For now, treat as raw data - multipart parsing is complex
                data = body
            else:
                # Default to raw data
                data = body

        # Build result
        result = {
            'method': method,
            'url': url,
            'headers': headers,
        }

        if query_params:
            result['params'] = query_params

        if data is not None:
            result['data'] = data

        if json_data is not None:
            result['json'] = json_data

        return result


# Convenience function
def parse_http_request(request_text: str) -> Dict[str, Any]:
    """
    Parse an HTTP request from text.

    Args:
        request_text: Raw HTTP request text

    Returns:
        Dictionary containing method, url, headers, params, data, json
    """
    return HTTPRequestParser.parse(request_text)