"""Map raw API responses to PersonObject."""

from __future__ import annotations

from schemas.objects import PersonObject


class PersonMapper:
    def from_sec_officer(self, raw: dict, company_key: str) -> PersonObject:
        name = raw.get("name", "Unknown")
        key = f"{name.lower().replace(' ', '-')}-{company_key}"
        return PersonObject(
            key=key,
            properties={
                "name": name,
                "role": raw.get("title"),
                "company_key": company_key,
            },
            sources={"sec_edgar": raw},
        )

    def from_github_contributor(self, raw: dict, repo_key: str) -> PersonObject:
        login = raw.get("login", "unknown")
        return PersonObject(
            key=login.lower(),
            properties={
                "name": login,
                "github_handle": login,
                "contributions": raw.get("contributions", 0),
                "repo_key": repo_key,
            },
            sources={"github": raw},
        )
