"""Map raw patent / filing data to EventObject."""

from __future__ import annotations

from schemas.objects import EventObject


class EventMapper:
    def from_patent(self, raw: dict, company_key: str) -> EventObject:
        patent_number = raw.get("patent_number", "unknown")
        date = raw.get("patent_date", "")
        key = f"patent-{patent_number}"
        return EventObject(
            key=key,
            properties={
                "event_type": "patent",
                "title": raw.get("patent_title"),
                "date": date,
                "patent_number": patent_number,
                "company_key": company_key,
            },
            sources={"patents": raw},
        )

    def from_sec_filing(self, raw: dict, company_key: str) -> EventObject:
        form = raw.get("form", "unknown")
        date = raw.get("filingDate", raw.get("dateFiled", ""))
        accession = raw.get("accessionNumber", "unknown")
        key = f"filing-{accession}"
        return EventObject(
            key=key,
            properties={
                "event_type": "sec_filing",
                "form": form,
                "date": date,
                "description": raw.get("primaryDocDescription"),
                "company_key": company_key,
            },
            sources={"sec_edgar": raw},
        )
