from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database", "neo4j"),
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(
    cypher: str,
    parameters: dict[str, Any] | None = None,
    *,
    write: bool = False,
) -> list[dict[str, Any]]:
    _, _, _, database = _config()

    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


def create_schema() -> None:
    statements = [
        """
        CREATE CONSTRAINT user_id_unique IF NOT EXISTS
        FOR (u:User) REQUIRE u.user_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT place_id_unique IF NOT EXISTS
        FOR (p:Place) REQUIRE p.place_id IS UNIQUE
        """,
    ]

    for statement in statements:
        query(statement, write=True)


def seed_data() -> None:
    """Seed the Travel Graph dataset used by the Colab notebook."""
    create_schema()

    users = [
        {"user_id": "U001", "name": "mark"},
        {"user_id": "U002", "name": "jay"},
        {"user_id": "U003", "name": "moren"},
        {"user_id": "U004", "name": "jacob"},
        {"user_id": "U005", "name": "yu"},
        {"user_id": "U006", "name": "kon"},
        {"user_id": "U007", "name": "bonus"},
        {"user_id": "U008", "name": "model"},
        {"user_id": "U009", "name": "fay"},
        {"user_id": "U010", "name": "nax"},
    ]

    places = [
        {"place_id": "P001", "name": "Wat Phra Kaew"},
        {"place_id": "P002", "name": "Wat Arun"},
        {"place_id": "P003", "name": "Wat Phra That Doi Suthep"},
        {"place_id": "P004", "name": "Ayutthaya Historical Park"},
        {"place_id": "P005", "name": "Railay Beach & Phi Phi Islands"},
        {"place_id": "P006", "name": "Khao Sok National Park"},
        {"place_id": "P007", "name": "Erawan National Park"},
        {"place_id": "P008", "name": "Pa Tong Beach"},
        {"place_id": "P009", "name": "Pai Canyon"},
        {"place_id": "P010", "name": "Khao Yai National Park"},
    ]

    friendships = [
        ("U001", "U002"),
        ("U001", "U003"),
        ("U001", "U004"),
        ("U002", "U005"),
        ("U002", "U006"),
        ("U003", "U007"),
        ("U003", "U008"),
        ("U004", "U009"),
        ("U004", "U010"),
        ("U005", "U006"),
        ("U007", "U008"),
        ("U009", "U010"),
    ]

    visits = [
        ("U001", "P001", "2026-09-01"),
        ("U001", "P003", "2026-09-02"),
        ("U002", "P002", "2026-09-03"),
        ("U002", "P003", "2026-09-04"),
        ("U003", "P003", "2026-09-05"),
        ("U003", "P004", "2026-09-06"),
        ("U004", "P005", "2026-09-07"),
        ("U005", "P006", "2026-09-08"),
        ("U006", "P007", "2026-09-09"),
        ("U007", "P008", "2026-09-10"),
        ("U008", "P009", "2026-09-11"),
        ("U009", "P010", "2026-09-12"),
        ("U010", "P001", "2026-09-13"),
    ]

    query(
        """
        UNWIND $users AS item
        MERGE (u:User {user_id:item.user_id})
        SET u.name = item.name
        """,
        {"users": users},
        write=True,
    )

    query(
        """
        UNWIND $places AS item
        MERGE (p:Place {place_id:item.place_id})
        SET p.name = item.name
        """,
        {"places": places},
        write=True,
    )

    query(
        """
        UNWIND $friendships AS pair
        MATCH (a:User {user_id:pair[0]})
        MATCH (b:User {user_id:pair[1]})
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"friendships": [list(x) for x in friendships]},
        write=True,
    )

    query(
        """
        UNWIND $visits AS item
        MATCH (u:User {user_id:item[0]})
        MATCH (p:Place {place_id:item[1]})
        MERGE (u)-[r:VISITED]->(p)
        SET r.visit_date = date(item[2])
        """,
        {"visits": [list(x) for x in visits]},
        write=True,
    )


def get_users() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)
        RETURN u.user_id AS user_id, u.name AS name
        ORDER BY u.user_id
        """
    )


def get_profile(user_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH (u)-[:FRIEND_OF]-(friend:User)
        WITH u, count(DISTINCT friend) AS friend_count
        OPTIONAL MATCH (u)-[:VISITED]->(p:Place)
        RETURN u.user_id AS user_id,
               u.name AS name,
               friend_count,
               count(DISTINCT p) AS visit_count
        """,
        {"user_id": user_id},
    )
    return rows[0] if rows else None


def visited_places(user_id: str) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {user_id:$user_id})-[v:VISITED]->(p:Place)
        RETURN p.place_id AS place_id,
               p.name AS name,
               toString(v.visit_date) AS visit_date
        ORDER BY v.visit_date
        """,
        {"user_id": user_id},
    )


def search_places(keyword: str = "") -> list[dict[str, Any]]:
    return query(
        """
        MATCH (p:Place)
        WHERE $keyword = ''
           OR toLower(p.name) CONTAINS toLower($keyword)
           OR toLower(p.place_id) CONTAINS toLower($keyword)
        RETURN p.place_id AS place_id,
               p.name AS name
        ORDER BY p.place_id
        """,
        {"keyword": keyword.strip()},
    )


def recommend_places(user_id: str, limit: int = 5) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (me:User {user_id:$user_id})
        MATCH (me)-[:FRIEND_OF]-(friend:User)-[:VISITED]->(place:Place)
        WHERE NOT (me)-[:VISITED]->(place)
        WITH place,
             count(DISTINCT friend) AS friend_score,
             collect(DISTINCT friend.name) AS friend_names
        RETURN place.place_id AS place_id,
               place.name AS name,
               friend_score,
               friend_names
        ORDER BY friend_score DESC, name
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": int(limit)},
    )


def popular_places(limit: int = 10) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)-[:VISITED]->(p:Place)
        RETURN p.place_id AS place_id,
               p.name AS name,
               count(DISTINCT u) AS visitors
        ORDER BY visitors DESC, name
        LIMIT $limit
        """,
        {"limit": int(limit)},
    )


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        OPTIONAL MATCH (u:User)
        WITH count(u) AS users
        OPTIONAL MATCH (p:Place)
        WITH users, count(p) AS places
        OPTIONAL MATCH ()-[v:VISITED]->()
        WITH users, places, count(v) AS visits
        OPTIONAL MATCH ()-[f:FRIEND_OF]->()
        RETURN users, places, visits, count(f) AS friendships
        """
    )

    if not rows:
        return {"users": 0, "places": 0, "visits": 0, "friendships": 0}

    return {
        "users": int(rows[0]["users"]),
        "places": int(rows[0]["places"]),
        "visits": int(rows[0]["visits"]),
        "friendships": int(rows[0]["friendships"]),
    }


def graph_neighborhood(user_id: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {user_id:$user_id})-[r]-(n)
        WHERE n:User OR n:Place
        RETURN u.user_id AS source_id,
               'User' AS source_label,
               u.name AS source_name,
               CASE
                 WHEN n:User THEN n.user_id
                 WHEN n:Place THEN n.place_id
               END AS target_id,
               CASE
                 WHEN n:User THEN 'User'
                 WHEN n:Place THEN 'Place'
               END AS target_label,
               n.name AS target_name,
               type(r) AS relationship
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": int(limit)},
    )


def add_visit(user_id: str, place_id: str, visit_date: str) -> None:
    query(
        """
        MATCH (u:User {user_id:$user_id})
        MATCH (p:Place {place_id:$place_id})
        MERGE (u)-[r:VISITED]->(p)
        SET r.visit_date = date($visit_date)
        """,
        {
            "user_id": user_id,
            "place_id": place_id,
            "visit_date": visit_date,
        },
        write=True,
    )
