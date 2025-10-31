from .forgejo import ForgejoClient, ForgejoHandler


class CodebergHandler(ForgejoHandler):
    title = "Codeberg"
    url = "https://codeberg.org"
    url_regex = r"(https|git)://codeberg.org/"
    repo_regex = r"(?:https|git)://codeberg.org/[^/]*/([^/]*)"
    slug_regex = repo_regex
    supports_auto_detection = True

    def __init__(self):
        super().__init__()
        self._base_url = self.url
        self.client = ForgejoClient(self._base_url)
        self._client_cache[self._base_url] = self.client

    def get_base_url(self, repo_url: str) -> str:
        return self._base_url


repo_handler = CodebergHandler()
