"""
Normalizes Git repository URLs for GitHub, Bitbucket, GitLab, Codeberg, and Forgejo.
"""

import re
from urllib.parse import urlparse, unquote


class RepoURLError(Exception):
    """Base exception for repository URL errors"""

    pass


# Provider configurations
PROVIDERS = {
    # GitHub-like: simple owner/repo structure
    "github.com": {"type": "simple", "max_segments": 2},
    "bitbucket.org": {"type": "simple", "max_segments": 2},
    "codeberg.org": {"type": "simple", "max_segments": 2},
    # GitLab-like: supports nested groups
    "gitlab.com": {"type": "nested", "max_segments": None},
}

# URL path markers to strip
URL_MARKERS = {
    "tree",
    "blob",
    "commit",
    "commits",
    "compare",
    "releases",
    "pull",
    "pulls",
    "issues",
    "src",
    "raw",
    "merge_requests",
    "tags",
    "-",
    "milestone",
    "wiki",
    "settings",
}

# SCP-style SSH regex (git@host:path)
SCP_REGEX = re.compile(r"^(?P<user>[^@]+)@(?P<host>[^:\/]+):(?P<path>.+)$")


def normalize_repo_url(
    url: str, allowed_hosts: set[str] | None = None, allow_unknown: bool = True
) -> str:
    """
    Normalize a Git repository URL to HTTPS format.

    Supports multiple URL formats:
    - HTTPS: https://github.com/owner/repo
    - HTTP: http://github.com/owner/repo
    - SSH: git@github.com:owner/repo.git
    - Bare: github.com/owner/repo

    Args:
        url: Repository URL to normalize
        allowed_hosts: Optional set of allowed hostnames. If None, all are allowed.
        allow_unknown: Whether to allow unknown hosts (for Forgejo self-hosted)

    Returns:
        Normalized HTTPS URL (lowercase)

    Raises:
        RepoURLError: If URL is invalid or not allowed

    Examples:
        >>> normalize_repo_url("github.com/owner/repo")
        'https://github.com/owner/repo'
        >>> normalize_repo_url("git@gitlab.com:group/subgroup/project.git")
        'https://gitlab.com/group/subgroup/project'
    """
    url = url.strip()

    if not url:
        raise RepoURLError("URL cannot be empty")

    # Parse host and path
    host, path = _parse_url(url)

    if not host:
        raise RepoURLError("Could not extract hostname from URL")

    # Validate allowed hosts
    if allowed_hosts and host not in allowed_hosts:
        raise RepoURLError(
            f"Host '{host}' not in allowed list: {', '.join(sorted(allowed_hosts))}"
        )

    # Clean and segment path
    segments = _clean_path(path)

    if not segments or len(segments) < 2:
        raise RepoURLError(
            "Invalid repository path. Expected format: owner/repo or group/project"
        )

    # Extract repository path based on provider type
    provider = PROVIDERS.get(host)

    if provider:
        # Known provider
        repo_path = _extract_repo_path(segments, provider)
    else:
        # Unknown provider (Forgejo or self-hosted)
        if not allow_unknown:
            raise RepoURLError(
                f"Unknown provider '{host}'. Known: {', '.join(sorted(PROVIDERS.keys()))}"
            )
        # Assume simple owner/repo structure
        repo_path = "/".join(segments[:2])

    return f"https://{host}/{repo_path}".lower()


def _parse_url(url: str) -> tuple[str, str]:
    """
    Parse URL and extract hostname and path.

    Handles:
    - SCP-style SSH: git@github.com:owner/repo
    - Standard URL: https://github.com/owner/repo
    - Bare format: github.com/owner/repo

    Returns:
        Tuple of (hostname, path)
    """
    # Try SCP-style SSH first
    match = SCP_REGEX.match(url)
    if match:
        return match.group("host").lower(), match.group("path")

    # Try standard URL parsing
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""

    # Handle bare format (github.com/owner/repo)
    if not host and "/" in url:
        parts = url.split("/", 1)
        if "." in parts[0]:  # Looks like a domain
            host = parts[0].lower()
            path = "/" + parts[1] if len(parts) > 1 else ""

    # Remove www prefix
    if host.startswith("www."):
        host = host[4:]

    return host, path


def _clean_path(path: str) -> list[str]:
    """
    Clean path and return segments.

    Operations:
    - URL decode
    - Strip slashes and .git extension
    - Filter empty segments
    """
    path = unquote(path or "").strip("/")

    if path.endswith(".git"):
        path = path[:-4]

    return [seg for seg in path.split("/") if seg]


def _strip_url_markers(segments: list[str]) -> list[str]:
    """Remove URL path markers (tree, blob, etc.) from segments"""
    for i, seg in enumerate(segments):
        if seg in URL_MARKERS:
            return segments[:i]
    return segments


def _extract_repo_path(segments: list[str], provider: dict) -> str:
    """
    Extract repository path based on provider type.

    Args:
        segments: Path segments
        provider: Provider configuration dict

    Returns:
        Repository path string
    """
    provider_type = provider["type"]
    max_segments = provider.get("max_segments")

    # Strip URL markers first
    segments = _strip_url_markers(segments)

    if not segments or len(segments) < 2:
        raise RepoURLError("Invalid URL structure")

    if provider_type == "simple":
        # GitHub-like: take first 2 segments (owner/repo)
        if max_segments and len(segments) > max_segments:
            segments = segments[:max_segments]
        return "/".join(segments[:2])

    elif provider_type == "nested":
        # GitLab-like: support nested groups
        if max_segments and len(segments) > max_segments:
            segments = segments[:max_segments]
        return "/".join(segments)

    return "/".join(segments[:2])
