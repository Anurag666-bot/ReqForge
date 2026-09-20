"""
Mutation engine for ReqForge.
Generates controlled mutations of HTTP requests for testing.
"""

import copy
import json
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class MutationType(Enum):
    """Types of mutations that can be applied to HTTP requests."""
    METHOD = "method"
    HEADER = "header"
    COOKIE = "cookie"
    QUERY_PARAM = "query_param"
    PATH = "path"
    BODY = "body"
    JSON_FIELD = "json_field"
    FORM_FIELD = "form_field"


class MutationEngine:
    """Engine for generating controlled mutations of HTTP requests."""

    @staticmethod
    def mutate_request(
        base_request: Dict[str, Any],
        mutation_type: MutationType,
        field_name: Optional[str] = None,
        values: Optional[List[Any]] = None,
        exclude_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate mutations of a base request.

        Args:
            base_request: Dictionary containing method, url, headers, params, data, json
            mutation_type: Type of mutation to apply
            field_name: Specific field to mutate (for header, cookie, query_param, etc.)
            values: List of values to use for mutation
            exclude_fields: List of fields to exclude from mutation

        Returns:
            List of mutated request dictionaries
        """
        if exclude_fields is None:
            exclude_fields = []

        mutations = []

        if mutation_type == MutationType.METHOD:
            mutations = MutationEngine._mutate_method(base_request, values or ["GET", "POST", "PUT", "DELETE", "PATCH"])
        elif mutation_type == MutationType.HEADER:
            mutations = MutationEngine._mutate_header(base_request, field_name, values or [], exclude_fields)
        elif mutation_type == MutationType.COOKIE:
            mutations = MutationEngine._mutate_cookie(base_request, field_name, values or [], exclude_fields)
        elif mutation_type == MutationType.QUERY_PARAM:
            mutations = MutationEngine._mutate_query_param(base_request, field_name, values or [], exclude_fields)
        elif mutation_type == MutationType.PATH:
            mutations = MutationEngine._mutate_path(base_request, values or [])
        elif mutation_type == MutationType.BODY:
            mutations = MutationEngine._mutate_body(base_request, values or [])
        elif mutation_type == MutationType.JSON_FIELD:
            mutations = MutationEngine._mutate_json_field(base_request, field_name, values or [], exclude_fields)
        elif mutation_type == MutationType.FORM_FIELD:
            mutations = MutationEngine._mutate_form_field(base_request, field_name, values or [], exclude_fields)

        return mutations

    @staticmethod
    def _mutate_method(base_request: Dict[str, Any], values: List[str]) -> List[Dict[str, Any]]:
        """Mutate HTTP method."""
        mutations = []
        for value in values:
            if value != base_request.get('method', 'GET'):
                mutated = copy.deepcopy(base_request)
                mutated['method'] = value
                mutations.append(mutated)
        return mutations

    @staticmethod
    def _mutate_header(base_request: Dict[str, Any], field_name: Optional[str], values: List[str], exclude_fields: List[str]) -> List[Dict[str, Any]]:
        """Mutate HTTP headers."""
        mutations = []
        headers = base_request.get('headers', {}).copy()

        if field_name:
            # Mutate specific header
            for value in values:
                mutated = copy.deepcopy(base_request)
                if 'headers' not in mutated:
                    mutated['headers'] = {}
                mutated['headers'][field_name] = value
                mutations.append(mutated)
        else:
            # Mutate all headers (except excluded ones)
            for header_name, header_value in headers.items():
                if header_name in exclude_fields:
                    continue
                for value in values:
                    mutated = copy.deepcopy(base_request)
                    if 'headers' not in mutated:
                        mutated['headers'] = {}
                    mutated['headers'][header_name] = value
                    mutations.append(mutated)
        return mutations

    @staticmethod
    def _mutate_cookie(base_request: Dict[str, Any], field_name: Optional[str], values: List[str], exclude_fields: List[str]) -> List[Dict[str, Any]]:
        """Mutate cookies (in Cookie header)."""
        mutations = []
        headers = base_request.get('headers', {}).copy()
        cookie_header = headers.get('Cookie', '')

        # Parse existing cookies
        cookies = {}
        if cookie_header:
            for cookie in cookie_header.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    cookies[name.strip()] = value.strip()

        if field_name:
            # Mutate specific cookie
            for value in values:
                mutated = copy.deepcopy(base_request)
                if 'headers' not in mutated:
                    mutated['headers'] = {}
                cookies[field_name] = value
                # Reconstruct Cookie header
                cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
                if cookie_str:
                    mutated['headers']['Cookie'] = cookie_str
                elif 'Cookie' in mutated['headers']:
                    del mutated['headers']['Cookie']
                mutations.append(mutated)
        else:
            # Mutate all cookies (except excluded ones)
            for cookie_name, cookie_value in cookies.items():
                if cookie_name in exclude_fields:
                    continue
                for value in values:
                    mutated = copy.deepcopy(base_request)
                    if 'headers' not in mutated:
                        mutated['headers'] = {}
                    cookies[cookie_name] = value
                    # Reconstruct Cookie header
                    cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
                    if cookie_str:
                        mutated['headers']['Cookie'] = cookie_str
                    elif 'Cookie' in mutated['headers']:
                        del mutated['headers']['Cookie']
                    mutations.append(mutated)
        return mutations

    @staticmethod
    def _mutate_query_param(base_request: Dict[str, Any], field_name: Optional[str], values: List[str], exclude_fields: List[str]) -> List[Dict[str, Any]]:
        """Mutate query parameters."""
        mutations = []
        params = base_request.get('params', {}).copy()
        url = base_request.get('url', '')

        # Parse URL to handle query parameters properly
        parsed_url = urlparse(url)
        existing_params = parse_qs(parsed_url.query)
        # Convert lists to single values
        existing_params = {k: v[0] if v else '' for k, v in existing_params.items()}
        # Merge with params from request dict (params from dict take precedence)
        existing_params.update(params)

        if field_name:
            # Mutate specific query parameter
            for value in values:
                mutated = copy.deepcopy(base_request)
                mutated_params = existing_params.copy()
                mutated_params[field_name] = value
                # Reconstruct URL with new query parameters
                new_query = urlencode(mutated_params)
                new_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query,
                    parsed_url.fragment
                ))
                mutated['url'] = new_url
                mutated['params'] = mutated_params
                mutations.append(mutated)
        else:
            # Mutate all query parameters (except excluded ones)
            for param_name, param_value in existing_params.items():
                if param_name in exclude_fields:
                    continue
                for value in values:
                    mutated = copy.deepcopy(base_request)
                    mutated_params = existing_params.copy()
                    mutated_params[param_name] = value
                    # Reconstruct URL with new query parameters
                    new_query = urlencode(mutated_params)
                    new_url = urlunparse((
                        parsed_url.scheme,
                        parsed_url.netloc,
                        parsed_url.path,
                        parsed_url.params,
                        new_query,
                        parsed_url.fragment
                    ))
                    mutated['url'] = new_url
                    mutated['params'] = mutated_params
                    mutations.append(mutated)
        return mutations

    @staticmethod
    def _mutate_path(base_request: Dict[str, Any], values: List[str]) -> List[Dict[str, Any]]:
        """Mutate URL path."""
        mutations = []
        url = base_request.get('url', '')
        parsed_url = urlparse(url)

        for value in values:
            if value != parsed_url.path:
                mutated = copy.deepcopy(base_request)
                # Reconstruct URL with new path
                new_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    value,  # new path
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment
                ))
                mutated['url'] = new_url
                mutations.append(mutated)
        return mutations

    @staticmethod
    def _mutate_body(base_request: Dict[str, Any], values: List[Any]) -> List[Dict[str, Any]]:
        """Mutate request body."""
        mutations = []
        body_data = base_request.get('data')
        json_data = base_request.get('json')

        for value in values:
            mutated = copy.deepcopy(base_request)
            # Clear existing body data
            if 'data' in mutated:
                del mutated['data']
            if 'json' in mutated:
                del mutated['json']

            # Set new body data
            if isinstance(value, dict):
                # If value is a dict, treat as JSON
                mutated['json'] = value
            else:
                # Otherwise treat as raw data
                mutated['data'] = value
            mutations.append(mutated)
        return mutations

    @staticmethod
    def _mutate_json_field(base_request: Dict[str, Any], field_name: Optional[str], values: List[Any], exclude_fields: List[str]) -> List[Dict[str, Any]]:
        """Mutate specific fields in JSON body."""
        mutations = []
        json_data = base_request.get('json')

        if not isinstance(json_data, dict):
            # Can't mutate JSON fields if body isn't JSON
            return mutations

        if field_name:
            # Mutate specific JSON field
            for value in values:
                mutated = copy.deepcopy(base_request)
                if 'json' not in mutated:
                    mutated['json'] = {}
                mutated['json'][field_name] = value
                mutations.append(mutated)
        else:
            # Mutate all JSON fields (except excluded ones)
            for key, json_value in json_data.items():
                if key in exclude_fields:
                    continue
                for value in values:
                    mutated = copy.deepcopy(base_request)
                    if 'json' not in mutated:
                        mutated['json'] = {}
                    mutated['json'][key] = value
                    mutations.append(mutated)
        return mutations

    @staticmethod
    def _mutate_form_field(base_request: Dict[str, Any], field_name: Optional[str], values: List[Any], exclude_fields: List[str]) -> List[Dict[str, Any]]:
        """Mutate specific fields in form body."""
        mutations = []
        form_data = base_request.get('data')

        if not isinstance(form_data, dict):
            # Can't mutate form fields if body isn't form data
            return mutations

        if field_name:
            # Mutate specific form field
            for value in values:
                mutated = copy.deepcopy(base_request)
                if 'data' not in mutated:
                    mutated['data'] = {}
                mutated['data'][field_name] = value
                mutations.append(mutated)
        else:
            # Mutate all form fields (except excluded ones)
            for key, form_value in form_data.items():
                if key in exclude_fields:
                    continue
                for value in values:
                    mutated = copy.deepcopy(base_request)
                    if 'data' not in mutated:
                        mutated['data'] = {}
                    mutated['data'][key] = value
                    mutations.append(mutated)
        return mutations