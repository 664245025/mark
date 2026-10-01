from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from neo4j_service import (
    add_visit,
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

st.set_page_config(
    page_title="Travel Graph Recommendation",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
      .hero {
        padding: 1.6rem 1.8rem;
        border-radius: 22px;
        background: linear-gradient(120deg, #111827 0%, #1f2937 55%, #0f766e 100%);
        color: white;
        margin-bottom: 1.2rem;
      }
      .hero h1 { margin: 0; font-size: 2.15rem; }
      .hero p { opacity: .88; margin: .45rem 0 0 0; }
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
        font-size: .82rem;
        font-weight: 700;
      }
      .muted { opacity: .72; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def connection_status() -> bool:
    try:
        return ping()
    except Exception:
        return False


def user_selector(key: str = "user") -> str:
    users = get_users()
    if not users:
        st.warning("ยังไม่มีข้อมูล User ใน Neo4j กรุณาไปที่ Admin / Setup")
        st.stop()

    labels = {
        f"{u['user_id']} — {u['name']}": u["user_id"]
        for u in users
    }
    chosen = st.selectbox("เลือกผู้ใช้", list(labels), key=key)
    return labels[chosen]


def explain_recommendation(row: dict) -> str:
    friends = ", ".join(row.get("friend_names") or [])
    if row.get("friend_score", 0):
        if friends:
            return (
                f"เพื่อนที่เชื่อมโยงกับคุณเคยไปสถานที่นี้ "
                f"{row['friend_score']} คน ({friends})"
            )
        return f"เพื่อนที่เชื่อมโยงกับคุณเคยไปสถานที่นี้ {row['friend_score']} คน"
    return "แนะนำจากข้อมูลในกราฟ"


if not connection_status():
    st.error("ไม่สามารถเชื่อมต่อ Neo4j Aura ได้")
    st.info(
        "ตรวจสอบค่า [neo4j] ใน Streamlit Secrets: "
        "uri, username, password และ database"
    )
    st.code(
        '[neo4j]\n'
        'uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
        'username = "neo4j"\n'
        'password = "YOUR_PASSWORD"\n'
        'database = "neo4j"',
        language="toml",
    )
    st.stop()

# ถ้า Travel Graph ยังว่าง ระบบจะสร้าง dataset จาก Colab ให้อัตโนมัติ
metrics = get_dashboard_metrics()
if metrics["users"] == 0 and metrics["places"] == 0:
    seed_data()
    metrics = get_dashboard_metrics()

with st.sidebar:
    st.markdown("## 🌍 Travel Graph")
    st.caption("Neo4j Aura + Streamlit")
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
    st.caption("Graph Database Travel Recommendation")

st.markdown(
    """
    <div class="hero">
      <h1>🌍 Travel Graph Recommendation System</h1>
      <p>ระบบแนะนำสถานที่ท่องเที่ยวด้วย Graph Database</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "Dashboard":
    st.subheader("📊 ภาพรวมระบบ")
    m = get_dashboard_metrics()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m["users"])
    c2.metric("Places", m["places"])
    c3.metric("Visited", m["visits"])
    c4.metric("Friendships", m["friendships"])

    if m["users"] == 0:
        st.warning("ยังไม่มีข้อมูล User กรุณาไปที่ Admin / Setup")
    else:
        st.divider()
        user_id = user_selector("dashboard_user")
        profile = get_profile(user_id)

        if profile:
            left, right = st.columns([1, 2])
            with left:
                st.markdown(f"### 👤 {profile['name']}")
                st.write(f"**User ID:** {profile['user_id']}")
                st.write(f"**เพื่อน:** {profile['friend_count']} คน")
                st.write(f"**สถานที่ที่เคยไป:** {profile['visit_count']} แห่ง")
            with right:
                st.markdown("### สถานที่ที่เคยไป")
                rows = visited_places(user_id)
                if rows:
                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("ยังไม่มีประวัติการเดินทาง")

elif page == "Recommendations":
    st.subheader("✨ สถานที่ท่องเที่ยวที่แนะนำ")
    user_id = user_selector("recommend_user")
    top_n = st.slider("จำนวนคำแนะนำ", 1, 10, 5)

    rows = recommend_places(user_id, top_n)

    st.caption(
        "หลักการแนะนำ: สถานที่ที่เพื่อนของผู้ใช้เคยไป "
        "และผู้ใช้ยังไม่เคยไป โดยเรียงตามจำนวนเพื่อนที่เคยไป"
    )

    if not rows:
        st.info("ยังไม่มีสถานที่ที่แนะนำสำหรับผู้ใช้นี้")
    else:
        for i, row in enumerate(rows, start=1):
            st.markdown(
                f"""
                <div class="place-card">
                  <span class="score-pill">
                    #{i} · friend score {row['friend_score']}
                  </span>
                  <h3 style="margin:.55rem 0 .2rem 0">{row['name']}</h3>
                  <div class="muted">{row['place_id']}</div>
                  <p><b>เหตุผล:</b> {explain_recommendation(row)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

elif page == "Place Search":
    st.subheader("🔎 ค้นหาสถานที่ท่องเที่ยว")
    keyword = st.text_input(
        "ค้นหาจากชื่อสถานที่หรือ Place ID",
        placeholder="เช่น Wat, Khao, P001",
    )
    rows = search_places(keyword)
    st.write(f"พบ {len(rows)} รายการ")

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("ไม่พบสถานที่")

elif page == "Visited Places":
    st.subheader("🗺️ สถานที่ที่ผู้ใช้เคยไป")
    user_id = user_selector("visited_user")
    rows = visited_places(user_id)

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("ยังไม่มีประวัติการเดินทาง")

    with st.expander("➕ เพิ่มประวัติการไปสถานที่"):
        places = search_places()
        if places:
            place_labels = {
                f"{p['place_id']} — {p['name']}": p["place_id"]
                for p in places
            }
            selected = st.selectbox("สถานที่", list(place_labels))
            visit_date = st.date_input("วันที่ไป", value=date.today())

            if st.button("บันทึกการเดินทาง", type="primary"):
                add_visit(
                    user_id,
                    place_labels[selected],
                    visit_date.isoformat(),
                )
                st.success("บันทึก VISITED เรียบร้อยแล้ว")
                st.rerun()

elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    user_id = user_selector("graph_user")
    rows = graph_neighborhood(user_id)

    if not rows:
        st.info("ยังไม่มี neighborhood graph")
    else:
        dot = [
            "digraph G {",
            'rankdir="LR";',
            'node [shape=box, style="rounded,filled"];',
        ]

        seen_nodes = set()

        for r in rows:
            source_id = str(r["source_id"])
            target_id = str(r["target_id"])

            for nid, label, name in [
                (source_id, r["source_label"], r["source_name"]),
                (target_id, r["target_label"], r["target_name"]),
            ]:
                if nid not in seen_nodes:
                    safe_name = str(name).replace('"', "'")
                    dot.append(
                        f'"{nid}" [label="{safe_name}\\n:{label}"];'
                    )
                    seen_nodes.add(nid)

            dot.append(
                f'"{source_id}" -> "{target_id}" '
                f'[label="{r["relationship"]}"];'
            )

        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)

        with st.expander("ดูข้อมูลความสัมพันธ์"):
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

elif page == "Popular Places":
    st.subheader("🔥 สถานที่ยอดนิยม")
    limit = st.slider("จำนวนสถานที่", 5, 10, 10)
    rows = popular_places(limit)

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("ยังไม่มีข้อมูล")

elif page == "Admin / Setup":
    st.subheader("⚙️ Admin / Setup")

    st.markdown(
        """
        **Graph schema**

        - `(:User)-[:FRIEND_OF]->(:User)`
        - `(:User)-[:VISITED {visit_date}]->(:Place)`

        Recommendation ใช้เส้นทาง:

        `User → FRIEND_OF → User → VISITED → Place`
        """
    )

    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m["users"])
    c2.metric("Places", m["places"])
    c3.metric("Visited", m["visits"])
    c4.metric("Friendships", m["friendships"])

    st.divider()

    if st.button(
        "สร้าง / อัปเดต Travel Graph จากข้อมูล Colab",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("กำลังสร้าง User, Place และ Relationships..."):
            seed_data()
        st.success("สร้างข้อมูล Travel Graph เรียบร้อยแล้ว")
        st.rerun()

    st.caption(
        "การ Seed ใช้ MERGE จึงสามารถกดซ้ำได้โดยไม่สร้าง node ซ้ำจาก User ID / Place ID"
    )

    st.divider()
    st.markdown("### 🔌 Connection")
    st.success("Neo4j Aura เชื่อมต่อสำเร็จ")
