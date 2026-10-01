from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


# =========================================================
# Neo4j Configuration
# =========================================================

def _config():
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

    driver = GraphDatabase.driver(
        uri,
        auth=(username, password)
    )

    driver.verify_connectivity()

    return driver


def query(
    cypher: str,
    parameters: dict[str, Any] | None = None,
    *,
    write: bool = False,
):
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

    return bool(
        rows and rows[0]["ok"] == 1
    )


# =========================================================
# Schema
# =========================================================

def create_schema():

    statements = [

        """
        CREATE CONSTRAINT user_id_unique
        IF NOT EXISTS
        FOR (u:User)
        REQUIRE u.user_id IS UNIQUE
        """,

        """
        CREATE CONSTRAINT place_id_unique
        IF NOT EXISTS
        FOR (p:Place)
        REQUIRE p.place_id IS UNIQUE
        """,
    ]

    for statement in statements:
        query(
            statement,
            write=True
        )


# =========================================================
# Data from Colab
# =========================================================

def seed_data():

    create_schema()

    # -----------------------------------------------------
    # Users
    # -----------------------------------------------------

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

    query(
        """
        UNWIND $users AS row

        MERGE (u:User {
            user_id: row.user_id
        })

        SET u.name = row.name
        """,
        {
            "users": users
        },
        write=True,
    )

    # -----------------------------------------------------
    # Places
    # -----------------------------------------------------

    places = [
        {
            "place_id": "P001",
            "name": "Wat Phra Kaew",
        },
        {
            "place_id": "P002",
            "name": "Wat Arun",
        },
        {
            "place_id": "P003",
            "name": "Wat Phra That Doi Suthep",
        },
        {
            "place_id": "P004",
            "name": "Ayutthaya Historical Park",
        },
        {
            "place_id": "P005",
            "name": "Railay Beach & Phi Phi Islands",
        },
        {
            "place_id": "P006",
            "name": "Khao Sok National Park",
        },
        {
            "place_id": "P007",
            "name": "Erawan National Park",
        },
        {
            "place_id": "P008",
            "name": "Pa Tong Beach",
        },
        {
            "place_id": "P009",
            "name": "Pai Canyon",
        },
        {
            "place_id": "P010",
            "name": "Khao Yai National Park",
        },
    ]

    query(
        """
        UNWIND $places AS row

        MERGE (p:Place {
            place_id: row.place_id
        })

        SET p.name = row.name
        """,
        {
            "places": places
        },
        write=True,
    )

    # -----------------------------------------------------
    # Friendships
    # -----------------------------------------------------

    friendships = [
        ["U001", "U002"],
        ["U001", "U003"],
        ["U001", "U004"],
        ["U002", "U005"],
        ["U002", "U006"],
        ["U003", "U007"],
        ["U003", "U008"],
        ["U004", "U009"],
        ["U004", "U010"],
        ["U005", "U006"],
        ["U007", "U008"],
        ["U009", "U010"],
    ]

    query(
        """
        UNWIND $friendships AS row

        MATCH
            (a:User {user_id: row[0]}),
            (b:User {user_id: row[1]})

        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {
            "friendships": friendships
        },
        write=True,
    )

    # -----------------------------------------------------
    # Visited
    # -----------------------------------------------------

    visited = [
        {
            "user_id": "U001",
            "place_id": "P001",
            "date": "2026-09-01",
        },
        {
            "user_id": "U001",
            "place_id": "P003",
            "date": "2026-09-02",
        },
        {
            "user_id": "U002",
            "place_id": "P002",
            "date": "2026-09-03",
        },
        {
            "user_id": "U002",
            "place_id": "P003",
            "date": "2026-09-04",
        },
        {
            "user_id": "U003",
            "place_id": "P003",
            "date": "2026-09-05",
        },
        {
            "user_id": "U003",
            "place_id": "P004",
            "date": "2026-09-06",
        },
        {
            "user_id": "U004",
            "place_id": "P005",
            "date": "2026-09-07",
        },
        {
            "user_id": "U005",
            "place_id": "P006",
            "date": "2026-09-08",
        },
        {
            "user_id": "U006",
            "place_id": "P007",
            "date": "2026-09-09",
        },
        {
            "user_id": "U007",
            "place_id": "P008",
            "date": "2026-09-10",
        },
        {
            "user_id": "U008",
            "place_id": "P009",
            "date": "2026-09-11",
        },
        {
            "user_id": "U009",
            "place_id": "P010",
            "date": "2026-09-12",
        },
        {
            "user_id": "U010",
            "place_id": "P001",
            "date": "2026-09-13",
        },
    ]

    query(
        """
        UNWIND $visited AS row

        MATCH
            (u:User {
                user_id: row.user_id
            }),
            (p:Place {
                place_id: row.place_id
            })

        MERGE (u)-[r:VISITED]->(p)

        SET r.visit_date = date(row.date)
        """,
        {
            "visited": visited
        },
        write=True,
    )


# =========================================================
# Users
# =========================================================

def get_users():

    return query(
        """
        MATCH (u:User)

        RETURN
            u.user_id AS user_id,
            u.name AS name

        ORDER BY u.user_id
        """
    )


def find_user(user_id: str):

    rows = query(
        """
        MATCH (u:User {
            user_id: $user_id
        })

        RETURN
            u.user_id AS user_id,
            u.name AS name
        """,
        {
            "user_id": user_id
        },
    )

    return rows[0] if rows else None


# =========================================================
# User Profile
# =========================================================

def get_profile(user_id: str):

    rows = query(
        """
        MATCH (u:User {
            user_id: $user_id
        })

        OPTIONAL MATCH
            (u)-[:VISITED]->(p:Place)

        RETURN
            u.user_id AS user_id,
            u.name AS name,
            collect(
                DISTINCT {
                    place_id: p.place_id,
                    place: p.name
                }
            ) AS visited
        """,
        {
            "user_id": user_id
        },
    )

    if not rows:
        return None

    profile = rows[0]

    profile["visited"] = [
        x
        for x in profile["visited"]
        if x.get("place_id")
    ]

    return profile


# =========================================================
# Visited Places
# =========================================================

def visited_places(user_id: str):

    return query(
        """
        MATCH
            (u:User {
                user_id: $user_id
            })
            -[r:VISITED]->
            (p:Place)

        RETURN
            p.place_id AS place_id,
            p.name AS name,
            r.visit_date AS visit_date

        ORDER BY visit_date
        """,
        {
            "user_id": user_id
        },
    )


# =========================================================
# Search Places
# =========================================================

def search_places(keyword: str = ""):

    return query(
        """
        MATCH (p:Place)

        WHERE
            $keyword = ""
            OR
            toLower(p.name)
            CONTAINS
            toLower($keyword)

        RETURN
            p.place_id AS place_id,
            p.name AS name

        ORDER BY p.name
        """,
        {
            "keyword": keyword.strip()
        },
    )


# =========================================================
# Recommendation
# =========================================================

def recommend_places(
    user_id: str,
    limit: int = 10
):

    return query(
        """
        MATCH
            (me:User {
                user_id: $user_id
            })
            -[:FRIEND_OF]-
            (friend:User)
            -[:VISITED]->
            (place:Place)

        WHERE NOT EXISTS {
            MATCH
                (me)-[:VISITED]->(place)
        }

        RETURN
            place.place_id AS place_id,
            place.name AS recommendation,
            count(DISTINCT friend) AS friend_score,
            collect(DISTINCT friend.name) AS friends

        ORDER BY
            friend_score DESC,
            recommendation

        LIMIT $limit
        """,
        {
            "user_id": user_id,
            "limit": int(limit),
        },
    )


# =========================================================
# Friend Places
# =========================================================

def friend_places(user_id: str):

    return query(
        """
        MATCH
            (me:User {
                user_id: $user_id
            })
            -[:FRIEND_OF]-
            (friend:User)
            -[:VISITED]->
            (place:Place)

        RETURN
            friend.name AS friend,
            place.name AS place

        ORDER BY
            friend,
            place
        """
    )


# =========================================================
# Popular Places
# =========================================================

def popular_places():

    return query(
        """
        MATCH
            (:User)-[:VISITED]->(p:Place)

        RETURN
            p.place_id AS place_id,
            p.name AS place,
            count(*) AS visit_count

        ORDER BY
            visit_count DESC,
            place
        """
    )


# =========================================================
# Dashboard
# =========================================================

def get_dashboard_metrics():

    rows = query(
        """
        MATCH (u:User)
        WITH count(u) AS users

        MATCH (p:Place)
        WITH
            users,
            count(p) AS places

        MATCH ()-[v:VISITED]->()
        WITH
            users,
            places,
            count(v) AS visits

        MATCH ()-[f:FRIEND_OF]->()

        RETURN
            users,
            places,
            visits,
            count(f) AS friendships
        """
    )

    if rows:
        return rows[0]

    return {
        "users": 0,
        "places": 0,
        "visits": 0,
        "friendships": 0,
    }


# =========================================================
# Graph Explorer
# =========================================================

def graph_neighborhood(
    user_id: str,
    limit: int = 50
):

    return query(
        """
        MATCH
            (u:User {
                user_id: $user_id
            })
            -[r]-
            (n)

        RETURN
            u.user_id AS source_id,
            "User" AS source_label,
            u.name AS source_name,

            elementId(n) AS target_id,
            labels(n)[0] AS target_label,

            CASE
                WHEN n:User THEN n.name
                WHEN n:Place THEN n.name
                ELSE toString(n)
            END AS target_name,

            type(r) AS relationship

        LIMIT $limit
        """,
        {
            "user_id": user_id,
            "limit": int(limit),
        },
    )


# =========================================================
# Add Visit
# =========================================================

def add_visit(
    user_id: str,
    place_id: str,
    visit_date: str,
):

    query(
        """
        MATCH
            (u:User {
                user_id: $user_id
            }),
            (p:Place {
                place_id: $place_id
            })

        MERGE
            (u)-[r:VISITED]->(p)

        SET
            r.visit_date = date($visit_date)
        """,
        {
            "user_id": user_id,
            "place_id": place_id,
            "visit_date": visit_date,
        },
        write=True,
    )