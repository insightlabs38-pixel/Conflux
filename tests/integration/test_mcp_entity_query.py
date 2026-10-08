"""PD-F006-B01-T91: an agent runs the entity query the application lists use, as the credential."""

import json

import pytest
from mcp_adapter import tools as catalogue

from tests.integration.test_mcp_adapter import MCP, credential, tool, world  # noqa: F401

pytestmark = pytest.mark.django_db

ACTION = catalogue.BY_NAME["query_entity"].action


def rows(result):
    return json.loads(result["content"][0]["text"])


def test_query_entity_returns_the_same_page_as_the_route_with_search_sort_and_paging(world):  # noqa: F811
    w = world
    token = credential(w, [f"POST:{MCP}", ACTION])
    page = rows(tool(w, token, "query_entity", {"entity": "projects", "limit": "5"})["result"])
    assert page["entity"] == "projects" and page["total"] == 1
    assert [r["name"] for r in page["rows"]] == ["Robot"]
    found = tool(w, token, "query_entity", {"entity": "projects", "search": "robo"})["result"]
    assert rows(found)["total"] == 1 and rows(found)["search"] == "robo"
    none = tool(w, token, "query_entity", {"entity": "projects", "search": "zzzz"})["result"]
    assert rows(none)["total"] == 0
    filtered = tool(
        w,
        token,
        "query_entity",
        {
            "entity": "projects",
            "filter": '{"field":"name","op":"eq","value":"Robot"}',
            "sort": "-name",
        },
    )["result"]
    assert rows(filtered)["total"] == 1 and rows(filtered)["sort"] == ["-name"]


def test_refusals_come_back_as_tool_errors_that_name_the_part(world):  # noqa: F811
    w = world
    token = credential(w, [f"POST:{MCP}", ACTION])
    one_letter = tool(w, token, "query_entity", {"entity": "projects", "search": "a"})["result"]
    assert one_letter["isError"] is True and "search" in one_letter["content"][0]["text"]
    bad_filter = tool(w, token, "query_entity", {"entity": "projects", "filter": '{"field":"x"}'})[
        "result"
    ]
    assert bad_filter["isError"] is True and "filter" in bad_filter["content"][0]["text"]
    unknown = tool(w, token, "query_entity", {"entity": "nothing"})["result"]
    assert unknown["isError"] is True and "404" in unknown["content"][0]["text"]
    malformed = tool(w, token, "query_entity", {"entity": "Bad Entity!"})
    assert "error" in malformed  # refused before any route runs
    too_big = tool(w, token, "query_entity", {"entity": "projects", "limit": "9999"})
    assert "error" in too_big or too_big["result"]["isError"] is True


def test_the_credential_owner_keeps_their_own_rights_and_the_tool_needs_its_action(world):  # noqa: F811
    w = world
    # a participant owns this credential: the entity's roles do not include them
    participant = credential(w, [f"POST:{MCP}", ACTION], owner=w["participant"])
    refused = tool(w, participant, "query_entity", {"entity": "projects"})
    assert "error" in refused or refused["result"]["isError"] is True
    # an organizer credential limited to another tool cannot call it
    other = next(t for t in catalogue.TOOLS if t.action != ACTION)
    limited = credential(w, [f"POST:{MCP}", other.action])
    denied = tool(w, limited, "query_entity", {"entity": "projects"})
    assert "error" in denied or denied["result"]["isError"] is True


def test_group_and_subgroup_return_buckets_through_the_tool(world):  # noqa: F811
    w = world
    token = credential(w, [f"POST:{MCP}", ACTION])
    page = rows(
        tool(w, token, "query_entity", {"entity": "projects", "group": "gallery_visible"})["result"]
    )
    assert page["rows"] == [] and page["group"] == "gallery_visible"
    assert [(g["label"], g["count"]) for g in page["groups"]] == [("Yes", 1)]
    refused = tool(w, token, "query_entity", {"entity": "projects", "group": "name"})["result"]
    assert refused["isError"] is True and "Cannot group by" in refused["content"][0]["text"]


def test_a_calendar_is_asked_through_the_tool_like_the_route(world):  # noqa: F811
    w = world
    token = credential(w, [f"POST:{MCP}", ACTION])
    month = tool(
        w,
        token,
        "query_entity",
        {"entity": "projects", "calendar": "created_at", "month": "2099-01"},
    )["result"]
    page = rows(month)
    assert page["calendar"] == "created_at" and page["month"] == "2099-01" and page["days"] == []
    bad = tool(w, token, "query_entity", {"entity": "projects", "calendar": "name"})["result"]
    assert bad["isError"] is True and "Cannot place rows by" in bad["content"][0]["text"]
    malformed = tool(
        w, token, "query_entity", {"entity": "projects", "calendar": "created_at", "month": "soon"}
    )
    assert "error" in malformed  # refused before any route runs
    thirteenth = tool(
        w,
        token,
        "query_entity",
        {"entity": "projects", "calendar": "created_at", "month": "2027-13"},
    )["result"]
    assert thirteenth["isError"] is True and "month" in thirteenth["content"][0]["text"]
