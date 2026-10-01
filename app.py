from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from neo4j_service import (
    add_visit,
    create_schema,
    find_user,
    friend_places,
    get_dashboard_metrics,
    get_profile,
    get_users,
    graph_neighborhood,
    ping,
    popular_places,
    recommend_places,
    search_places,
    seed_data,
    visited_places,
)


# =========================================================
# Page Config
# =========================================================

st.set_page_config(
    page_title="Travel Graph Recommender",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.3rem;
        padding-bottom: 2rem;
    }

    .hero {
        padding: 1.5rem;
        border-radius: 22px;
        background: linear-gradient(
            120deg,
            #111827 0%,
            #1f2937 55%,
            #0f766e 100%
        );
        color: white;
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.2rem;
    }

    .hero p {
        opacity: .88;
        margin-top: .4rem;
    }

    .place-card {
        padding: 1rem 1.1rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px;
        margin-bottom: .8rem;
    }

    .score-pill {
        display: inline-block;
        padding: .2rem .6rem;
        border-radius: 999px;
        background: #0f766e;
        color: white;
        font-size: .8rem;
        font-weight: 700;
    }

    .muted {
        opacity: .72;
        font-size: .9rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Connection
# =========================================================

def require_connection():

    try:

        if not ping():
            raise RuntimeError(
                "Neo4j did not return a healthy response"
            )

    except Exception as exc:

        st.error(
            "ยังไม่สามารถเชื่อมต่อ Neo4j Aura ได้"
        )

        st.code(
            """
[neo4j]
uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
username = "neo4j"
password = "YOUR_PASSWORD"
database = "neo4j"
            """,
            language="toml",
        )

        st.caption(
            "ใส่ค่า Neo4j ใน Streamlit Secrets "
            "และอย่าใส่ password ลง GitHub"
        )

        st.exception(exc)

        st.stop()


# =========================================================
# User Selector
# =========================================================

def user_selector(key: str):

    users = get_users()

    if not users:

        st.info(
            "ยังไม่มีข้อมูล User "
            "กรุณาไปที่ Setup ก่อน"
        )

        st.stop()

    labels = {
        f"{u['user_id']} — {u['name']}":
        u["user_id"]
        for u in users
    }

    selected = st.selectbox(
        "เลือกผู้ใช้",
        list(labels.keys()),
        key=key,
    )

    return labels[selected]


# =========================================================
# Recommendation Explanation
# =========================================================

def explain_recommendation(row):

    score = row.get("friend_score", 0)

    friends = ", ".join(
        row.get("friends") or []
    )

    if friends:

        return (
            f"มีเพื่อน {score} คนเคยไปสถานที่นี้ "
            f"({friends})"
        )

    return (
        "สถานที่นี้ถูกพบจากประวัติการท่องเที่ยว "
        "ของเพื่อน"
    )


# =========================================================
# Connection
# =========================================================

require_connection()


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.markdown("## 🌏 Travel Graph")

    st.caption(
        "Neo4j Aura + Streamlit"
    )

    page = st.radio(
        "เมนู",
        [
            "Dashboard",
            "Recommendations",
            "Place Search",
            "Visited Places",
            "Graph Explorer",
            "Popular Places",
            "Admin / Setup",
        ],
    )

    st.divider()

    st.caption(
        "Graph Database Travel Recommendation"
    )


# =========================================================
# Hero
# =========================================================

st.markdown(
    """
    <div class="hero">

        <h1>
            🌏 Travel Graph Recommendation System
        </h1>

        <p>
            ระบบแนะนำสถานที่ท่องเที่ยวด้วย Graph Database
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Dashboard
# =========================================================

if page == "Dashboard":

    st.subheader("📊 ภาพรวมระบบ")

    metrics = get_dashboard_metrics()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Users",
        metrics.get("users", 0)
    )

    c2.metric(
        "Places",
        metrics.get("places", 0)
    )

    c3.metric(
        "Visited",
        metrics.get("visits", 0)
    )

    c4.metric(
        "Friendships",
        metrics.get("friendships", 0)
    )

    st.divider()

    user_id = user_selector(
        "dashboard_user"
    )

    profile = get_profile(user_id)

    if profile:

        left, right = st.columns(
            [1, 2]
        )

        with left:

            st.markdown(
                f"### 👤 {profile['name']}"
            )

            st.write(
                f"**User ID:** "
                f"{profile['user_id']}"
            )

            st.write(
                f"**จำนวนสถานที่ที่เคยไป:** "
                f"{len(profile['visited'])}"
            )

        with right:

            st.markdown(
                "### 🗺️ สถานที่ที่เคยไป"
            )

            if profile["visited"]:

                st.dataframe(
                    pd.DataFrame(
                        profile["visited"]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "ยังไม่มีประวัติการท่องเที่ยว"
                )


# =========================================================
# Recommendations
# =========================================================

elif page == "Recommendations":

    st.subheader(
        "✨ สถานที่ท่องเที่ยวที่แนะนำ"
    )

    user_id = user_selector(
        "recommend_user"
    )

    top_n = st.slider(
        "จำนวนสถานที่ที่ต้องการแนะนำ",
        1,
        10,
        5,
    )

    rows = recommend_places(
        user_id,
        top_n,
    )

    st.caption(
        "ระบบแนะนำสถานที่จากสถานที่ที่เพื่อนเคยไป "
        "และผู้ใช้ยังไม่เคยไป"
    )

    if not rows:

        st.info(
            "ยังไม่มีสถานที่ที่สามารถแนะนำได้"
        )

    else:

        for i, row in enumerate(
            rows,
            start=1
        ):

            st.markdown(
                f"""
                <div class="place-card">

                    <span class="score-pill">
                        #{i}
                        · friend score
                        {row['friend_score']}
                    </span>

                    <h3>
                        {row['recommendation']}
                    </h3>

                    <div class="muted">
                        {row['place_id']}
                    </div>

                    <p>
                        <b>เหตุผล:</b>
                        {explain_recommendation(row)}
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# Place Search
# =========================================================

elif page == "Place Search":

    st.subheader(
        "🔎 ค้นหาสถานที่ท่องเที่ยว"
    )

    keyword = st.text_input(
        "ชื่อสถานที่",
        placeholder="เช่น Wat Arun"
    )

    rows = search_places(
        keyword
    )

    st.write(
        f"พบ {len(rows)} รายการ"
    )

    if rows:

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# Visited Places
# =========================================================

elif page == "Visited Places":

    st.subheader(
        "🗺️ ประวัติการท่องเที่ยว"
    )

    user_id = user_selector(
        "visited_user"
    )

    rows = visited_places(
        user_id
    )

    if not rows:

        st.info(
            "ผู้ใช้นี้ยังไม่มีประวัติการท่องเที่ยว"
        )

    else:

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# Graph Explorer
# =========================================================

elif page == "Graph Explorer":

    st.subheader(
        "🕸️ Graph Explorer"
    )

    user_id = user_selector(
        "graph_user"
    )

    rows = graph_neighborhood(
        user_id
    )

    if not rows:

        st.info(
            "ไม่พบความสัมพันธ์ของ User นี้"
        )

    else:

        dot = [
            "digraph G {",
            'rankdir="LR";',
            'node [shape=box, style="rounded,filled"];',
        ]

        seen_nodes = set()

        for row in rows:

            source_id = row[
                "source_id"
            ]

            source_name = row[
                "source_name"
            ]

            target_id = row[
                "target_id"
            ]

            target_name = row[
                "target_name"
            ]

            relationship = row[
                "relationship"
            ]

            if source_id not in seen_nodes:

                safe_source = str(
                    source_name
                ).replace('"', "'")

                dot.append(
                    f'"{source_id}" '
                    f'[label="{safe_source}"];'
                )

                seen_nodes.add(
                    source_id
                )

            if target_id not in seen_nodes:

                safe_target = str(
                    target_name
                ).replace('"', "'")

                dot.append(
                    f'"{target_id}" '
                    f'[label="{safe_target}"];'
                )

                seen_nodes.add(
                    target_id
                )

            dot.append(
                f'"{source_id}" -> '
                f'"{target_id}" '
                f'[label="{relationship}"];'
            )

        dot.append("}")

        st.graphviz_chart(
            "\n".join(dot),
            use_container_width=True,
        )

        with st.expander(
            "ดูข้อมูล Relationship"
        ):

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# Popular Places
# =========================================================

elif page == "Popular Places":

    st.subheader(
        "🔥 สถานที่ท่องเที่ยวยอดนิยม"
    )

    rows = popular_places()

    if rows:

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "ยังไม่มีข้อมูลการท่องเที่ยว"
        )


# =========================================================
# Admin / Setup
# =========================================================

elif page == "Admin / Setup":

    st.subheader(
        "⚙️ Setup ระบบ"
    )

    st.warning(
        "ปุ่มนี้จะสร้าง User, Place และ Relationship "
        "ตามข้อมูลจาก Colab"
    )

    st.markdown(
        """
        ### Graph Schema

        ```text
        (:User)-[:FRIEND_OF]->(:User)

        (:User)-[:VISITED {
            visit_date
        }]->(:Place)
        ```

        ### Recommendation

        ระบบจะหา:

        ```text
        User
          ↓
        Friend
          ↓
        VISITED
          ↓
        Place
        ```

        แล้วตัดสถานที่ที่ User เคยไปออก
        """

    )

    if st.button(
        "สร้าง Constraint + ข้อมูลจาก Colab",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "กำลังสร้างข้อมูล..."
        ):

            seed_data()

        st.success(
            "สร้างข้อมูลจาก Colab เรียบร้อยแล้ว"
        )

        st.rerun()


# =========================================================
# Add Visit
# =========================================================

st.divider()

with st.expander(
    "➕ เพิ่มประวัติการไปสถานที่"
):

    users = get_users()
    places = search_places()

    if users and places:

        user_options = {
            f"{u['user_id']} — {u['name']}":
            u["user_id"]
            for u in users
        }

        place_options = {
            f"{p['place_id']} — {p['name']}":
            p["place_id"]
            for p in places
        }

        selected_user = st.selectbox(
            "User",
            list(user_options.keys()),
        )

        selected_place = st.selectbox(
            "สถานที่",
            list(place_options.keys()),
        )

        visit_date = st.date_input(
            "วันที่ไป",
            value=date.today(),
        )

        if st.button(
            "บันทึกการท่องเที่ยว"
        ):

            add_visit(
                user_options[selected_user],
                place_options[selected_place],
                visit_date.isoformat(),
            )

            st.success(
                "บันทึกข้อมูลเรียบร้อยแล้ว"
            )

            st.rerun()