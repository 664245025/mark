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
    page_title="Travel Graph",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Premium UI
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root { --bg:#070b12; --panel:#0e1522; --line:rgba(255,255,255,.08); --muted:#8ea0b8; --teal:#2dd4bf; --blue:#60a5fa; }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp {
        background:
          radial-gradient(circle at 82% 0%, rgba(20,184,166,.14), transparent 25%),
          radial-gradient(circle at 8% 20%, rgba(59,130,246,.10), transparent 23%),
          var(--bg);
    }
    .block-container { max-width: 1380px; padding: 1.8rem 2.4rem 3rem; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#0b1019 0%,#080b12 100%);
        border-right: 1px solid rgba(255,255,255,.06);
    }
    [data-testid="stSidebar"] * { font-family:'Inter',sans-serif; }

    .brand { padding: .5rem 0 1.5rem; }
    .brand-title { color:#f8fafc; font-size:1.35rem; font-weight:800; letter-spacing:-.03em; }
    .brand-sub { color:#64748b; font-size:.78rem; margin-top:.2rem; }

    .hero {
        position:relative; overflow:hidden; min-height:250px;
        padding:2.5rem 2.7rem; margin-bottom:1.8rem;
        border:1px solid rgba(45,212,191,.18); border-radius:30px;
        background:
          radial-gradient(circle at 88% 35%, rgba(45,212,191,.28), transparent 24%),
          radial-gradient(circle at 12% 110%, rgba(59,130,246,.23), transparent 35%),
          linear-gradient(135deg,#111827 0%,#0f172a 48%,#0f3d3a 100%);
        box-shadow:0 28px 80px rgba(0,0,0,.32);
    }
    .hero:before { content:""; position:absolute; width:340px; height:340px; right:-150px; top:-180px; border-radius:50%; border:1px solid rgba(255,255,255,.08); box-shadow:0 0 0 35px rgba(255,255,255,.025),0 0 0 75px rgba(255,255,255,.018); }
    .hero-kicker { color:#5eead4; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800; margin-bottom:.7rem; }
    .hero h1 { position:relative; margin:0; max-width:850px; color:#fff; font-size:clamp(2.2rem,4.4vw,4rem); line-height:1.02; letter-spacing:-.055em; }
    .hero p { position:relative; margin:1rem 0 0; max-width:720px; color:#cbd5e1; font-size:1rem; }
    .hero-badges { position:relative; display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1.35rem; }
    .badge { padding:.4rem .7rem; border:1px solid rgba(255,255,255,.09); border-radius:999px; background:rgba(255,255,255,.045); color:#cbd5e1; font-size:.72rem; font-weight:700; }

    .section { display:flex; align-items:end; justify-content:space-between; gap:1rem; margin:1.4rem 0 .9rem; }
    .section h2 { margin:0; color:#f8fafc; font-size:1.55rem; letter-spacing:-.035em; }
    .section p { margin:0; color:#64748b; font-size:.82rem; }

    .stat {
        min-height:122px; padding:1.2rem 1.25rem; border:1px solid var(--line); border-radius:22px;
        background:linear-gradient(145deg,rgba(17,24,39,.92),rgba(9,13,21,.96));
        box-shadow:0 16px 40px rgba(0,0,0,.18); transition:transform .18s ease,border-color .18s ease;
    }
    .stat:hover { transform:translateY(-2px); border-color:rgba(45,212,191,.22); }
    .stat-top { display:flex; justify-content:space-between; color:#94a3b8; font-size:.78rem; font-weight:700; }
    .stat-icon { font-size:1.25rem; }
    .stat-value { margin-top:.35rem; color:#fff; font-size:2.2rem; font-weight:800; letter-spacing:-.05em; }
    .stat-note { color:#64748b; font-size:.72rem; margin-top:.1rem; }

    .profile {
        padding:1.45rem; border:1px solid var(--line); border-radius:24px;
        background:linear-gradient(145deg,#101827,#0b111c); box-shadow:0 18px 50px rgba(0,0,0,.2);
    }
    .avatar { width:54px; height:54px; display:flex; align-items:center; justify-content:center; border-radius:17px; background:linear-gradient(135deg,rgba(45,212,191,.25),rgba(96,165,250,.18)); border:1px solid rgba(45,212,191,.2); font-size:1.6rem; }
    .profile-name { color:#fff; font-size:1.55rem; font-weight:800; margin-top:.8rem; }
    .profile-id { color:#64748b; font-size:.78rem; }
    .profile-stats { display:grid; grid-template-columns:1fr 1fr; gap:.65rem; margin-top:1.1rem; }
    .mini { padding:.75rem; border-radius:14px; background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.05); }
    .mini b { display:block; color:#f8fafc; font-size:1.1rem; }
    .mini span { color:#64748b; font-size:.72rem; }

    .place-card { padding:1.3rem; margin-bottom:1rem; border:1px solid var(--line); border-radius:23px; background:linear-gradient(145deg,rgba(16,24,39,.94),rgba(8,12,19,.98)); box-shadow:0 16px 42px rgba(0,0,0,.18); }
    .rank { display:inline-flex; padding:.34rem .65rem; border-radius:999px; background:rgba(45,212,191,.12); border:1px solid rgba(45,212,191,.2); color:#5eead4; font-size:.72rem; font-weight:800; }
    .place-title { margin:.7rem 0 .15rem; color:#f8fafc; font-size:1.35rem; font-weight:800; letter-spacing:-.025em; }
    .place-id { color:#64748b; font-size:.74rem; }
    .reason { margin-top:.9rem; padding:.9rem 1rem; border-radius:16px; background:#070b12; border:1px solid rgba(255,255,255,.06); color:#cbd5e1; }
    .path { margin-top:.8rem; padding:1rem; border-radius:16px; background:linear-gradient(90deg,rgba(45,212,191,.08),rgba(96,165,250,.05)); border:1px solid rgba(45,212,191,.12); color:#cbd5e1; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.82rem; line-height:1.8; }
    .node { color:#5eead4; font-weight:800; }
    .edge { color:#64748b; }

    .schema { padding:1.25rem; border-radius:22px; border:1px solid var(--line); background:linear-gradient(145deg,#101827,#0b111b); }
    .schema-row { display:flex; align-items:center; gap:.65rem; flex-wrap:wrap; margin:.65rem 0; }
    .node-pill { padding:.6rem .8rem; border-radius:14px; background:rgba(96,165,250,.10); border:1px solid rgba(96,165,250,.18); color:#bfdbfe; font-weight:800; }
    .edge-pill { color:#64748b; font-size:.72rem; font-weight:800; letter-spacing:.06em; }

    .footer { margin-top:2.5rem; text-align:center; color:#475569; font-size:.72rem; }

    .stButton > button { border-radius:12px; border:1px solid rgba(45,212,191,.2); background:rgba(45,212,191,.08); color:#ccfbf1; font-weight:700; }
    .stButton > button:hover { border-color:rgba(45,212,191,.5); background:rgba(45,212,191,.14); }
    div[data-testid="stDataFrame"] { border-radius:16px; overflow:hidden; }
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
    labels = {f"{u['user_id']} — {u['name']}": u['user_id'] for u in users}
    chosen = st.selectbox("เลือกผู้ใช้", list(labels), key=key)
    return labels[chosen]


def relationship_graph(user_id: str, place_id: str | None = None) -> str:
    from neo4j_service import query
    if place_id:
        rows = query(
            """
            MATCH (me:User {user_id:$user_id})
            MATCH (me)-[:FRIEND_OF]-(friend:User)-[:VISITED]->(place:Place {place_id:$place_id})
            RETURN me.user_id AS me_id, me.name AS me_name,
                   friend.user_id AS friend_id, friend.name AS friend_name,
                   place.place_id AS place_id, place.name AS place_name
            ORDER BY friend.name
            """,
            {"user_id": user_id, "place_id": place_id},
        )
    else:
        rows = query(
            """
            MATCH (me:User {user_id:$user_id})
            OPTIONAL MATCH (me)-[:FRIEND_OF]-(friend:User)
            OPTIONAL MATCH (friend)-[:VISITED]->(place:Place)
            RETURN me.user_id AS me_id, me.name AS me_name,
                   friend.user_id AS friend_id, friend.name AS friend_name,
                   place.place_id AS place_id, place.name AS place_name
            ORDER BY friend.name, place.name
            LIMIT 40
            """,
            {"user_id": user_id},
        )
    dot = [
        "digraph G {",
        'rankdir="LR";',
        'graph [bgcolor="transparent", pad="0.3", nodesep="0.6", ranksep="0.85"];',
        'node [shape=box, style="rounded,filled", fontname="Arial", color="#334155", fontcolor="#e2e8f0"];',
        'edge [color="#64748b", fontcolor="#94a3b8", fontname="Arial", penwidth=1.5];',
    ]
    seen = set()
    for r in rows:
        me, friend, place = r["me_id"], r.get("friend_id"), r.get("place_id")
        if me not in seen:
            dot.append(f'"{me}" [label="USER\\n{r["me_name"]}\\n{me}", fillcolor="#12343a"];')
            seen.add(me)
        if friend:
            if friend not in seen:
                dot.append(f'"{friend}" [label="FRIEND\\n{r["friend_name"]}\\n{friend}", fillcolor="#17263d"];')
                seen.add(friend)
            dot.append(f'"{me}" -> "{friend}" [label="FRIEND_OF"];')
        if friend and place:
            if place not in seen:
                dot.append(f'"{place}" [label="PLACE\\n{r["place_name"]}\\n{place}", fillcolor="#30251a"];')
                seen.add(place)
            dot.append(f'"{friend}" -> "{place}" [label="VISITED"];')
    dot.append("}")
    return "\n".join(dot)


if not connection_status():
    st.error("ไม่สามารถเชื่อมต่อ Neo4j Aura ได้")
    st.info("ตรวจสอบ [neo4j] ใน Streamlit Secrets: uri, username, password และ database")
    st.code('[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\nusername = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"', language="toml")
    st.stop()

metrics = get_dashboard_metrics()
if metrics["users"] == 0 and metrics["places"] == 0:
    seed_data()
    metrics = get_dashboard_metrics()

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-title">🌍 Travel Graph</div><div class="brand-sub">Neo4j Aura · Graph Intelligence</div></div>', unsafe_allow_html=True)
    page = st.radio("เมนู", ["Dashboard", "Recommendations", "Place Search", "Visited Places", "Graph Explorer", "Popular Places", "Admin / Setup"], label_visibility="visible")
    st.divider()
    st.markdown('<div class="brand-sub">USER → FRIEND_OF → USER<br>USER → VISITED → PLACE</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">Neo4j Aura · Graph Intelligence</div>
      <h1>🌍 Travel Graph<br>Recommendation System</h1>
      <p>ค้นพบสถานที่ใหม่จากความสัมพันธ์ของผู้ใช้ เพื่อน และประวัติการเดินทาง</p>
      <div class="hero-badges">
        <span class="badge">👤 User Graph</span>
        <span class="badge">🤝 FRIEND_OF</span>
        <span class="badge">📍 VISITED</span>
        <span class="badge">✨ Smart Recommendation</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if page == "Dashboard":
    m = get_dashboard_metrics()
    st.markdown('<div class="section"><div><h2>📊 ภาพรวมระบบ</h2><p>ภาพรวมข้อมูลและโครงสร้าง Travel Graph</p></div></div>', unsafe_allow_html=True)
    cols = st.columns(4)
    stats = [("USERS", m["users"], "👤", "ผู้ใช้งานใน Graph"), ("PLACES", m["places"], "📍", "สถานที่ท่องเที่ยว"), ("VISITED", m["visits"], "🧭", "ประวัติการเดินทาง"), ("FRIENDSHIPS", m["friendships"], "🤝", "ความสัมพันธ์เพื่อน")]
    for col, (label, value, icon, note) in zip(cols, stats):
        with col:
            st.markdown(f'<div class="stat"><div class="stat-top"><span>{label}</span><span class="stat-icon">{icon}</span></div><div class="stat-value">{value}</div><div class="stat-note">{note}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section"><div><h2>👤 User Profile</h2><p>เลือกผู้ใช้เพื่อดูความสัมพันธ์และประวัติการเดินทาง</p></div></div>', unsafe_allow_html=True)
    user_id = user_selector("dashboard_user")
    profile = get_profile(user_id)
    if profile:
        left, right = st.columns([.82, 1.8], gap="large")
        with left:
            st.markdown(f'''<div class="profile"><div class="avatar">👤</div><div class="profile-name">{profile['name']}</div><div class="profile-id">{profile['user_id']}</div><div class="profile-stats"><div class="mini"><b>{profile['friend_count']}</b><span>เพื่อน</span></div><div class="mini"><b>{profile['visit_count']}</b><span>สถานที่เคยไป</span></div></div></div>''', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="section"><div><h2>🗺️ สถานที่ล่าสุด</h2></div></div>', unsafe_allow_html=True)
            rows = visited_places(user_id)
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีประวัติการเดินทาง")

    st.markdown('<div class="section"><div><h2>🧩 Graph Schema</h2><p>โครงสร้างความสัมพันธ์หลักของระบบ</p></div></div>', unsafe_allow_html=True)
    st.markdown('''<div class="schema"><div class="schema-row"><span class="node-pill">👤 User</span><span class="edge-pill">— FRIEND_OF →</span><span class="node-pill">👤 User</span></div><div class="schema-row"><span class="node-pill">👤 User</span><span class="edge-pill">— VISITED →</span><span class="node-pill">📍 Place</span></div></div>''', unsafe_allow_html=True)

elif page == "Recommendations":
    st.markdown('<div class="section"><div><h2>✨ Recommended For You</h2><p>คำแนะนำจากความสัมพันธ์ใน Graph Database</p></div></div>', unsafe_allow_html=True)
    user_id = user_selector("recommend_user")
    top_n = st.slider("จำนวนคำแนะนำ", 1, 10, 5)
    rows = recommend_places(user_id, top_n)
    st.markdown('<div class="schema"><b>เส้นทางการแนะนำ</b><div class="schema-row"><span class="node-pill">👤 คุณ</span><span class="edge-pill">FRIEND_OF →</span><span class="node-pill">👤 เพื่อน</span><span class="edge-pill">VISITED →</span><span class="node-pill">📍 Place</span></div></div>', unsafe_allow_html=True)
    st.write("")
    if not rows:
        st.info("ยังไม่มีสถานที่ที่แนะนำสำหรับผู้ใช้นี้")
    else:
        for i, row in enumerate(rows, start=1):
            friends = row.get("friend_names") or []
            friend_text = ", ".join(friends) if friends else "ไม่พบข้อมูล"
            with st.container(border=True):
                st.markdown(f'<span class="rank">#{i} · {row["friend_score"]} FRIEND CONNECTIONS</span><div class="place-title">📍 {row["name"]}</div><div class="place-id">{row["place_id"]}</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1: st.metric("👥 เพื่อนที่เคยไป", row["friend_score"])
                with c2: st.metric("สถานะของคุณ", "ยังไม่เคยไป")
                st.markdown(f'<div class="path"><span class="node">👤 {user_id}</span> <span class="edge">→ FRIEND_OF →</span> <span class="node">👥 {friend_text}</span><br><span class="edge">→ VISITED →</span> <span class="node">📍 {row["name"]}</span></div>', unsafe_allow_html=True)
                if st.button("🔎 ดู Graph ความสัมพันธ์", key=f"view_graph_{user_id}_{row['place_id']}"):
                    st.graphviz_chart(relationship_graph(user_id, row["place_id"]), use_container_width=True)

elif page == "Place Search":
    st.markdown('<div class="section"><div><h2>🔎 Explore Places</h2><p>ค้นหาสถานที่จากชื่อหรือ Place ID</p></div></div>', unsafe_allow_html=True)
    keyword = st.text_input("ค้นหา", placeholder="เช่น Wat, Khao, P001", label_visibility="collapsed")
    rows = search_places(keyword)
    st.caption(f"พบ {len(rows)} สถานที่")
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("ไม่พบสถานที่")

elif page == "Visited Places":
    st.markdown('<div class="section"><div><h2>🗺️ Travel History</h2><p>ประวัติสถานที่ที่ผู้ใช้เคยไป</p></div></div>', unsafe_allow_html=True)
    user_id = user_selector("visited_user")
    rows = visited_places(user_id)
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("ยังไม่มีประวัติการเดินทาง")
    with st.expander("➕ เพิ่มประวัติการไปสถานที่"):
        places = search_places()
        if places:
            place_labels = {f"{p['place_id']} — {p['name']}": p['place_id'] for p in places}
            selected = st.selectbox("สถานที่", list(place_labels))
            visit_date = st.date_input("วันที่ไป", value=date.today())
            if st.button("บันทึกการเดินทาง", type="primary"):
                add_visit(user_id, place_labels[selected], visit_date.isoformat())
                st.success("บันทึก VISITED เรียบร้อยแล้ว")
                st.rerun()

elif page == "Graph Explorer":
    st.markdown('<div class="section"><div><h2>🕸️ Graph Explorer</h2><p>สำรวจความสัมพันธ์ของ User และ Place แบบภาพ</p></div></div>', unsafe_allow_html=True)
    user_id = user_selector("graph_user")
    st.graphviz_chart(relationship_graph(user_id), use_container_width=True)
    c1, c2 = st.columns(2)
    with c1: st.info("🤝 FRIEND_OF — ความสัมพันธ์ระหว่างผู้ใช้")
    with c2: st.info("📍 VISITED — ประวัติการไปสถานที่")
    rows = graph_neighborhood(user_id)
    if rows:
        with st.expander("ดูข้อมูล Relationship แบบตาราง"): st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Popular Places":
    st.markdown('<div class="section"><div><h2>🔥 Popular Places</h2><p>สถานที่ที่มีผู้ใช้ไปเยือนมากที่สุด</p></div></div>', unsafe_allow_html=True)
    limit = st.slider("จำนวนสถานที่", 5, 10, 10)
    rows = popular_places(limit)
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("ยังไม่มีข้อมูล")

elif page == "Admin / Setup":
    st.markdown('<div class="section"><div><h2>⚙️ Graph Control Center</h2><p>จัดการและตรวจสอบ Travel Graph</p></div></div>', unsafe_allow_html=True)
    m = get_dashboard_metrics()
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Users",m["users"]),("Places",m["places"]),("Visited",m["visits"]),("Friendships",m["friendships"])]) : col.metric(label, value)
    st.divider()
    st.markdown('<div class="schema"><b>Current Graph Schema</b><div class="schema-row"><span class="node-pill">User</span><span class="edge-pill">FRIEND_OF</span><span class="node-pill">User</span></div><div class="schema-row"><span class="node-pill">User</span><span class="edge-pill">VISITED</span><span class="node-pill">Place</span></div></div>', unsafe_allow_html=True)
    st.write("")
    if st.button("🔄 สร้าง / อัปเดต Travel Graph จากข้อมูล Colab", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้าง User, Place และ Relationships..."):
            seed_data()
        st.success("สร้างข้อมูล Travel Graph เรียบร้อยแล้ว")
        st.rerun()
    st.caption("ใช้ MERGE จึงไม่สร้าง node ซ้ำจาก User ID / Place ID")
    st.success("🟢 Neo4j Aura เชื่อมต่อสำเร็จ")

st.markdown('<div class="footer">Travel Graph Recommendation · Neo4j Aura + Streamlit · User → FRIEND_OF → User → VISITED → Place</div>', unsafe_allow_html=True)
