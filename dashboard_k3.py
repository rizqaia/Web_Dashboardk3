import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import io

# =========================
# File CSV
# =========================
FILE_MANHOURS = "data_manhours.csv"
FILE_ACCIDENT = "data_accident.csv"
FILE_PATROL = "data_patrol.csv"
FILE_MANPOWER = "data_manpower.csv"

# =========================
# Utility Functions
# =========================
def load_data(file, columns=None):
    """
    Jika file ada dan tidak kosong -> load CSV.
    Jika tidak ada atau kosong -> kembalikan DataFrame dengan kolom (jika diberikan).
    """
    if os.path.exists(file) and os.path.getsize(file) > 0:
        try:
            return pd.read_csv(file)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=columns if columns else [])
    else:
        return pd.DataFrame(columns=columns if columns else [])

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
# Dashboard utama
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
    # kumpulkan tahun dari semua dataset (jika kolom Tanggal ada)
    years = set()
    for df in [df_man, df_acc, df_patrol]:
        if not df.empty and "Tanggal" in df.columns:
            years.update(list(df["Tanggal"].dropna().astype(str).str[:4]))
    filter_tahun = st.selectbox("Filter Tahun", ["All"] + sorted(years))

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
    if not df_man.empty and "Total Manhours" in df_man.columns:
        today = datetime.now().date()
        total_today = df_man[df_man['Tanggal'].dt.date == today]['Total Manhours'].sum()
        total_all = df_man['Total Manhours'].sum()
        col1, col2 = st.columns(2)
        with col1: st.metric("Harian", total_today)
        with col2: st.metric("Total", total_all)

        monthly = df_man.groupby("Bulan")["Total Manhours"].sum().reset_index()
        if not monthly.empty:
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
    if not df_acc.empty and "Jenis" in df_acc.columns:
        st.subheader("Accident per Jenis")
        acc_count = df_acc["Jenis"].value_counts().reset_index()
        acc_count.columns = ["Jenis","Count"]
        if not acc_count.empty:
            max_row = acc_count.loc[acc_count['Count'].idxmax()]
            fig_acc = px.bar(acc_count, y="Jenis", x="Count", orientation="h", color_discrete_sequence=["#800000"])
            fig_acc.update_traces(
                texttemplate=['%{x}' if val==max_row['Count'] else '' for val in acc_count['Count']],
                textposition='outside'
            )
            fig_acc.update_layout(xaxis_title=None, yaxis_title=None, showlegend=False)
            st.plotly_chart(fig_acc, use_container_width=True)

        # Line chart accident per bulan
        if "Tanggal" in df_acc.columns:
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
    if not df_patrol.empty and "Status" in df_patrol.columns:
        st.subheader("Safety Patrol - Status")
        status_count = df_patrol["Status"].value_counts().reset_index()
        status_count.columns = ["Status","Count"]
        fig_pat = px.pie(status_count, names="Status", values="Count", color_discrete_sequence=["#800000","#DEB887"])
        fig_pat.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pat, use_container_width=True)

        if "Jenis Temuan" in df_patrol.columns:
            st.subheader("Safety Patrol - Jenis Temuan")
            temuan_count = df_patrol["Jenis Temuan"].value_counts().reset_index()
            temuan_count.columns = ["Temuan","Count"]
            fig_tem = px.pie(temuan_count, names="Temuan", values="Count",
                             color_discrete_sequence=["#800000","#FFFDD0","#DEB887"])
            fig_tem.update_traces(textinfo="percent+value")
            st.plotly_chart(fig_tem, use_container_width=True)

# =========================
# Input Data (Admin Only)
# =========================
def input_data(df_man, df_acc, df_patrol):
    """Form input data Manhours, Accident, dan Safety Patrol (khusus Admin)."""
    if not st.session_state.get("logged_in", False):
        st.warning("Hanya admin yang bisa input data")
        return df_man, df_acc, df_patrol

    st.header("Input Data Harian")
    tab1, tab2, tab3 = st.tabs(["Manhours", "Accident", "Safety Patrol"])

    # --- TAB 1: MANHOURS ---
    with tab1:
        st.subheader("Input Data Manhours")
        tanggal = st.date_input("Tanggal")
        manpower = st.number_input("Jumlah Pekerja", min_value=0, step=1)
        jam_kerja = st.number_input("Jam Kerja per Pekerja", min_value=0, step=1)
        total = manpower * jam_kerja

        if st.button("Simpan Manhours"):
            new = pd.DataFrame([[tanggal, manpower, jam_kerja, total]], columns=df_man.columns)
            df_man = pd.concat([df_man, new], ignore_index=True)
            save_data(FILE_MANHOURS, df_man)
            st.success("Data Manhours tersimpan")

    # --- TAB 2: ACCIDENT ---
    with tab2:
        st.subheader("Input Data Accident")
        tanggal = st.date_input("Tanggal Accident", key="acc")
        jenis = st.selectbox("Jenis Accident", ["Fatality", "LTI", "MTC", "FAC", "Near Miss", "Property Damage", "PAK"])
        kronologi = st.text_area("Kronologi Singkat")

        if st.button("Simpan Accident"):
            new = pd.DataFrame([[tanggal, jenis, kronologi]], columns=df_acc.columns)
            df_acc = pd.concat([df_acc, new], ignore_index=True)
            save_data(FILE_ACCIDENT, df_acc)
            st.success("Data Accident tersimpan")

    # --- TAB 3: SAFETY PATROL ---
    with tab3:
        st.subheader("📋 Input / Update Data Safety Patrol")

    FILE_SAFETY_PATROL = FILE_PATROL  # pakai file yang sudah ada

    # Pastikan folder upload ada
    upload_dir = "uploads/safety_patrol"
    os.makedirs(upload_dir, exist_ok=True)

    # Inisialisasi dataframe jika kosong
    if df_patrol.empty:
        df_patrol = pd.DataFrame(columns=[
            "Kode Temuan", "Tanggal", "Jenis Temuan", "Ditemukan Oleh",
            "Status", "Deskripsi", "Foto"
        ])

    # Dropdown kode lama
    kode_options = ["Tambah Data Baru"] + df_patrol["Kode Temuan"].dropna().unique().tolist()
    selected_kode = st.selectbox("Pilih Kode Temuan (untuk update data lama):", kode_options)

    if selected_kode != "Tambah Data Baru":
        data_lama = df_patrol[df_patrol["Kode Temuan"] == selected_kode].iloc[0]
        kode_temuan = data_lama["Kode Temuan"]
        tanggal = st.date_input("Tanggal", value=pd.to_datetime(data_lama["Tanggal"]))
        jenis_temuan = st.selectbox("Jenis Temuan", ["Cara Kerja", "Environment", "Manpower"],
                                    index=["Cara Kerja", "Environment", "Manpower"].index(data_lama["Jenis Temuan"]))
        ditemukan_oleh = st.text_input("Ditemukan Oleh", value=data_lama["Ditemukan Oleh"])
        status = st.selectbox("Status", ["Open", "Progress", "Close"],
                            index=["Open", "Progress", "Close"].index(data_lama["Status"]))
        deskripsi = st.text_area("Deskripsi Temuan", value=data_lama["Deskripsi"])
        foto = st.file_uploader("Upload Foto Temuan (opsional)", type=["jpg", "jpeg", "png"], key="foto_update")

        # Tampilkan foto lama (jika ada)
        if data_lama["Foto"]:
            st.image(data_lama["Foto"], caption="Foto Lama", width=250)

    else:
        kode_temuan = None
        tanggal = st.date_input("Tanggal", format="DD-MM-YYYY")
        jenis_temuan = st.selectbox("Jenis Temuan", ["Cara Kerja", "Environment", "Manpower"])
        ditemukan_oleh = st.text_input("Ditemukan Oleh")
        status = st.selectbox("Status", ["Open", "Progress", "Close"])
        deskripsi = st.text_area("Deskripsi Temuan")
        foto = st.file_uploader("Upload Foto Temuan (opsional)", type=["jpg", "jpeg", "png"], key="foto_baru")

    if st.button("💾 Simpan / Update Data Patrol"):
        # Buat kode otomatis jika belum ada
        if not kode_temuan:
            nomor = len(df_patrol) + 1
            kode_temuan = f"SP-{datetime.now().strftime('%Y%m%d')}-{nomor:03d}"

        foto_path = ""
        if foto is not None:
            foto_dir = "uploads/safety_patrol"
    os.makedirs(foto_dir, exist_ok=True)
    foto_path = os.path.join(foto_dir, foto.name)

        # Jika foto kosong tapi data lama punya foto
        if selected_kode != "Tambah Data Baru" and not foto_path:
            foto_path = data_lama["Foto"]

        new_data = pd.DataFrame([{
            "Kode Temuan": kode_temuan,
            "Tanggal": tanggal,
            "Jenis Temuan": jenis_temuan,
            "Ditemukan Oleh": ditemukan_oleh,
            "Status": status,
            "Deskripsi": deskripsi,
            "Foto": foto_path
        }])

        if kode_temuan in df_patrol["Kode Temuan"].values:
            df_patrol.loc[df_patrol["Kode Temuan"] == kode_temuan, :] = new_data.values[0]
            st.success(f"✅ Data {kode_temuan} berhasil diperbarui!")
        else:
            df_patrol = pd.concat([df_patrol, new_data], ignore_index=True)
            st.success(f"✅ Data baru {kode_temuan} berhasil disimpan!")

        save_data(FILE_SAFETY_PATROL, df_patrol)

    st.markdown("---")
    st.subheader("📥 Unduh Data Safety Patrol")
    if not df_patrol.empty:
        output = io.BytesIO()
        df_patrol.to_excel(output, index=False, sheet_name="Safety Patrol")
        output.seek(0)
        st.download_button(
            label="💾 Download Data Safety Patrol (Excel)",
            data=output,
            file_name=f"data_safety_patrol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Belum ada data Safety Patrol untuk diunduh.")
    return df_man, df_acc, df_patrol

# =========================
# Input Data Manpower (Admin Only)
# =========================
def input_data_manpower(df_manpower):
    st.header("📋 Input Data Manpower")

    if not st.session_state.get("logged_in", False):
        st.warning("Hanya admin yang bisa input data")
        return df_manpower

    if df_manpower is None or df_manpower.empty:
        df_manpower = pd.DataFrame(columns=["Tanggal","Proyek","Jumlah Pekerja","Nama Pekerja"])

    tanggal = st.date_input("Tanggal", format="DD-MM-YYYY")

    list_proyek = ["PT. GEA", "PT. Glico", "PT. Ciomas", "PT. Asahi", "Lainnya"]
    pilihan_proyek = st.selectbox("Nama Proyek / Lokasi", list_proyek)
    if pilihan_proyek == "Lainnya":
        proyek = st.text_input("Masukkan Nama Proyek / Lokasi Lainnya")
    else:
        proyek = pilihan_proyek

    jumlah = st.number_input("Jumlah Pekerja", min_value=0, step=1)
    nama_pekerja = st.text_area("Nama Pekerja (pisahkan dengan koma atau baris baru)")

    if st.button("💾 Simpan Data Manpower"):
        if proyek.strip() == "":
            st.error("Nama proyek tidak boleh kosong!")
        else:
            new_row = pd.DataFrame(
                [[tanggal, proyek, jumlah, nama_pekerja]],
                columns=["Tanggal","Proyek","Jumlah Pekerja","Nama Pekerja"]
            )
            df_manpower = pd.concat([df_manpower, new_row], ignore_index=True)
            save_data(FILE_MANPOWER, df_manpower)
            st.success("✅ Data Manpower berhasil disimpan!")

    return df_manpower

# =========================
# Dashboard Manpower
# =========================
def dashboard_manpower(df_manpower):
    st.header("📊 Dashboard Manpower")

    if df_manpower.empty:
        st.info("Belum ada data manpower.")
        return

    df_manpower["Tanggal"] = pd.to_datetime(df_manpower["Tanggal"], errors="coerce")
    df_manpower["Bulan"] = df_manpower["Tanggal"].dt.strftime("%b")
    df_manpower["Tahun"] = df_manpower["Tanggal"].dt.strftime("%Y")

    proyek_list = ["All"] + sorted(df_manpower["Proyek"].dropna().unique().tolist())
    selected_proyek = st.selectbox("Filter Proyek / Lokasi", proyek_list)
    tahun_list = ["All"] + sorted(df_manpower["Tahun"].dropna().unique().tolist())
    selected_tahun = st.selectbox("Filter Tahun", tahun_list)
    bulan_list = ["All"] + sorted(df_manpower["Bulan"].dropna().unique().tolist())
    selected_bulan = st.selectbox("Filter Bulan", bulan_list)

    df_filtered = df_manpower.copy()
    if selected_proyek != "All":
        df_filtered = df_filtered[df_filtered["Proyek"] == selected_proyek]
    if selected_tahun != "All":
        df_filtered = df_filtered[df_filtered["Tahun"] == selected_tahun]
    if selected_bulan != "All":
        df_filtered = df_filtered[df_filtered["Bulan"] == selected_bulan]

    # Grafik
    if selected_bulan != "All":
        chart = df_filtered.groupby("Tanggal")["Jumlah Pekerja"].sum().reset_index()
        fig = px.bar(chart, x="Tanggal", y="Jumlah Pekerja", color_discrete_sequence=["#800000"])
        st.subheader("Jumlah Pekerja per Hari")
        st.plotly_chart(fig, use_container_width=True)
    else:
        chart = df_filtered.groupby("Bulan")["Jumlah Pekerja"].sum().reset_index()
        fig = px.bar(chart, x="Bulan", y="Jumlah Pekerja", color_discrete_sequence=["#800000"])
        st.subheader("Jumlah Pekerja per Bulan")
        st.plotly_chart(fig, use_container_width=True)

    # Download
    st.markdown("---")
    st.subheader("📥 Unduh Laporan Manpower")
    output = io.BytesIO()
    df_filtered.to_excel(output, index=False, sheet_name="Data Manpower")
    output.seek(0)
    st.download_button(
        label="💾 Download Data Manpower (Excel)",
        data=output,
        file_name=f"laporan_manpower_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# Dokumen PDF
# =========================
def dokumen_pdf():
    st.header("📂 Dokumen PDF")

    # Pastikan folder PDF ada
    pdf_dir = "uploads/pdf"
    os.makedirs(pdf_dir, exist_ok=True)

    # Hanya admin yang boleh upload PDF
    if st.session_state.get("logged_in", False):
        uploaded_file = st.file_uploader("Upload file PDF", type=["pdf"])
        if uploaded_file is not None:
            save_path = os.path.join(pdf_dir, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ File berhasil diupload: {uploaded_file.name}")

    # Tampilkan hanya file PDF di folder khusus
    files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]

    if files:
        st.subheader("📥 Unduh File PDF")
        for file in files:
            file_path = os.path.join(pdf_dir, file)
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"📄 Download {file}",
                    data=f.read(),
                    file_name=file,
                    mime="application/pdf"
                )
    else:
        st.info("Belum ada file PDF yang diupload.")


# =========================
# MAIN
# =========================
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    menu = st.sidebar.radio("Menu", [
        "Dashboard",
        "Input Data",
        "Data Manpower",
        "Dokumen PDF"
    ])

    if st.session_state["logged_in"]:
        st.sidebar.success("Login sebagai Admin")
        logout()
    else:
        login()

    df_man = load_data(FILE_MANHOURS, ["Tanggal","Manpower","Jam Kerja","Total Manhours"])
    df_acc = load_data(FILE_ACCIDENT, ["Tanggal","Jenis","Kronologi"])
    df_patrol = load_data(FILE_PATROL, ["Tanggal","Jenis Temuan","Ditemukan Oleh","Status","Deskripsi","Foto"])
    df_manpower = load_data(FILE_MANPOWER, ["Tanggal","Proyek","Jumlah Pekerja","Nama Pekerja"])

    if menu == "Dashboard":
        dashboard(df_man, df_acc, df_patrol)
    elif menu == "Input Data":
        df_man, df_acc, df_patrol = input_data(df_man, df_acc, df_patrol)
    elif menu == "Data Manpower":
        df_manpower = input_data_manpower(df_manpower)
        dashboard_manpower(df_manpower)
    elif menu == "Dokumen PDF":
        dokumen_pdf()

if __name__ == "__main__":
    main()
