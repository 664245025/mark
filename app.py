from __future__ import annotations

from datetime import date
import html

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
from neo4j_service import query

st.set_page_config(
    page_title="Travel Graph",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- DESIGN SYSTEM ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
  --bg:#070b14;
  --panel:#0d1422;
  --panel2:#101a2b;
  --line:rgba(148,163,184,.13);
  --text:#f8fafc;
  --muted:#8fa1b8;
  --blue:#3b82f6;
  --cyan:#22d3ee;
  --teal:#2dd4bf;
  --purple:#8b5cf6;
  --pink:#ec4899;
  --orange:#fb923c;
}
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{
 background:
   radial-gradient(900px 500px at 75% -5%,rgba(34,211,238,.10),transparent 60%),
   radial-gradient(700px 500px at 0% 35%,rgba(139,92,246,.09),transparent 60%),
   var(--bg);
 color:var(--text);
}
.block-container{max-width:1440px;padding:1.25rem 2.2rem 3rem}
[data-testid="stSidebar"]{
 background:linear-gradient(180deg,#08101d 0%,#090d17 55%,#0b0d15 100%);
 border-right:1px solid rgba(255,255,255,.07);
}
[data-testid="stSidebar"] .block-container{padding:1.2rem .9rem}
[data-testid="stSidebar"] [data-testid="stRadio"] label{font-weight:600}

/* brand */
.brand{padding:.35rem .45rem 1.4rem}
.brand-row{display:flex;align-items:center;gap:.7rem}
.brand-logo{width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.45rem;background:linear-gradient(135deg,#2563eb,#14b8a6);box-shadow:0 10px 30px rgba(37,99,235,.25)}
.brand-title{font-size:1.12rem;font-weight:800;letter-spacing:-.03em;color:#fff}
.brand-sub{font-size:.68rem;color:#64748b;margin-top:.12rem}

/* hero */
.hero{position:relative;overflow:hidden;border-radius:30px;min-height:265px;padding:2.3rem 2.5rem;margin-bottom:1.35rem;border:1px solid rgba(96,165,250,.18);background:linear-gradient(120deg,#111827 0%,#0e1b2f 42%,#0b5960 100%);box-shadow:0 25px 80px rgba(0,0,0,.28)}
.hero:before{content:"";position:absolute;right:-100px;top:-160px;width:440px;height:440px;border-radius:50%;border:1px solid rgba(255,255,255,.10);box-shadow:0 0 0 40px rgba(255,255,255,.025),0 0 0 90px rgba(255,255,255,.015)}
.hero:after{content:"✈";position:absolute;right:7%;bottom:18%;font-size:5rem;opacity:.10;transform:rotate(-12deg)}
.kicker{position:relative;color:#67e8f9;font-size:.72rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.hero h1{position:relative;margin:.6rem 0 0;font-size:clamp(2.2rem,4vw,4.2rem);line-height:.98;letter-spacing:-.06em;color:#fff}
.hero p{position:relative;max-width:720px;margin:1rem 0 0;color:#cbd5e1;font-size:1rem;line-height:1.7}
.hero-chips{position:relative;display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1.2rem}
.chip{padding:.42rem .7rem;border-radius:999px;border:1px solid rgba(255,255,255,.11);background:rgba(255,255,255,.05);font-size:.72rem;font-weight:700;color:#dbeafe}

.section-head{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin:1.25rem 0 .75rem}
.section-head h2{margin:0;font-size:1.45rem;letter-spacing:-.04em}
.section-head p{margin:0;color:var(--muted);font-size:.78rem}

/* metrics */
.metric-card{position:relative;overflow:hidden;min-height:130px;padding:1.15rem 1.25rem;border-radius:22px;border:1px solid var(--line);background:linear-gradient(145deg,rgba(16,25,42,.94),rgba(8,13,22,.98));box-shadow:0 14px 35px rgba(0,0,0,.18)}
.metric-card:after{content:"";position:absolute;width:100px;height:100px;border-radius:50%;right:-35px;bottom:-50px;background:rgba(59,130,246,.12);filter:blur(5px)}
.metric-top{display:flex;justify-content:space-between;color:#94a3b8;font-size:.75rem;font-weight:700}
.metric-icon{font-size:1.15rem}
.metric-number{margin-top:.3rem;font-size:2.15rem;font-weight:800;letter-spacing:-.06em;color:#fff}
.metric-caption{font-size:.7rem;color:#64748b}

/* cards */
.glass{border:1px solid var(--line);border-radius:24px;background:linear-gradient(145deg,rgba(16,25,42,.92),rgba(8,13,22,.96));box-shadow:0 16px 45px rgba(0,0,0,.20)}
.profile-card{padding:1.25rem}
.profile-top{display:flex;gap:.85rem;align-items:center}
.avatar{width:58px;height:58px;border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:1.7rem;background:linear-gradient(135deg,rgba(59,130,246,.22),rgba(45,212,191,.18));border:1px solid rgba(96,165,250,.22)}
.profile-name{font-size:1.3rem;font-weight:800}.profile-id{color:#64748b;font-size:.75rem}
.profile-grid{display:grid;grid-template-columns:1fr 1fr;gap:.65rem;margin-top:1rem}
.mini-card{padding:.8rem;border-radius:15px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.05)}
.mini-card b{font-size:1.05rem}.mini-card span{display:block;color:#64748b;font-size:.68rem;margin-top:.15rem}

.place{overflow:hidden;border-radius:22px;border:1px solid var(--line);background:#0b1220;box-shadow:0 16px 45px rgba(0,0,0,.18)}
.place-cover{height:145px;display:flex;align-items:flex-end;padding:1rem;background:linear-gradient(135deg,#164e63,#1e293b 55%,#312e81);position:relative}
.place-cover:before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 75% 20%,rgba(255,255,255,.22),transparent 25%),linear-gradient(180deg,transparent 20%,rgba(0,0,0,.58))}
.place-rank{position:relative;z-index:1;padding:.35rem .55rem;border-radius:999px;background:rgba(0,0,0,.38);backdrop-filter:blur(8px);font-size:.7rem;font-weight:800;color:#fff}
.place-body{padding:1rem}.place-title{font-size:1.08rem;font-weight:800}.place-id{font-size:.7rem;color:#64748b;margin-top:.15rem}.place-reason{margin-top:.7rem;padding:.75rem;border-radius:14px;background:rgba(255,255,255,.035);color:#b9c6d8;font-size:.75rem;line-height:1.55}
.place-foot{display:flex;justify-content:space-between;align-items:center;margin-top:.85rem;color:#94a3b8;font-size:.72rem}

/* graph */
.graph-card{padding:1rem;border-radius:24px;border:1px solid var(--line);background:linear-gradient(145deg,#0d1727,#080d17)}
.graph-title{font-size:1rem;font-weight:800;margin-bottom:.6rem}
.schema{padding:1rem;border-radius:20px;border:1px solid var(--line);background:rgba(255,255,255,.025)}
.node-pill{padding:.55rem .75rem;border-radius:13px;background:rgba(59,130,246,.10);border:1px solid rgba(96,165,250,.18);color:#bfdbfe;font-size:.78rem;font-weight:800}
.edge-pill{color:#64748b;font-size:.68rem;font-weight:800;letter-spacing:.05em}

/* buttons / inputs */
.stButton>button{border-radius:12px;border:1px solid rgba(96,165,250,.20);background:linear-gradient(135deg,rgba(59,130,246,.15),rgba(139,92,246,.12));color:#e0f2fe;font-weight:700}
.stButton>button:hover{border-color:rgba(34,211,238,.55);transform:translateY(-1px)}
[data-baseweb="select"]>div,[data-baseweb="input"]>div{border-radius:12px!important}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:18px;overflow:hidden}
.footer{text-align:center;color:#475569;font-size:.68rem;margin-top:2.5rem;padding-bottom:1rem}

@media(max-width:900px){.block-container{padding:1rem}.hero{padding:1.6rem;min-height:220px}.hero h1{font-size:2.25rem}}
</style>
""",
    unsafe_allow_html=True,
)


def safe(v):
    return html.escape(str(v))


def connected() -> bool:
    try:
        return bool(ping())
    except Exception:
        return False


def user_selector(key: str) -> str:
    users = get_users()
    if not users:
        st.warning("ยังไม่มีข้อมูล User ใน Neo4j"); st.stop()
    labels = {f"{u['user_id']}  ·  {u['name']}": u['user_id'] for u in users}
    return labels[st.selectbox("ผู้ใช้", list(labels), key=key, label_visibility="collapsed")]


def relationship_graph(user_id: str, place_id: str | None = None) -> str:
    if place_id:
        rows = query("""
        MATCH (me:User {user_id:$user_id})
        MATCH (me)-[:FRIEND_OF]-(friend:User)-[:VISITED]->(place:Place {place_id:$place_id})
        RETURN me.user_id AS me_id, me.name AS me_name,
               friend.user_id AS friend_id, friend.name AS friend_name,
               place.place_id AS place_id, place.name AS place_name
        ORDER BY friend.name
        """, {"user_id": user_id, "place_id": place_id})
    else:
        rows = query("""
        MATCH (me:User {user_id:$user_id})
        OPTIONAL MATCH (me)-[:FRIEND_OF]-(friend:User)
        OPTIONAL MATCH (friend)-[:VISITED]->(place:Place)
        RETURN me.user_id AS me_id, me.name AS me_name,
               friend.user_id AS friend_id, friend.name AS friend_name,
               place.place_id AS place_id, place.name AS place_name
        ORDER BY friend.name, place.name LIMIT 45
        """, {"user_id": user_id})

    dot = [
        "digraph G {", 'rankdir="LR";',
        'graph [bgcolor="transparent", pad="0.2", nodesep="0.55", ranksep="0.75"];',
        'node [shape=box, style="rounded,filled", fontname="Arial", color="#334155", fontcolor="#e2e8f0"];',
        'edge [color="#64748b", fontcolor="#94a3b8", fontname="Arial", penwidth=1.4];'
    ]
    seen=set()
    for r in rows:
        me, friend, place = r["me_id"], r.get("friend_id"), r.get("place_id")
        if me not in seen:
            dot.append(f'"{me}" [label="USER\\n{r["me_name"]}\\n{me}", fillcolor="#123a46"];'); seen.add(me)
        if friend:
            if friend not in seen:
                dot.append(f'"{friend}" [label="FRIEND\\n{r["friend_name"]}\\n{friend}", fillcolor="#172a49"];'); seen.add(friend)
            dot.append(f'"{me}" -> "{friend}" [label="FRIEND_OF"];')
        if friend and place:
            if place not in seen:
                dot.append(f'"{place}" [label="PLACE\\n{r["place_name"]}\\n{place}", fillcolor="#3a2918"];'); seen.add(place)
            dot.append(f'"{friend}" -> "{place}" [label="VISITED"];')
    dot.append("}")
    return "\n".join(dot)


# ---------- CONNECTION ----------
if not connected():
    st.error("เชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
    st.info("ตรวจสอบ Streamlit Secrets ใน [neo4j]")
    st.stop()

metrics = get_dashboard_metrics()
if metrics["users"] == 0 and metrics["places"] == 0:
    seed_data(); metrics = get_dashboard_metrics()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown('''<div class="brand"><div class="brand-row"><div class="brand-logo">🌍</div><div><div class="brand-title">Travel Graph</div><div class="brand-sub">Recommendation System</div></div></div></div>''', unsafe_allow_html=True)
    page = st.radio("เมนู", ["Dashboard", "Recommendations", "Place Search", "Visited Places", "Graph Explorer", "Popular Places", "Admin / Setup"], label_visibility="collapsed")
    st.divider()
    st.markdown('''<div style="padding:.5rem;color:#64748b;font-size:.72rem;line-height:1.8">GRAPH MODEL<br><b style="color:#94a3b8">User</b> ─ FRIEND_OF ─ <b style="color:#94a3b8">User</b><br><b style="color:#94a3b8">User</b> ─ VISITED ─ <b style="color:#94a3b8">Place</b></div>''', unsafe_allow_html=True)
    st.divider()
    st.markdown(f'''<div style="padding:.5rem;color:#64748b;font-size:.7rem">● <span style="color:#34d399">Connected</span><br>Neo4j Aura<br>{metrics["users"]} users · {metrics["places"]} places</div>''', unsafe_allow_html=True)

# ---------- GLOBAL HERO ----------
st.markdown('''
<div class="hero">
  <div class="kicker">TRAVEL INTELLIGENCE · NEO4J AURA</div>
  <h1>Explore places<br>through your graph.</h1>
  <p>ค้นหาสถานที่ท่องเที่ยวที่น่าสนใจจากเครือข่ายเพื่อนและประวัติการเดินทางของคุณ</p>
  <div class="hero-chips"><span class="chip">👤 USER GRAPH</span><span class="chip">🤝 FRIEND_OF</span><span class="chip">📍 VISITED</span><span class="chip">✨ RECOMMENDATION</span></div>
</div>
''', unsafe_allow_html=True)

# ---------- DASHBOARD ----------
if page == "Dashboard":
    st.markdown('<div class="section-head"><div><h2>Overview</h2><p>ภาพรวมของ Travel Graph</p></div></div>', unsafe_allow_html=True)
    cols = st.columns(4, gap="medium")
    stats = [("Users",metrics["users"],"👤","ผู้ใช้ทั้งหมด"),("Places",metrics["places"],"📍","สถานที่ใน Graph"),("Visited",metrics["visits"],"🧭","ประวัติการเดินทาง"),("Friendships",metrics["friendships"],"🤝","ความสัมพันธ์")]
    for c,(name,val,icon,caption) in zip(cols,stats):
        with c: st.markdown(f'<div class="metric-card"><div class="metric-top"><span>{name}</span><span class="metric-icon">{icon}</span></div><div class="metric-number">{val}</div><div class="metric-caption">{caption}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head"><div><h2>👤 Your travel profile</h2><p>เลือกผู้ใช้เพื่อดูเส้นทางและสถานที่ที่เคยไป</p></div></div>', unsafe_allow_html=True)
    user_id = user_selector("dashboard_user")
    profile = get_profile(user_id)
    if profile:
        left,right = st.columns([.72,1.55],gap="large")
        with left:
            st.markdown(f'''<div class="glass profile-card"><div class="profile-top"><div class="avatar">👤</div><div><div class="profile-name">{safe(profile['name'])}</div><div class="profile-id">{safe(profile['user_id'])} · Explorer</div></div></div><div class="profile-grid"><div class="mini-card"><b>{profile['friend_count']}</b><span>Friends</span></div><div class="mini-card"><b>{profile['visit_count']}</b><span>Places visited</span></div></div></div>''', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="section-head"><div><h2>🧭 Recent journeys</h2></div></div>', unsafe_allow_html=True)
            rows=visited_places(user_id)
            if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            else: st.info("ยังไม่มีประวัติการเดินทาง")

    st.markdown('<div class="section-head"><div><h2>🕸️ Graph structure</h2><p>ความสัมพันธ์ที่ระบบใช้สร้างคำแนะนำ</p></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="schema"><div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap"><span class="node-pill">👤 User</span><span class="edge-pill">— FRIEND_OF →</span><span class="node-pill">👤 User</span><span class="edge-pill">— VISITED →</span><span class="node-pill">📍 Place</span></div></div>', unsafe_allow_html=True)

# ---------- RECOMMENDATIONS ----------
elif page == "Recommendations":
    st.markdown('<div class="section-head"><div><h2>✨ Recommended places</h2><p>แนะนำจากความสัมพันธ์ใน Graph — เพื่อนเคยไป แต่คุณยังไม่เคยไป</p></div></div>', unsafe_allow_html=True)
    user_id=user_selector("recommend_user")
    top_n=st.slider("จำนวนคำแนะนำ",1,9,6)
    rows=recommend_places(user_id,top_n)
    if not rows: st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")
    else:
        for start in range(0,len(rows),3):
            grid=st.columns(3,gap="medium")
            for c,i in zip(grid,range(start,min(start+3,len(rows)))):
                r=rows[i]; friends=r.get("friend_names") or []
                friend_text=", ".join(friends) if friends else "เพื่อนใน Graph"
                with c:
                    st.markdown(f'''<div class="place"><div class="place-cover"><span class="place-rank">#{i+1} · {r['friend_score']} friends</span></div><div class="place-body"><div class="place-title">📍 {safe(r['name'])}</div><div class="place-id">{safe(r['place_id'])}</div><div class="place-reason">แนะนำเพราะ <b>{safe(friend_text)}</b> เคยไปสถานที่นี้</div><div class="place-foot"><span>ยังไม่เคยไป</span><span>⭐ Graph match</span></div></div></div>''',unsafe_allow_html=True)
                    if st.button("ดูความสัมพันธ์ →",key=f"rec_{user_id}_{r['place_id']}",use_container_width=True):
                        st.graphviz_chart(relationship_graph(user_id,r['place_id']),use_container_width=True)

# ---------- SEARCH ----------
elif page == "Place Search":
    st.markdown('<div class="section-head"><div><h2>🔎 Explore places</h2><p>ค้นหาจากชื่อสถานที่หรือ Place ID</p></div></div>', unsafe_allow_html=True)
    keyword=st.text_input("ค้นหา",placeholder="Wat · Khao · P001",label_visibility="collapsed")
    rows=search_places(keyword)
    st.caption(f"พบ {len(rows)} สถานที่")
    if rows:
        for r in rows:
            st.markdown(f'''<div class="glass" style="padding:1rem;margin:.55rem 0;display:flex;justify-content:space-between;align-items:center"><div><b>📍 {safe(r['name'])}</b><div style="color:#64748b;font-size:.7rem">{safe(r['place_id'])}</div></div><span class="chip">EXPLORE</span></div>''',unsafe_allow_html=True)
    else: st.info("ไม่พบสถานที่")

# ---------- VISITED ----------
elif page == "Visited Places":
    st.markdown('<div class="section-head"><div><h2>🧭 Travel history</h2><p>สถานที่ที่ผู้ใช้เคยเดินทางไป</p></div></div>', unsafe_allow_html=True)
    user_id=user_selector("visited_user")
    rows=visited_places(user_id)
    if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    else: st.info("ยังไม่มีประวัติการเดินทาง")
    with st.expander("＋ เพิ่มสถานที่ที่เคยไป"):
        places=search_places()
        if places:
            labels={f"{p['place_id']} · {p['name']}":p['place_id'] for p in places}
            selected=st.selectbox("สถานที่",list(labels)); visit_date=st.date_input("วันที่ไป",value=date.today())
            if st.button("บันทึก VISITED",type="primary"):
                add_visit(user_id,labels[selected],visit_date.isoformat()); st.success("บันทึกเรียบร้อย"); st.rerun()

# ---------- GRAPH ----------
elif page == "Graph Explorer":
    st.markdown('<div class="section-head"><div><h2>🕸️ Graph explorer</h2><p>มองเห็นความสัมพันธ์จริงใน Neo4j</p></div></div>', unsafe_allow_html=True)
    user_id=user_selector("graph_user")
    st.markdown('<div class="graph-card"><div class="graph-title">Relationship network</div></div>',unsafe_allow_html=True)
    st.graphviz_chart(relationship_graph(user_id),use_container_width=True)
    c1,c2=st.columns(2)
    with c1: st.info("🤝 FRIEND_OF · User ↔ User")
    with c2: st.info("📍 VISITED · User → Place")
    rows=graph_neighborhood(user_id)
    if rows:
        with st.expander("ดู Relationship data"):
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ---------- POPULAR ----------
elif page == "Popular Places":
    st.markdown('<div class="section-head"><div><h2>🔥 Popular places</h2><p>สถานที่ที่มีผู้ใช้ไปเยือนมากที่สุด</p></div></div>', unsafe_allow_html=True)
    limit=st.slider("จำนวนสถานที่",5,10,8)
    rows=popular_places(limit)
    if rows:
        for i,r in enumerate(rows,1):
            st.markdown(f'''<div class="glass" style="padding:1rem;margin:.5rem 0;display:flex;align-items:center;gap:1rem"><div style="font-size:1.5rem;font-weight:800;color:#67e8f9;width:40px">{i:02d}</div><div style="flex:1"><b>📍 {safe(r.get('name',''))}</b><div style="color:#64748b;font-size:.7rem">{safe(r.get('place_id',''))}</div></div><span class="chip">{r.get('visit_count',r.get('visits',0))} visits</span></div>''',unsafe_allow_html=True)
    else: st.info("ยังไม่มีข้อมูล")

# ---------- ADMIN ----------
elif page == "Admin / Setup":
    st.markdown('<div class="section-head"><div><h2>⚙️ Graph control center</h2><p>ตรวจสอบและ seed Travel Graph</p></div></div>', unsafe_allow_html=True)
    cols=st.columns(4)
    for c,(name,val) in zip(cols,[("Users",metrics['users']),("Places",metrics['places']),("Visited",metrics['visits']),("Friendships",metrics['friendships'])]):
        c.metric(name,val)
    st.markdown('<div class="section-head"><div><h2>Current schema</h2></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="schema"><div class="schema-row"><span class="node-pill">👤 User</span><span class="edge-pill">FRIEND_OF</span><span class="node-pill">👤 User</span></div><div class="schema-row"><span class="node-pill">👤 User</span><span class="edge-pill">VISITED</span><span class="node-pill">📍 Place</span></div></div>',unsafe_allow_html=True)
    st.write("")
    if st.button("🔄 Seed / Update Travel Graph",type="primary",use_container_width=True):
        with st.spinner("กำลังอัปเดต Graph..."):
            seed_data()
        st.success("Travel Graph อัปเดตเรียบร้อยแล้ว"); st.rerun()
    st.success("🟢 Neo4j Aura connected")

st.markdown('<div class="footer">Travel Graph · Neo4j Aura + Streamlit · User → FRIEND_OF → User → VISITED → Place</div>',unsafe_allow_html=True)
