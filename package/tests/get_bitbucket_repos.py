"""
A script to find Bitbucket repos that (a) still exist and (b) have forks.

Usage:  python get_bitbucket_repos.py

Outputs a list of repos and the number of forks each has.

When testing repo handlers, the tests call the Bitbucket repo handler to
fetch repo metadata. However, many Bitbucket repos are no longer active,
have disappeared, or have no forks. This script was created to find a good
repo to test against, and, may be needed in the future if that particular
repo goes away. It may take a few minutes to run, due to only being able
to hit the APIs so fast.
"""

import requests, json, re, time

DJPACK_API_URL = "https://djangopackages.org/api/v3/packages/"
DJPACK_API_URL_BASE = "https://djangopackages.org"


def bitbucket_urls():
    next_url = DJPACK_API_URL
    while next_url:
        response = requests.get(next_url)
        parsed = json.loads(response.content)
        next_path = parsed["meta"]["next"]
        next_url = f"{DJPACK_API_URL_BASE}{next_path}" if next_path else None
        for repo in parsed["objects"]:
            if "bitbucket.org" in repo["repo_url"]:
                yield repo["repo_url"]
        time.sleep(0.1)


def non404urls(urls):
    for url in urls:
        url = url.strip()
        response = requests.get(url)
        # if response.status_code == 200:
        #     print(url)
        if response.status_code != 404:
            yield response.status_code, url
        time.sleep(1)
        if response.status_code == 429:  # too many requests:
            time.sleep(10)


def bitbucket_repos_with_forks(urls, include_unforked=False):
    for url in urls:
        urlparts = url.split("/")
        if len(urlparts) < 5:
            continue
        _, _, _, user, repo, *_ = urlparts
        api_url = f"https://api.bitbucket.org/2.0/repositories/{user}/{repo}/forks/"
        response = requests.get(api_url)
        if response.status_code != 200:
            continue
        parsed = json.loads(response.content)
        num_forks = len(parsed["values"])
        if num_forks or include_unforked:
            yield num_forks, url

        time.sleep(1)
        if response.status_code == 429:  # too many requests:
            time.sleep(10)


def main():
    print("Getting bitbucket repos from Django Packages API...")
    urls = list(bitbucket_urls())
    print(f"Found {len(urls)}.")

    # We might not actually need do do this before calling the BB API
    print("Checking for non-404'd repos...")
    urls = [url for status, url in non404urls(urls) if status == 200]
    print(f"Found {len(urls)}.")

    print("Searching Bitbucket Cloud API for repos with forks...")
    results = list(bitbucket_repos_with_forks(urls))
    print(f"Found {len(results)}. Showing repos and number of forks:")
    for num_forks, url in results:
        print(num_forks, url)


if __name__ == "__main__":
    main()
