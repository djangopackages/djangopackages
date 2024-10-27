# REST APIv4

This is the APIv4 documentation for Django Packages. It is designed to be language and tool agnostic.

## API Usage

This API is limited to read-only GET requests. Other HTTP methods will fail. Only JSON is provided.

## API Reference

### Representation Formats

Representation formats

- JSON.
- UTF-8.

### Base URI

| URI                                | Resource | Methods |
|------------------------------------|----------|---------|
| https://djangopackages.org/api/v4/ | Root     | GET     |

### URIs

| URI                      | Resource       | Methods |
|--------------------------|----------------|---------|
| /                        | Index          | GET     |
| /categories/             | Category list  | GET     |
| /categories/\{id}/       | Category       | GET     |
| /grids/                  | Grid list      | GET     |
| /grids/\{id \| slug}/    | Grid           | GET     |
| /packages/               | Package list   | GET     |
| /packages/\{id \| slug}/ | Package        | GET     |
| /search/                 | Package Search | GET     |


### Resources

#### Category list

**URL:** `/api/v4/categories/`

**Method:** `GET`

**Path parameters:**
`None`

**Query parameters:**

| Name   | Type      | Description                                         |
|--------|-----------|-----------------------------------------------------|
| `limit`  | integer   | Number of results to return per page.               |
| `offset` | integer   | The initial index from which to return the results. |

**Example cURL:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/categories/
```

**Example Response:**

```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Apps",
            "slug": "apps",
            "description": "",
            "title_plural": "",
            "show_pypi": true,
            "created": "2024-04-28T08:48:58.307236",
            "modified": "2024-04-28T08:48:58.307253"
        }
    ]
}
```

#### Category

**URL:** `/api/v4/categories/{id}`

**Method:** `GET`

**Path parameters:**

| Name | Type    | Required | Description                                       |
|------|---------|----------|---------------------------------------------------|
| `id`   | integer | yes      | A unique integer value identifying this category. |

**Query parameters:**
`None`

**Example cURL:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/categories/1/
```

**Example Response:**

```json
{
    "id": 1,
    "title": "App",
    "slug": "apps",
    "description": "Small components used to build projects. An app is anything that is installed by placing in settings.INSTALLED_APPS.",
    "title_plural": "Apps",
    "show_pypi": true,
    "created": "2010-08-14T22:47:52",
    "modified": "2022-03-04T21:48:41.249944"
}
```

#### Grid list

**URL:** `/api/v4/grids/`

**Method:** `GET`

**Path parameters:**
`None`

**Query parameters:**

| Name   | Type      | Description                                         |
|--------|-----------|-----------------------------------------------------|
| `limit`  | integer   | Number of results to return per page.               |
| `offset` | integer   | The initial index from which to return the results. |

**Example cURL:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/grids/
```

**Example Response:**

```json
{
    "count": 371,
    "next": "https://djangopackages.org/api/v4/grids/?limit=20&offset=20",
    "previous": null,
    "results": [
        {
            "id": 438,
            "title": "Health checkers",
            "slug": "healt-checkers",
            "description": "Packages that enables Django's health check (eg: is alive, can talk to database, etc...)",
            "is_locked": false,
            "packages": [
                "https://djangopackages.org/api/v4/packages/5810/",
                "https://djangopackages.org/api/v4/packages/976/",
                "https://djangopackages.org/api/v4/packages/3142/",
                "https://djangopackages.org/api/v4/packages/5811/",
                "https://djangopackages.org/api/v4/packages/5754/",
                "https://djangopackages.org/api/v4/packages/2225/"
            ],
            "header": false,
            "created": "2023-12-27T12:40:58.914633",
            "modified": "2023-12-27T12:40:58.914646"
        }
    ]
}

```

#### Grid

**URL:** `/api/v4/grids/{id | slug}`

**Method:** `GET`

**Path parameters:**

| Name   | Type    | Required | Description                                   |
|--------|---------|----------|-----------------------------------------------|
| `id`   | integer | yes      | A unique integer value identifying this grid. |
| `slug` | string  | yes      | A unique string value identifying this grid.  |

**Query parameters:**
`None`

**Example cURL:**

**Using `id`:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/grids/438/
```

**Using `slug`:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/grids/healt-checkers/
```

**Example Response:**

```json
{
    "id": 438,
    "title": "Health checkers",
    "slug": "healt-checkers",
    "description": "Packages that enables Django's health check (eg: is alive, can talk to database, etc...)",
    "is_locked": false,
    "packages": [
        "https://djangopackages.org/api/v4/packages/5810/",
        "https://djangopackages.org/api/v4/packages/976/",
        "https://djangopackages.org/api/v4/packages/3142/",
        "https://djangopackages.org/api/v4/packages/5811/",
        "https://djangopackages.org/api/v4/packages/5754/",
        "https://djangopackages.org/api/v4/packages/2225/"
    ],
    "header": false,
    "created": "2023-12-27T12:40:58.914633",
    "modified": "2023-12-27T12:40:58.914646"
}
```

#### Package list

**URL:** `/api/v4/packages/`

**Method:** `GET`

**Path parameters:**
`None`

**Query parameters:**

| Name   | Type      | Description                                           |
|--------|-----------|-------------------------------------------------------|
| `limit`  | integer   | Number of results to return per page.               |
| `offset` | integer   | The initial index from which to return the results. |

**Example cURL:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/packages/
```

**Example Response:**

```json
{
    "count": 5327,
    "next": "https://djangopackages.org/api/v4/packages/?limit=20&offset=20",
    "previous": null,
    "results": [
        {
            "category": "https://djangopackages.org/api/v4/categories/1/",
            "grids": [
                "https://djangopackages.org/api/v4/grids/21/",
                "https://djangopackages.org/api/v4/grids/11/",
                "https://djangopackages.org/api/v4/grids/113/"
            ],
            "id": 34,
            "title": "django-debug-toolbar",
            "slug": "django-debug-toolbar",
            "last_updated": "2024-06-01T07:50:28",
            "last_fetched": "2024-06-03T17:19:48.550707",
            "repo_url": "https://github.com/jazzband/django-debug-toolbar",
            "pypi_version": "4.3.0",
            "created": "2010-08-17T05:47:00.834356",
            "modified": "2024-06-03T17:19:49.078307",
            "repo_forks": 1027,
            "repo_description": "A configurable set of panels that display various debug information about the current request/response.",
            "pypi_url": "http://pypi.python.org/pypi/django-debug-toolbar",
            "documentation_url": "https://readthedocs.org/projects/django-debug-toolbar",
            "repo_watchers": 7937,
            "commits_over_52": [
                2,
                1,
                1,
                3
            ],
            "participants": [
                "user-xxx",
                "user-yyy"
            ]
        }
    ]
}
```

#### Package

**URL:** `/api/v4/packages/{id | slug}`

**Method:** `GET`

**Path parameters:**

| Name   | Type    | Required | Description                                      |
|--------|---------|----------|--------------------------------------------------|
| `id`   | integer | yes      | A unique integer value identifying this package. |
| `slug` | string  | yes      | A unique string value identifying this package.  |

**Query parameters:**
`None`

**Example cURL:**

**Using `id`:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/packages/34/
```

**Using `slug`:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/packages/django-debug-toolbar/
```

**Example Response:**

```json
{
    "category": "https://djangopackages.org/api/v4/categories/1/",
    "grids": [
        "https://djangopackages.org/api/v4/grids/21/",
        "https://djangopackages.org/api/v4/grids/11/",
        "https://djangopackages.org/api/v4/grids/113/"
    ],
    "id": 34,
    "title": "django-debug-toolbar",
    "slug": "django-debug-toolbar",
    "last_updated": "2024-06-01T07:50:28",
    "last_fetched": "2024-06-03T17:19:48.550707",
    "repo_url": "https://github.com/jazzband/django-debug-toolbar",
    "pypi_version": "4.3.0",
    "created": "2010-08-17T05:47:00.834356",
    "modified": "2024-06-03T17:19:49.078307",
    "repo_forks": 1027,
    "repo_description": "A configurable set of panels that display various debug information about the current request/response.",
    "pypi_url": "http://pypi.python.org/pypi/django-debug-toolbar",
    "documentation_url": "https://readthedocs.org/projects/django-debug-toolbar",
    "repo_watchers": 7937,
    "commits_over_52": [
        2,
        1,
        1,
        3
    ],
    "participants": [
        "user-xxx",
        "user-yyy"
    ]
}
```

#### Package Search

**URL:** `/api/v4/search/`

**Method:** `GET`

**Path parameters:**
`None`

**Query parameters:**

| Name | Type    | Description                                 |
|------|---------|---------------------------------------------|
| `q`    | string  | Search term containing one or more keywords |


**Example cURL:**

```bash
curl -X GET -H "Content-Type: application/json" https://djangopackages.org/api/v4/search/?q=REST
```

**Example Response:**

```json
[
    {
        "description": "python-social-auth and oauth2 support for django-rest-framework",
        "title": "django-rest-framework-social-oauth2",
        "created": "2024-05-30T19:13:37.117036",
        "modified": "2024-06-03T19:13:36.967715",
        "weight": 112,
        "item_type": "package",
        "title_no_prefix": "rest-framework-social-oauth2",
        "slug": "django-rest-framework-social-oauth2",
        "slug_no_prefix": "rest-framework-social-oauth2",
        "clean_title": "restframeworksocialoauth2",
        "category": "App",
        "absolute_url": "/packages/p/django-rest-framework-social-oauth2/",
        "repo_watchers": 1047,
        "repo_forks": 189,
        "pypi_downloads": 0,
        "usage": 2,
        "participants": "user-xxx,user-yyy",
        "last_committed": "2024-01-12T10:03:34",
        "last_released": "2024-01-12T15:28:41"
    }
]
```
