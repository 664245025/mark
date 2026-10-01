from __future__ import annotations

import html
import streamlit as st
import pandas as pd

from neo4j_service import (
    add_visit, get_dashboard_metrics, get_profile, get_users,
    graph_neighborhood, ping, popular_places, recommend_places,
    search_places, seed_data, visited_places,
)

st.set_page_config(page_title="Travel Graph Explorer", page_icon="✦", layout="wide")

# ----------------------------- STYLE -----------------------------
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#101318;--muted:#68707d;--paper:#f5f5f2;--card:#fff;--blue:#2864ff;--line:#e5e6e8;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:var(--paper)}
.block-container{max-width:1450px;padding:0 3.2rem 3rem}
[data-testid="stSidebar"]{display:none}
header[data-testid="stHeader"]{background:transparent}
.topbar{margin:0 -3.2rem 2rem;padding:1.15rem 3.2rem;background:#0e0f11;color:#fff;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #222}
.brand{display:flex;align-items:center;gap:12px}.brand-mark{font-family:'Space Grotesk';font-weight:700;font-size:1.4rem}.brand-dot{width:9px;height:9px;background:#4e7cff;border-radius:50%;display:inline-block}.brand-small{font-size:.67rem;color:#a9adb5;letter-spacing:.16em;text-transform:uppercase;margin-left:6px}
.nav-caption{font-size:.68rem;color:#a9adb5;letter-spacing:.13em;text-transform:uppercase}
[data-testid="stRadio"]{margin:0 0 1.7rem}
[data-testid="stRadio"]>div{gap:.35rem;flex-wrap:wrap}
[data-testid="stRadio"] label{background:transparent;border:1px solid transparent;border-radius:999px;padding:.48rem .95rem!important;color:#66707d;font-weight:600;font-size:.86rem;transition:.2s}
[data-testid="stRadio"] label:hover{border-color:#d8dbe0;color:#111}
[data-testid="stRadio"] label:has(input:checked){background:#111318;color:white;border-color:#111318}
.hero{background:#111318;color:#fff;border-radius:28px;padding:3rem 3.2rem;margin-bottom:1.5rem;position:relative;overflow:hidden;min-height:280px}
.hero:after{content:'✦';position:absolute;right:6%;top:7%;font-size:12rem;line-height:1;color:#fff;opacity:.035}
.eyebrow{font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;color:#8faeff;font-weight:700}.hero h1{font-family:'Space Grotesk';font-size:clamp(2.6rem,5vw,5rem);line-height:.95;letter-spacing:-.06em;margin:.55rem 0 1rem;max-width:760px}.hero p{max-width:720px;color:#c7cbd2;line-height:1.7;margin:0;font-size:1rem}
.intro{font-size:1rem;line-height:1.75;color:#555e6b;max-width:900px;margin:0 0 1.5rem}.section-title{font-family:'Space Grotesk';font-size:1.45rem;letter-spacing:-.03em;margin:2rem 0 .35rem}.section-sub{color:#777f8b;font-size:.9rem;margin-bottom:1rem}
.metric{background:#fff;border:1px solid var(--line);padding:1.35rem 1.4rem;border-radius:18px;min-height:118px}.metric-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;color:#7a818c}.metric-value{font-family:'Space Grotesk';font-size:2.35rem;font-weight:700;margin:.3rem 0}.metric-note{font-size:.78rem;color:#858c96}
.card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:1.35rem 1.45rem;height:100%;box-shadow:0 8px 30px rgba(20,25,35,.035)}
.card h3{font-family:'Space Grotesk';margin:0 0 .4rem;font-size:1.05rem}.card p{color:#707884;line-height:1.65;font-size:.88rem;margin:.35rem 0 0}.tag{display:inline-block;background:#eef3ff;color:#2758dc;border-radius:999px;padding:.25rem .6rem;font-size:.7rem;font-weight:700;margin-bottom:.7rem}
.place{background:#fff;border:1px solid var(--line);border-radius:18px;padding:1rem 1.1rem;margin:.65rem 0}.place-title{font-weight:700}.place-meta{font-size:.75rem;color:#7b838e;margin-top:.2rem}.score{float:right;background:#111318;color:white;border-radius:999px;padding:.25rem .55rem;font-size:.7rem;font-weight:700}
.info-box{background:#eef3ff;border:1px solid #d9e3ff;border-radius:18px;padding:1.15rem 1.3rem;color:#34425f;line-height:1.7;margin:1rem 0}.info-box b{color:#1e4ec8}
.empty{border:1px dashed #cfd3d9;border-radius:18px;padding:2rem;text-align:center;color:#7a818b;background:#fafaf8}
.footer{border-top:1px solid var(--line);margin-top:3rem;padding-top:1.2rem;color:#8a9098;font-size:.72rem;text-align:center}
.stButton>button{border-radius:12px!important;font-weight:700!important}
[data-testid="stDataFrame"]{border-radius:16px;overflow:hidden}
</style>
""", unsafe_allow_html=True)


def esc(x): return html.escape(str(x))

def users_list():
    rows = get_users() or []
    return rows

def user_options():
    rows=users_list()
    return [(str(r.get('user_id','')), str(r.get('name') or r.get('user_id',''))) for r in rows]

def user_select(key='user'):
    opts=user_options()
    if not opts:
        st.warning('ยังไม่พบข้อมูลผู้ใช้ใน Neo4j')
        return None
    ids=[x[0] for x in opts]
    names={x[0]:x[1] for x in opts}
    selected=st.selectbox('เลือกผู้ใช้', ids, key=key, format_func=lambda x:f"{names.get(x,x)}  ·  {x}")
    return selected

def metric_card(label,value,note):
    st.markdown(f'<div class="metric"><div class="metric-label">{esc(label)}</div><div class="metric-value">{esc(value)}</div><div class="metric-note">{esc(note)}</div></div>',unsafe_allow_html=True)

def relationship_graph(user_id):
    rows=graph_neighborhood(user_id) or []
    lines=['graph G {','rankdir=LR;','graph [bgcolor="transparent", pad="0.2"];','node [shape=box, style="rounded,filled", fontname="Arial", color="#d7dce5", fontcolor="#151820"];']
    lines.append(f'"{user_id}" [label="{user_id}", fillcolor="#dfe9ff", color="#2864ff"];')
    for r in rows:
        uid=str(r.get('user_id') or r.get('friend_id') or '')
        place=str(r.get('place_name') or r.get('name') or '')
        if uid and uid!=user_id:
            lines.append(f'"{uid}" [label="{uid}", fillcolor="#f4f4f2"];')
            lines.append(f'"{user_id}" -- "{uid}" [label=" FRIEND_OF ", color="#9ca3af"];')
        if place:
            p=f'place:{place}'
            lines.append(f'"{p}" [label="{place}", shape=ellipse, fillcolor="#eaf7f3"];')
            if uid: lines.append(f'"{uid}" -- "{p}" [label=" VISITED ", color="#67a98d"];')
    lines.append('}')
    return '\n'.join(lines)

# ----------------------------- HEADER -----------------------------
st.markdown('<div class="topbar"><div class="brand"><span class="brand-mark">u+i</span><span class="brand-dot"></span><span class="brand-small">connected to the travel pulse</span></div><div class="nav-caption">+ travel graph explorer</div></div>',unsafe_allow_html=True)

pages=['Overview','Recommendations','Search places','Visited places','Graph explorer','Popular places','Graph setup']
page=st.radio('Navigation',pages,horizontal=True,label_visibility='collapsed')

try:
    metrics=get_dashboard_metrics() or {}
except Exception:
    metrics={}

# ----------------------------- OVERVIEW -----------------------------
if page=='Overview':
    st.markdown('<div class="hero"><div class="eyebrow">Travel graph · Neo4j + Streamlit</div><h1>Travel data,<br>connected.</h1><p>ระบบนี้ใช้ Graph Database เพื่อเชื่อมโยง <b>ผู้ใช้ เพื่อน และสถานที่ท่องเที่ยว</b> เข้าด้วยกัน แล้วนำความสัมพันธ์เหล่านั้นมาใช้ค้นหาและแนะนำสถานที่ที่เกี่ยวข้องกับแต่ละคน</p></div>',unsafe_allow_html=True)
    st.markdown('<p class="intro">แทนที่จะดูข้อมูลเป็นรายการแยกกัน Travel Graph มองข้อมูลเป็นเครือข่าย: ใครเป็นเพื่อนกับใคร ใครเคยไปที่ไหน และความสัมพันธ์เหล่านี้ช่วยให้เราเห็นรูปแบบการเดินทางของผู้ใช้ได้อย่างไร</p>',unsafe_allow_html=True)
    c=st.columns(4)
    vals=[('Users',metrics.get('users',0),'จำนวนผู้ใช้ในกราฟ'),('Places',metrics.get('places',0),'สถานที่ท่องเที่ยว'),('Visits',metrics.get('visits',0),'รายการการไปเยือน'),('Friendships',metrics.get('friendships',0),'ความสัมพันธ์ระหว่างผู้ใช้')]
    for col,(a,b,d) in zip(c,vals):
        with col: metric_card(a,b,d)
    st.markdown('<div class="section-title">How the system works</div><div class="section-sub">โครงสร้างข้อมูลหลักของโปรเจกต์</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1: st.markdown('<div class="card"><span class="tag">01 · USER</span><h3>รู้ว่าใครกำลังเดินทาง</h3><p>แต่ละผู้ใช้มีตัวตนใน Graph เช่น U001, U002 และมีข้อมูลการเชื่อมโยงกับผู้ใช้อื่น</p></div>',unsafe_allow_html=True)
    with c2: st.markdown('<div class="card"><span class="tag">02 · RELATIONSHIP</span><h3>เชื่อมโยงผ่าน FRIEND_OF</h3><p>ความสัมพันธ์ระหว่างผู้ใช้ทำให้ระบบสามารถมองเห็นเครือข่ายเพื่อนของแต่ละคน</p></div>',unsafe_allow_html=True)
    with c3: st.markdown('<div class="card"><span class="tag">03 · PLACE</span><h3>เชื่อมกับสถานที่ที่เคยไป</h3><p>ความสัมพันธ์ VISITED เชื่อมผู้ใช้กับสถานที่ และเป็นฐานสำหรับการค้นหาและ recommendation</p></div>',unsafe_allow_html=True)

# ----------------------------- RECOMMEND -----------------------------
elif page=='Recommendations':
    st.markdown('<div class="section-title">Recommendations</div><div class="section-sub">คำแนะนำจากพฤติกรรมของเครือข่ายเพื่อน</div>',unsafe_allow_html=True)
    st.markdown('<div class="info-box"><b>ระบบทำงานอย่างไร?</b><br>1) หาเพื่อนที่เชื่อมโยงกับผู้ใช้ → 2) ดูสถานที่ที่เพื่อนเคยไป → 3) ตัดสถานที่ที่ผู้ใช้เคยไปแล้ว → 4) จัดลำดับตามจำนวนเพื่อนที่เคยไปสถานที่นั้น</div>',unsafe_allow_html=True)
    uid=user_select('recommend_user')
    if uid:
        rows=recommend_places(uid) or []
        if rows:
            for i,r in enumerate(rows,1):
                score=r.get('friend_score',r.get('score',0))
                st.markdown(f'<div class="place"><span class="score">{score} friends</span><div class="place-title">{i:02d} · 📍 {esc(r.get("place_name",r.get("name","Unknown place")))}</div><div class="place-meta">{esc(r.get("place_id",""))} · สถานที่ที่คนในเครือข่ายของคุณเคยไป</div></div>',unsafe_allow_html=True)
        else: st.markdown('<div class="empty">ยังไม่มีสถานที่แนะนำสำหรับผู้ใช้นี้จากข้อมูลปัจจุบัน</div>',unsafe_allow_html=True)

# ----------------------------- SEARCH -----------------------------
elif page=='Search places':
    st.markdown('<div class="section-title">Search places</div><div class="section-sub">ค้นหาสถานที่จากข้อมูลใน Neo4j</div>',unsafe_allow_html=True)
    q=st.text_input('ค้นหาสถานที่',placeholder='เช่น Wat, Beach, National Park ...')
    if q.strip():
        rows=search_places(q.strip()) or []
        if rows:
            for r in rows:
                st.markdown(f'<div class="place"><div class="place-title">📍 {esc(r.get("name",r.get("place_name","Unknown")))}</div><div class="place-meta">{esc(r.get("place_id",""))}</div></div>',unsafe_allow_html=True)
        else: st.markdown('<div class="empty">ไม่พบสถานที่ที่ตรงกับคำค้น</div>',unsafe_allow_html=True)
    else: st.markdown('<div class="empty">พิมพ์ชื่อหรือคำที่เกี่ยวข้องกับสถานที่เพื่อเริ่มค้นหา</div>',unsafe_allow_html=True)

# ----------------------------- VISITED -----------------------------
elif page=='Visited places':
    st.markdown('<div class="section-title">Visited places</div><div class="section-sub">ประวัติสถานที่ที่ผู้ใช้เคยไป</div>',unsafe_allow_html=True)
    uid=user_select('visited_user')
    if uid:
        rows=visited_places(uid) or []
        if rows:
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        else: st.markdown('<div class="empty">ผู้ใช้นี้ยังไม่มีประวัติการเดินทาง</div>',unsafe_allow_html=True)

# ----------------------------- GRAPH -----------------------------
elif page=='Graph explorer':
    st.markdown('<div class="section-title">Graph explorer</div><div class="section-sub">ดูความสัมพันธ์ของผู้ใช้ เพื่อน และสถานที่ในรูปแบบ Graph</div>',unsafe_allow_html=True)
    st.markdown('<div class="info-box"><b>FRIEND_OF</b> เชื่อม User ↔ User &nbsp;&nbsp;•&nbsp;&nbsp; <b>VISITED</b> เชื่อม User → Place<br>หน้าจอนี้ช่วยให้เห็นโครงสร้างเครือข่ายเดียวกับที่ recommendation query ใช้งาน</div>',unsafe_allow_html=True)
    uid=user_select('graph_user')
    if uid:
        st.graphviz_chart(relationship_graph(uid),use_container_width=True)
        rows=graph_neighborhood(uid) or []
        if rows:
            with st.expander('ดู relationship data'):
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ----------------------------- POPULAR -----------------------------
elif page=='Popular places':
    st.markdown('<div class="section-title">Popular places</div><div class="section-sub">สถานที่ที่มีรายการ VISITED มากที่สุดในกราฟ</div>',unsafe_allow_html=True)
    limit=st.slider('จำนวนสถานที่',3,10,8)
    rows=popular_places(limit) or []
    if rows:
        for i,r in enumerate(rows,1):
            st.markdown(f'<div class="place"><span class="score">{r.get("visit_count",r.get("visits",0))} visits</span><div class="place-title">{i:02d} · 📍 {esc(r.get("name",r.get("place_name","Unknown")))}</div><div class="place-meta">{esc(r.get("place_id",""))}</div></div>',unsafe_allow_html=True)
    else: st.markdown('<div class="empty">ยังไม่มีข้อมูลการเยี่ยมชม</div>',unsafe_allow_html=True)

# ----------------------------- SETUP -----------------------------
elif page=='Graph setup':
    st.markdown('<div class="section-title">Graph setup</div><div class="section-sub">ตรวจสอบการเชื่อมต่อและเตรียมข้อมูล Travel Graph</div>',unsafe_allow_html=True)
    try:
        ok=ping()
    except Exception: ok=False
    st.markdown(f'<div class="info-box"><b>{"● Neo4j connected" if ok else "● Neo4j connection unavailable"}</b><br>หน้านี้ใช้สำหรับตรวจสอบ connection และ seed/update ข้อมูลตาม schema ของโปรเจกต์</div>',unsafe_allow_html=True)
    c=st.columns(4)
    vals=[('Users',metrics.get('users',0)),('Places',metrics.get('places',0)),('Visits',metrics.get('visits',0)),('Friendships',metrics.get('friendships',0))]
    for col,(a,b) in zip(c,vals):
        with col: metric_card(a,b,'current graph')
    if st.button('↻ Seed / Update Travel Graph',type='primary'):
        with st.spinner('กำลังอัปเดตข้อมูล...'):
            seed_data()
        st.success('อัปเดต Travel Graph เรียบร้อยแล้ว')
        st.rerun()

# ----------------------------- ADD VISIT -----------------------------
with st.expander('＋ เพิ่มประวัติการเดินทาง'):
    st.caption('เพิ่มความสัมพันธ์ VISITED ระหว่างผู้ใช้กับสถานที่ โดยระบบจะบันทึกวันที่ที่ระบุ')
    opts=user_options()
    if opts:
        ids=[x[0] for x in opts]
        names={x[0]:x[1] for x in opts}
        a,b,c=st.columns([1,1,1])
        with a: uid=st.selectbox('User',ids,key='add_uid',format_func=lambda x:f'{names.get(x,x)} · {x}')
        with b: pid=st.text_input('Place ID',placeholder='เช่น P001')
        with c: dt=st.date_input('Visit date')
        if st.button('บันทึก Visit',key='save_visit'):
            if pid.strip():
                add_visit(uid,pid.strip(),dt.isoformat())
                st.success('บันทึก VISITED เรียบร้อยแล้ว')
            else: st.warning('กรุณาระบุ Place ID')

st.markdown('<div class="footer">Travel Graph Explorer · Neo4j Aura · User → FRIEND_OF → User → VISITED → Place</div>',unsafe_allow_html=True)
