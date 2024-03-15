# Contributors

## Core Developers

These contributors have commit flags for the repository, and are able to
accept and merge pull requests.

<table>
  <tr>
    <th>Name</th>
    <th>GitHub</th>
    <th>Twitter</th>
  </tr>
  {%- for contributor in core_contributors %}
  <tr>
    <td>{{ contributor.name }}</td>
    <td>
      <a href="https://github.com/{{ contributor.github_login }}">{{ contributor.github_login }}</a>
    </td>
    <td>{{ contributor.twitter_username }}</td>
  </tr>
  {%- endfor %}
</table>

For Django Dash 2010, @pydanny and @audreyr created Django Packages.

They are joined by a host of core developers and contributors. See https://github.com/djangopackages/djangopackages/blob/main/CONTRIBUTORS.md

## Other Contributors

Listed in alphabetical order.

<table>
  <tr>
    <th>Name</th>
    <th>GitHub</th>
    <th>Twitter</th>
  </tr>
  {%- for contributor in other_contributors %}
  <tr>
    <td>{{ contributor.name }}</td>
    <td>
      <a href="https://github.com/{{ contributor.github_login }}">{{ contributor.github_login }}</a>
    </td>
    <td>{{ contributor.twitter_username }}</td>
  </tr>
  {%- endfor %}
</table>
