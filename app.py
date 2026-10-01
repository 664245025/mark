import streamlit as st
import pandas as pd

from neo4j_service import (
    get_users,
    get_profile,
    visited_places,
    recommend_places,
    search_places,
    popular_places,
    graph_neighborhood,
    get_dashboard_metrics,
    ping,
)

st.set_page_config(
    page_title="Travel Graph",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

* { font-family: Inter, sans-serif; }
.stApp { background:#fff; color:#111; }
.block-container { max-width:1400px; padding:0 2.4rem 4rem; }

/* Sidebar */
[data-testid="stSidebar"] { background:#0a0a0c; }
[data-testid="stSidebar"] * { color:#fff !important; }
[data-testid="stSidebar"] .stRadio label { padding:.55rem 0; border-bottom:1px solid rgba(255,255,255,.10); }

/* Editorial masthead */
.masthead {
    margin:0 -2.4rem;
    min-height:235px;
    background:#050505;
    color:#fff;
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    align-items:center;
    padding:2rem 4rem;
}
.logo { font-size:6.5rem; font-weight:900; letter-spacing:-.12em; line-height:.75; }
.logo .plus { color:#1755ff; font-size:3.5rem; vertical-align:top; position:relative; top:-.42em; }
.tagline { text-align:center; font-size:1.15rem; line-height:1.25; }
.blue { color:#1755ff; }
.red { color:#ef473c; }
.brand { text-align:right; font-size:3rem; line-height:.82; font-weight:900; }
.brand small { display:block; font-size:1rem; font-weight:400; margin-top:.4rem; }

/* Navigation */
.topnav {
    margin:0 -2.4rem 2.4rem;
    min-height:72px;
    border-bottom:1px solid #ddd;
    display:flex;
    justify-content:center;
    align-items:center;
    gap:2.4rem;
    overflow:auto;
    white-space:nowrap;
}
.topnav span { font-size:.82rem; font-weight:700; }

.eyebrow { color:#1755ff; font-size:.72rem; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }
.page-title { font-size:3rem; line-height:1; font-weight:900; letter-spacing:-.065em; margin:.35rem 0 .7rem; }
.page-sub { color:#666; font-size:.92rem; margin-bottom:1.8rem; }

/* Metrics */
.metric { border-top:2px solid #111; border-bottom:1px solid #ddd; padding:1rem 0 1.2rem; }
.metric-label { color:#777; font-size:.7rem; letter-spacing:.12em; font-weight:800; }
.metric-value { font-size:2.7rem; line-height:1; font-weight:900; letter-spacing:-.06em; margin-top:.3rem; }

/* Editorial cards */
.feature { border:1px solid #ddd; background:#fff; box-shadow:0 15px 35px rgba(0,0,0,.06); }
.feature-image {
    min-height:300px;
    padding:1.5rem;
    display:flex;
    align-items:flex-end;
    color:#fff;
    background:
      linear-gradient(180deg,rgba(0,0,0,.02),rgba(0,0,0,.72)),
      linear-gradient(135deg,#0e4b87,#168a78 50%,#e8b33b);
}
.feature-image h2 { font-size:2.1rem; line-height:1; margin:0; font-weight:900; letter-spacing:-.05em; }
.feature-body { padding:1.2rem 1.4rem 1.5rem; }

.side-title { border-top:3px solid #111; padding-top:.8rem; font-size:1.45rem; font-weight:900; }
.category { padding:.8rem 0; border-bottom:1px solid #111; color:#1755ff; font-weight:600; }

/* Recommendation cards */
.rec-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; }
.rec { border:1px solid #ddd; background:#fff; min-height:210px; padding:1.25rem; box-shadow:0 8px 22px rgba(0,0,0,.04); }
.rec:hover { transform:translateY(-3px); transition:.2s; box-shadow:0 15px 30px rgba(0,0,0,.08); }
.rec-num { color:#1755ff; font-size:.7rem; font-weight:900; letter-spacing:.12em; }
.rec h3 { font-size:1.25rem; line-height:1.05; margin:.5rem 0 .3rem; font-weight:900; }
.rec-id { color:#888; font-size:.72rem; }
.rel { margin-top:1rem; padding:.75rem; background:#f4f5f7; border-left:3px solid #1755ff; font-family:monospace; font-size:.72rem; line-height:1.45; }

/* Graph */
.graph-panel { border:1px solid #ddd; padding:1rem; background:#fafafa; }

.stButton > button { border-radius:0; background:#1755ff; color:white; border:1px solid #1755ff; font-weight:800; }
.stButton > button:hover { background:#0b36b9; border-color:#0b36b9; color:#fff; }
.stTextInput > div > div, .stSelectbox > div > div { border-radius:0; }

.footer { margin-top:4rem; padding-top:1rem; border-top:2px solid #111; color:#777; font-size:.7rem; display:flex; justify-content:space-between; }

@media(max-width:900px) {
  .masthead { grid-template-columns:1fr; text-align:center; gap:1.2rem; padding:2rem; }
  .brand { text-align:center; }
  .logo { font-size:4rem; }
  .topnav { justify-content:flex-start; padding:0 1rem; }
  .rec-grid { grid-template-columns:1fr; }
}
</style>
''', unsafe_allow_html=True)


def safe(fn, *args, default=None, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        st.session_state["last_error"] = str(exc)
        return default


def users_list():
    rows = safe(get_users, default=[]) or []
    return rows


def choose_user(key):
    users = users_list()
    if not users:
        st.warning("ยังไม่พบข้อมูล User ใน Neo4j")
        return None
    labels = [f"{u.get('user_id', '-')} — {u.get('name', '-')}" for u in users]
    idx = st.selectbox("เลือกผู้ใช้", range(len(labels)), format_func=lambda i: labels[i], key=key)
    return users[idx].get("user_id")


def relation_line(user_id, place_id):
    return f"{user_id}  →  FRIEND_OF  →  friend  →  VISITED  →  {place_id}"


# Header
st.markdown('''
<div class="masthead">
  <div class="logo">u<span class="plus">+</span>i</div>
  <div class="tagline"><span class="blue">connected</span><br>to<br>the <span class="red">travel</span> pulse</div>
  <div class="brand"><span class="blue">+</span>travel<br><small>graph explorer</small></div>
</div>
<div class="topnav">
  <span>HOME</span><span>TRAVEL GRAPH</span><span>DISCOVER</span><span>RECOMMENDATIONS</span><span>PLACES</span><span>SOCIAL</span>
</div>
''', unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("# 🌍 TRAVEL GRAPH")
st.sidebar.caption("Neo4j Aura · Streamlit")
page = st.sidebar.radio(
    "MENU",
    ["Dashboard", "Recommendations", "Place Search", "Visited Places", "Graph Explorer", "Popular Places", "Admin / Setup"],
)
st.sidebar.markdown("---")
st.sidebar.caption("USER → FRIEND_OF → USER → VISITED → PLACE")

# Dashboard
if page == "Dashboard":
    st.markdown('<div class="eyebrow">Travel intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Explore the graph.</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">ค้นพบสถานที่ผ่านความสัมพันธ์ระหว่างผู้ใช้ เพื่อน และประวัติการเดินทาง</div>', unsafe_allow_html=True)

    metrics = safe(get_dashboard_metrics, default={}) or {}
    cols = st.columns(4)
    metric_data = [
        ("USERS", metrics.get("users", 0), "👤"),
        ("PLACES", metrics.get("places", 0), "📍"),
        ("VISITED", metrics.get("visited", 0), "✦"),
        ("FRIENDSHIPS", metrics.get("friendships", 0), "↗"),
    ]
    for col, (label, value, icon) in zip(cols, metric_data):
        with col:
            st.markdown(f'<div class="metric"><div class="metric-label">{icon} {label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

    st.write("")
    user_id = choose_user("dash_user")
    if user_id:
        profile = safe(get_profile, user_id, default={}) or {}
        visits = safe(visited_places, user_id, default=[]) or []
        left, right = st.columns([1.7, 1])
        with left:
            st.markdown('<div class="eyebrow">Selected traveller</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="page-title">{profile.get("name", user_id)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="page-sub">USER ID · {user_id}</div>', unsafe_allow_html=True)
            st.markdown('''<div class="feature"><div class="feature-image"><h2>Your next journey<br>starts in the graph.</h2></div><div class="feature-body"><b>Graph identity</b><br><span style="color:#777">Friend connections and visited places drive recommendations.</span></div></div>''', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="side-title">Travel history</div>', unsafe_allow_html=True)
            if visits:
                st.dataframe(pd.DataFrame(visits), use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีประวัติการเดินทาง")

# Recommendations
elif page == "Recommendations":
    st.markdown('<div class="eyebrow">Social discovery</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Places your network knows.</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">คำแนะนำจากเพื่อนของผู้ใช้ที่เคยไปสถานที่นั้น และผู้ใช้ยังไม่เคยไป</div>', unsafe_allow_html=True)

    user_id = choose_user("rec_user")
    limit = st.slider("จำนวนคำแนะนำ", 1, 10, 6)
    rows = safe(recommend_places, user_id, limit, default=[]) if user_id else []
    if rows:
        html = '<div class="rec-grid">'
        for i, row in enumerate(rows, 1):
            place_id = row.get("place_id", "-")
            name = row.get("name", "Unknown")
            score = row.get("friend_score", 0)
            html += f'''<div class="rec"><div class="rec-num">#{i:02d} · FRIEND SCORE {score}</div><h3>📍 {name}</h3><div class="rec-id">{place_id}</div><div class="rel">{relation_line(user_id, place_id)}</div></div>'''
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("ยังไม่มีสถานที่ที่สามารถแนะนำได้")

# Search
elif page == "Place Search":
    st.markdown('<div class="eyebrow">Explore</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Find a place.</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">ค้นหาสถานที่ท่องเที่ยวจาก Neo4j</div>', unsafe_allow_html=True)
    q = st.text_input("ค้นหาสถานที่", placeholder="เช่น Wat Arun, Pai, Khao Yai")
    if q:
        rows = safe(search_places, q, default=[]) or []
        if rows:
            for row in rows:
                st.markdown(f'<div class="rec"><div class="rec-num">PLACE</div><h3>📍 {row.get("name", "Unknown")}</h3><div class="rec-id">{row.get("place_id", "-")}</div></div>', unsafe_allow_html=True)
        else:
            st.info("ไม่พบสถานที่")

# Visited
elif page == "Visited Places":
    st.markdown('<div class="eyebrow">Travel archive</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Places you visited.</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">ประวัติการเดินทางของผู้ใช้</div>', unsafe_allow_html=True)
    user_id = choose_user("visited_user")
    rows = safe(visited_places, user_id, default=[]) if user_id else []
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีข้อมูล")

# Graph
elif page == "Graph Explorer":
    st.markdown('<div class="eyebrow">Graph intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">See the connections.</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">ดูเส้นทางความสัมพันธ์ของ User และ Place</div>', unsafe_allow_html=True)
    user_id = choose_user("graph_user")
    rows = safe(graph_neighborhood, user_id, default=[]) if user_id else []
    if rows:
        edges = []
        for r in rows:
            target = str(r.get("target_id", ""))
            rel = str(r.get("relationship", "RELATED"))
            if target:
                edges.append(f'"{user_id}" -> "{target}" [label="{rel}"];')
        graph = 'digraph G { rankdir=LR; bgcolor="transparent"; node [shape=box, style="rounded,filled", fontname="Arial", color="#1755ff"]; ' + " ".join(edges) + " }"
        st.graphviz_chart(graph, use_container_width=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีข้อมูล Graph")

# Popular
elif page == "Popular Places":
    st.markdown('<div class="eyebrow">Community pulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Where people go.</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">สถานที่ที่มีผู้ใช้ไปเยือนมากที่สุดจากข้อมูลใน Graph</div>', unsafe_allow_html=True)
    rows = safe(popular_places, default=[]) or []
    if rows:
        for i, row in enumerate(rows, 1):
            count = row.get("visit_count", row.get("visitors", 0))
            st.markdown(f'<div class="rec"><div class="rec-num">#{i:02d}</div><h3>📍 {row.get("name", "Unknown")}</h3><div class="rec-id">VISITS · {count}</div></div>', unsafe_allow_html=True)
    else:
        st.info("ยังไม่มีข้อมูล")

# Admin
else:
    st.markdown('<div class="eyebrow">System</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Control center.</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">ตรวจสอบการเชื่อมต่อและสถานะระบบ</div>', unsafe_allow_html=True)
    if st.button("ตรวจสอบ Neo4j"):
        if safe(ping, default=False):
            st.success("Neo4j connection: OK")
        else:
            st.error("เชื่อมต่อ Neo4j ไม่สำเร็จ")

st.markdown('''<div class="footer"><span>TRAVEL GRAPH · NEO4J AURA</span><span>USER → FRIEND_OF → USER → VISITED → PLACE</span></div>''', unsafe_allow_html=True)
