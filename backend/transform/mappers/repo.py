"""Map raw GitHub repo data to RepositoryObject."""

from __future__ import annotations

from schemas.objects import RepositoryObject


class RepoMapper:
    def from_github(self, raw: dict) -> RepositoryObject:
        full_name = raw.get("full_name", "")
        return RepositoryObject(
            key=full_name.lower(),
            properties={
                "name": raw.get("name"),
                "full_name": full_name,
                "description": raw.get("description"),
                "stars": raw.get("stargazers_count", 0),
                "forks": raw.get("forks_count", 0),
                "language": raw.get("language"),
                "open_issues": raw.get("open_issues_count", 0),
                "url": raw.get("html_url"),
            },
            sources={"github": raw},
        )
