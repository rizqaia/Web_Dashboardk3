import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# =========================
# File CSV
# =========================
FILE_MANHOURS = "data_manhours.csv"
FILE_ACCIDENT = "data_accident.csv"
FILE_PATROL = "data_patrol.csv"

# =========================
# Utility Functions
# =========================
def load_data(file, columns):
    if os.path.exists(file) and os.path.getsize(file) > 0:
        try:
            return pd.read_csv(file)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

def save_data(file, df):
    df.to_csv(file, index=False)

# =========================
# Login Functions
# =========================
def login():
    st.sidebar.subheader("Login Admin")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login", key="login_btn"):
        if username == "rizqa" and password == "admin123":
            st.session_state["logged_in"] = True
            st.sidebar.success("Login berhasil sebagai Admin")
        else:
            st.sidebar.error("Username atau password salah")

def logout():
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state["logged_in"] = False
        st.sidebar.success("Berhasil logout")

# =========================
# Dashboard
# =========================
def dashboard(df_man, df_acc, df_patrol):
    st.markdown(
        """
        <style>
        .stApp { background-color: #C2B280; }
        div.stButton > button { 
            background-color: #800000; 
            color: #FFFDD0; 
            border-radius: 10px; 
            padding: 8px 20px; 
            font-size: 14px; font-weight:bold; 
        }
        div.stButton > button:hover { background-color:#A0522D; color:white;}
        </style>
        """, unsafe_allow_html=True
    )

    st.title("HSE Dashboard")

    # ---------------- FILTER ----------------
    all_bulan = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    filter_bulan = st.selectbox("Filter Bulan", ["All"] + all_bulan)
    filter_tahun = st.selectbox("Filter Tahun", ["All"] + sorted(set(
        list(df_man["Tanggal"].dropna().astype(str).str[:4]) +
        list(df_acc["Tanggal"].dropna().astype(str).str[:4]) +
        list(df_patrol["Tanggal"].dropna().astype(str).str[:4])
    )))

    def apply_filter(df):
        if not df.empty and "Tanggal" in df.columns:
            df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
            df["Bulan"] = df["Tanggal"].dt.strftime("%b")
            df["Tahun"] = df["Tanggal"].dt.strftime("%Y")
            if filter_bulan != "All":
                df = df[df["Bulan"] == filter_bulan]
            if filter_tahun != "All":
                df = df[df["Tahun"] == filter_tahun]
        return df

    df_man = apply_filter(df_man)
    df_acc = apply_filter(df_acc)
    df_patrol = apply_filter(df_patrol)

    # ---------------- MANHOURS ----------------
    if not df_man.empty:
        today = datetime.now().date()
        total_today = df_man[df_man['Tanggal'].dt.date == today]['Total Manhours'].sum()
        total_all = df_man['Total Manhours'].sum()
        col1, col2 = st.columns(2)
        with col1: st.metric("Harian", total_today)
        with col2: st.metric("Total", total_all)

        monthly = df_man.groupby("Bulan")["Total Manhours"].sum().reset_index()
        max_row = monthly.loc[monthly['Total Manhours'].idxmax()]
        fig = px.bar(monthly, x="Bulan", y="Total Manhours", color_discrete_sequence=["#800000"])
        fig.update_traces(
            texttemplate=['%{y}' if val==max_row['Total Manhours'] else '' for val in monthly['Total Manhours']],
            textposition='outside'
        )
        fig.update_layout(xaxis_title=None, yaxis_title="Total Manhours", showlegend=False)
        st.subheader("Manhours per Bulan")
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- ACCIDENT ----------------
    if not df_acc.empty:
        st.subheader("Accident per Jenis")
        acc_count = df_acc["Jenis"].value_counts().reset_index()
        acc_count.columns = ["Jenis","Count"]
        max_row = acc_count.loc[acc_count['Count'].idxmax()]
        fig_acc = px.bar(acc_count, y="Jenis", x="Count", orientation="h", color_discrete_sequence=["#800000"])
        fig_acc.update_traces(
            texttemplate=['%{x}' if val==max_row['Count'] else '' for val in acc_count['Count']],
            textposition='outside'
        )
        fig_acc.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
        st.plotly_chart(fig_acc, use_container_width=True)

        # Line chart accident per bulan
        df_acc["Bulan"] = df_acc["Tanggal"].dt.strftime("%b")
        acc_per_bulan = df_acc.groupby("Bulan").size().reset_index(name="Jumlah")
        if not acc_per_bulan.empty:
            max_idx = acc_per_bulan["Jumlah"].idxmax()
            fig_line = px.line(acc_per_bulan, x="Bulan", y="Jumlah", color_discrete_sequence=["#800000"])
            fig_line.add_annotation(
                x=acc_per_bulan.loc[max_idx,"Bulan"],
                y=acc_per_bulan.loc[max_idx,"Jumlah"],
                text=str(acc_per_bulan.loc[max_idx,"Jumlah"]),
                showarrow=True, arrowhead=2
            )
            st.subheader("Accident per Bulan")
            st.plotly_chart(fig_line, use_container_width=True)

    # ---------------- SAFETY PATROL ----------------
    if not df_patrol.empty:
        st.subheader("Safety Patrol - Status")
        status_count = df_patrol["Status"].value_counts().reset_index()
        status_count.columns = ["Status","Count"]
        fig_pat = px.pie(status_count, names="Status", values="Count", color_discrete_sequence=["#800000","#DEB887"])
        fig_pat.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pat, use_container_width=True)

        st.subheader("Safety Patrol - Jenis Temuan")
        temuan_count = df_patrol["Jenis Temuan"].value_counts().reset_index()
        temuan_count.columns = ["Temuan","Count"]
        fig_tem = px.pie(temuan_count, names="Temuan", values="Count",
                         color_discrete_sequence=["#800000","#FFFDD0","#DEB887"])
        fig_tem.update_traces(textinfo="percent+value")
        st.plotly_chart(fig_tem, use_container_width=True)

        # Line chart temuan per bulan
        df_patrol["Bulan"] = df_patrol["Tanggal"].dt.strftime("%b")
        patrol_per_bulan = df_patrol.groupby("Bulan").size().reset_index(name="Jumlah")
        if not patrol_per_bulan.empty:
            max_idx = patrol_per_bulan["Jumlah"].idxmax()
            fig_line_pat = px.line(patrol_per_bulan, x="Bulan", y="Jumlah", color_discrete_sequence=["#800000"])
            fig_line_pat.add_annotation(
                x=patrol_per_bulan.loc[max_idx,"Bulan"],
                y=patrol_per_bulan.loc[max_idx,"Jumlah"],
                text=str(patrol_per_bulan.loc[max_idx,"Jumlah"]),
                showarrow=True, arrowhead=2
            )
            st.subheader("Jumlah Temuan per Bulan")
            st.plotly_chart(fig_line_pat, use_container_width=True)

# =========================
# Input Data (Admin Only)
# =========================
def input_data(df_man, df_acc, df_patrol):
    if not st.session_state.get("logged_in", False):
        st.warning("Hanya admin yang bisa input data")
        return df_man, df_acc, df_patrol

    st.header("Input Data Harian")
    tab1, tab2, tab3 = st.tabs(["Manhours","Accident","Safety Patrol"])

    # --- MANHOURS ---
    with tab1:
        tanggal = st.date_input("Tanggal")
        manpower = st.number_input("Jumlah Pekerja", 0)
        jam_kerja = st.number_input("Jam Kerja per Pekerja", 0)
        total = manpower * jam_kerja
        if st.button("Simpan Manhours"):
            new = pd.DataFrame([[tanggal,manpower,jam_kerja,total]], columns=df_man.columns)
            df_man = pd.concat([df_man,new], ignore_index=True)
            save_data(FILE_MANHOURS, df_man)
            st.success("Data Manhours tersimpan!")

    # --- ACCIDENT ---
    with tab2:
        tanggal = st.date_input("Tanggal Accident", key="acc")
        jenis = st.selectbox("Jenis Accident", ["Fatality","LTI","MTC","FAC","Near Miss","Property Damage","PAK"])
        kronologi = st.text_area("Kronologi Singkat")
        if st.button("Simpan Accident"):
            new = pd.DataFrame([[tanggal,jenis,kronologi]], columns=df_acc.columns)
            df_acc = pd.concat([df_acc,new], ignore_index=True)
            save_data(FILE_ACCIDENT, df_acc)
            st.success("Data Accident tersimpan!")

    # --- SAFETY PATROL ---
    with tab3:
        tanggal = st.date_input("Tanggal Patrol", key="pat")
        jenis = st.selectbox("Jenis Temuan", ["Environment","Cara Kerja","Manpower"])
        ditemukan = st.text_input("Ditemukan Oleh")
        status = st.selectbox("Status", ["Open","Close"])
        deskripsi = st.text_area("Deskripsi Temuan")
        foto = st.file_uploader("Upload Foto Temuan", type=["jpg","png","jpeg"])
        if st.button("Simpan Patrol"):
            new = pd.DataFrame([[tanggal,jenis,ditemukan,status,deskripsi,foto.name if foto else ""]], columns=df_patrol.columns)
            df_patrol = pd.concat([df_patrol,new], ignore_index=True)
            save_data(FILE_PATROL, df_patrol)
            st.success("Data Safety Patrol tersimpan!")

    # --- EXPORT DATA ---
    st.subheader("Export Data (Admin Only)")
    st.download_button(
        "Download Manhours CSV",
        df_man.to_csv(index=False).encode("utf-8"),
        "manhours.csv",
        "text/csv"
    )
    st.download_button(
        "Download Accident CSV",
        df_acc.to_csv(index=False).encode("utf-8"),
        "accident.csv",
        "text/csv"
    )
    st.download_button(
        "Download Patrol CSV",
        df_patrol.to_csv(index=False).encode("utf-8"),
        "patrol.csv",
        "text/csv"
    )

    return df_man, df_acc, df_patrol

# =========================
# MAIN
# =========================
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    menu = st.sidebar.radio("Menu", ["Dashboard","Input Data"])

    if st.session_state["logged_in"]:
        st.sidebar.success("Login sebagai Admin")
        logout()
    else:
        login()

    df_man = load_data(FILE_MANHOURS, ["Tanggal","Manpower","Jam Kerja","Total Manhours"])
    df_acc = load_data(FILE_ACCIDENT, ["Tanggal","Jenis","Kronologi"])
    df_patrol = load_data(FILE_PATROL, ["Tanggal","Jenis Temuan","Ditemukan Oleh","Status","Deskripsi","Foto"])

    if menu=="Dashboard":
        dashboard(df_man, df_acc, df_patrol)
    elif menu=="Input Data":
        df_man, df_acc, df_patrol = input_data(df_man, df_acc, df_patrol)

if __name__=="__main__":
    main()
