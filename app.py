from __future__ import annotations

import pandas as pd
import streamlit as st

# สมมติว่าไฟล์จัดการ Neo4j ข้างต้นชื่อ neo4j_service.py หรืออยู่ในโปรเจกต์เดียวกัน
import neo4j_service as db

st.set_page_config(
    page_title="Control Center - Travel Graph",
    page_icon="✈️",
    layout="wide",
)

# --- Header & Metrics Dashboard ---
st.markdown("### ⚙️ Control Center")
st.markdown("จัดการและตรวจสอบระบบ Travel")

# ตรวจสอบการเชื่อมต่อ
try:
    if not db.ping():
        st.error("ไม่สามารถเชื่อมต่อฐานข้อมูล Neo4j ได้ กรุณาตรวจสอบการตั้งค่าใน .streamlit/secrets.toml")
        st.stop()
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
    st.stop()

# ดึงข้อมูลสถิติมาแสดงด้านบน
metrics = db.get_dashboard_metrics()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Users", metrics["users"])
with col2:
    st.metric("Places", metrics["places"])
with col3:
    st.metric("Visited", metrics["visits"])
with col4:
    st.metric("Friendships", metrics["friendships"])

st.markdown("---")

# --- Admin Section: จัดการข้อมูล & คำสั่งระบบ ---
st.markdown("### 🛠️ แอดมิน: จัดการข้อมูล & คำสั่งระบบ")

admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
    "➕ เพิ่มข้อมูล", 
    "🗑️ ลบข้อมูล", 
    "💻 รันคำสั่ง Cypher", 
    "🚀 โหลดข้อมูลเริ่มต้น (Seed Data)"
])

with admin_tab1:
    add_type = st.selectbox("เลือกประเภทที่ต้องการเพิ่ม", ["User", "Place", "Friendship (เพื่อน)"])
    
    if add_type == "User":
        new_uid = st.text_input("User ID (เช่น U011)")
        new_uname = st.text_input("ชื่อผู้ใช้")
        if st.button("บันทึก User ใหม่", type="primary"):
            if new_uid and new_uname:
                try:
                    db.query(
                        "MERGE (u:User {user_id: $uid}) SET u.name = $name", 
                        {"uid": new_uid, "name": new_uname}, 
                        write=True
                    )
                    st.success(f"เพิ่มผู้ใช้ {new_uname} ({new_uid}) สำเร็จ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")
                
    elif add_type == "Place":
        new_pid = st.text_input("Place ID (เช่น P011)")
        new_pname = st.text_input("ชื่อสถานที่")
        if st.button("บันทึก Place ใหม่", type="primary"):
            if new_pid and new_pname:
                try:
                    db.query(
                        "MERGE (p:Place {place_id: $pid}) SET p.name = $name", 
                        {"pid": new_pid, "name": new_pname}, 
                        write=True
                    )
                    st.success(f"เพิ่มสถานที่ {new_pname} ({new_pid}) สำเร็จ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")
                
    else:
        u1 = st.text_input("User ID คนที่ 1 (เช่น U001)")
        u2 = st.text_input("User ID คนที่ 2 (เช่น U002)")
        if st.button("สร้างความสัมพันธ์เพื่อน (FRIEND_OF)", type="primary"):
            if u1 and u2:
                try:
                    db.query(
                        """
                        MATCH (a:User {user_id: $u1})
                        MATCH (b:User {user_id: $u2})
                        MERGE (a)-[:FRIEND_OF]->(b)
                        """, 
                        {"u1": u1, "u2": u2}, 
                        write=True
                    )
                    st.success(f"เชื่อมความสัมพันธ์ระหว่าง {u1} และ {u2} สำเร็จ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
            else:
                st.warning("กรุณากรอก User ID ทั้งสองคน")

with admin_tab2:
    del_type = st.selectbox("เลือกประเภทที่ต้องการลบ", ["User", "Place"])
    del_id = st.text_input("ระบุ ID ที่ต้องการลบ (เช่น U001 หรือ P001)")
    if st.button("ยืนยันการลบ", type="secondary"):
        if del_id:
            try:
                if del_type == "User":
                    db.query(
                        "MATCH (u:User {user_id: $id}) DETACH DELETE u", 
                        {"id": del_id}, 
                        write=True
                    )
                else:
                    db.query(
                        "MATCH (p:Place {place_id: $id}) DETACH DELETE p", 
                        {"id": del_id}, 
                        write=True
                    )
                st.warning(f"ลบข้อมูล ID: {del_id} เรียบร้อยแล้ว")
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            st.warning("กรุณาระบุ ID ที่ต้องการลบ")

with admin_tab3:
    st.info("พิมพ์คำสั่ง Cypher Query เพื่อจัดการฐานข้อมูลโดยตรง")
    cypher_cmd = st.text_area("Cypher Query", placeholder="MATCH (n) RETURN n LIMIT 10")
    if st.button("รันคำสั่ง Cypher"):
        if cypher_cmd.strip():
            try:
                # ตรวจสอบอัตโนมัติว่าเป็นคำสั่งเขียนข้อมูลหรือไม่
                is_write = any(k in cypher_cmd.upper() for k in ["CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP"])
                res = db.query(cypher_cmd, write=is_write)
                st.success("รันคำสั่งสำเร็จ!")
                if res:
                    st.dataframe(pd.DataFrame(res), use_container_width=True)
                else:
                    st.info("คำสั่งทำงานสำเร็จ แต่ไม่มีข้อมูลส่งกลับ")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            st.warning("กรุณากรอกคำสั่ง Cypher")

with admin_tab4:
    st.warning("การกดปุ่มนี้จะทำการสร้าง Constraints และเพิ่มข้อมูลตัวอย่างชุดเริ่มต้น (Seed Data)")
    if st.button("🔄 เริ่มต้น Seed Data เข้าฐานข้อมูล"):
        try:
            db.seed_data()
            st.success("โหลดข้อมูลเริ่มต้นเข้า Neo4j สำเร็จเรียบร้อยแล้ว!")
            st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการ Seed Data: {e}")

st.markdown("---")

# --- User Explorer Section ---
st.markdown("### 🔍 สำรวจข้อมูลผู้ใช้และการเดินทาง (Travel Explorer)")

users_list = db.get_users()
if users_list:
    user_options = {f"{u['user_id']} - {u['name']}": u['user_id'] for u in users_list}
    selected_label = st.selectbox("เลือกผู้ใช้เพื่อดูโปรไฟล์และการแนะนำสถานที่", list(user_options.keys()))
    selected_user_id = user_options[selected_label]

    profile = db.get_profile(selected_user_id)
    if profile:
        c1, c2, c3 = st.columns(3)
        c1.metric("ชื่อผู้ใช้", profile["name"])
        c2.metric("จำนวนเพื่อน", profile["friend_count"])
        c3.metric("สถานที่ที่เคยไป", profile["visit_count"])

    # แสดงแท็บข้อมูลย่อยของผู้ใช้คนนี้
    u_tab1, u_tab2, u_tab3, u_tab4 = st.tabs(["🗺️ สถานที่ที่เคยไป", "💡 แนะนำสถานที่ท่องเที่ยว", "➕ บันทึกการเดินทางใหม่", "🌐 กราฟความสัมพันธ์รอบตัว"])

    with u_tab1:
        visited = db.visited_places(selected_user_id)
        if visited:
            st.dataframe(pd.DataFrame(visited), use_container_width=True)
        else:
            st.info("ยังไม่มีประวัติการเดินทาง")

    with u_tab2:
        recs = db.recommend_places(selected_user_id)
        if recs:
            st.dataframe(pd.DataFrame(recs), use_container_width=True)
        else:
            st.info("ยังไม่มีคำแนะนำสถานที่ท่องเที่ยวจากเพื่อนในขณะนี้")

    with u_tab3:
        all_places = db.search_search_places_placeholder = db.search_places("")
        place_options = {f"{p['place_id']} - {p['name']}": p['place_id'] for p in db.search_places()}
        
        if place_options:
            target_place_label = st.selectbox("เลือกสถานที่", list(place_options.keys()), key="target_place")
            target_place_id = place_options[target_place_label]
            visit_date_input = st.date_input("วันที่เดินทางไป")
            
            if st.button("บันทึกการเดินทาง (Add Visit)"):
                try:
                    db.add_visit(selected_user_id, target_place_id, str(visit_date_input))
                    st.success("บันทึกการเดินทางสำเร็จ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            st.warning("ยังไม่มีข้อมูลสถานที่ในระบบ กรุณาเพิ่มสถานที่ก่อน")

    with u_tab4:
        st.markdown("##### ความสัมพันธ์รอบตัวผู้ใช้ (Neighborhood)")
        neighborhood = db.graph_neighborhood(selected_user_id)
        if neighborhood:
            st.dataframe(pd.DataFrame(neighborhood), use_container_width=True)
        else:
            st.info("ไม่พบข้อมูลความสัมพันธ์รอบตัว")
else:
    st.info("ยังไม่มีข้อมูลผู้ใช้ในระบบ กรุณาไปที่แท็บแอดมินเพื่อโหลด Seed Data หรือเพิ่มผู้ใช้ใหม่")