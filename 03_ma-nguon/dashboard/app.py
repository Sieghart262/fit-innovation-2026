"""Dashboard TCI – NEU Academic Integrity & True Competency Analytics (Streamlit).

Phân quyền (quyết định của đội):
    - Công khai: chỉ số liệu tổng hợp; ô nào dưới 5 SV hiện "<5"; không tra cứu từng SV.
    - Nhà trường: xem hết, tra cứu từng SV, tải danh sách phân loại, chạy với file điểm mới.
      Cần mật khẩu đặt trong biến môi trường FIT_MAT_KHAU_NHA_TRUONG (không ghi vào code).

Dữ liệu: đọc kết quả do run_gp3.py ghi ra (mặc định 01_du-lieu/ket-qua/). Đặt biến môi trường
FIT_KET_QUA để trỏ tới thư mục khác (ví dụ kết quả từ DỮ LIỆU GIẢ khi demo công khai).

Chạy (từ thư mục gốc dự án):
    .venv/Scripts/streamlit.exe run 03_ma-nguon/dashboard/app.py
"""

from __future__ import annotations

import hmac
import os
import sys
import tempfile
import warnings
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

THU_MUC_MA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(THU_MUC_MA))

from eda import config as cf  # noqa: E402
from gp1 import cau_hinh as ch1  # noqa: E402
from gp3 import cau_hinh as ch3  # noqa: E402

KET_QUA = Path(os.environ.get("FIT_KET_QUA", cf.THU_MUC_GOC / "01_du-lieu" / "ket-qua"))
NGUONG = cf.NGUONG_NHOM_TOI_THIEU
MAU_TRUOC, MAU_SAU = "#2a78d6", "#eb6834"   # bảng màu đã kiểm tra an toàn cho người mù màu
CONG_KHAI, NHA_TRUONG = "Công khai", "Nhà trường"


@st.cache_data(show_spinner=False)
def doc_ket_qua(thu_muc: str) -> dict:
    """Đọc các file kết quả của 3 giải pháp (CSV UTF-8 có BOM).

    Tham số:
        thu_muc: thư mục gốc kết quả (có gp1/, gp2/, gp3/).
    Trả về:
        dict bảng; thiếu file nào thì bỏ qua file đó.
    Vì sao cần: dashboard chỉ đọc kết quả đã tính sẵn nên mở nhanh; cache để không đọc lại mỗi lần bấm.
    """
    g = Path(thu_muc)
    ten = {"lop": g / "gp1" / "chi_so_chi_tiet.csv", "hieu_chinh": g / "gp2" / "hieu_chinh_theo_lop.csv",
           "sv": g / "gp3" / "phan_loai_sinh_vien.csv", "mon": g / "gp3" / "mon_cua_sinh_vien.csv"}
    return {k: pd.read_csv(p, encoding="utf-8-sig") for k, p in ten.items() if p.exists()}


def an_nho(so: int) -> str:
    """Hiện số SV ở chế độ công khai: nhóm dưới 5 người hiện "<5"."""
    return "<5" if 0 < so < NGUONG else f"{so:,}"


def bieu_do_muc(sv: pd.DataFrame) -> alt.Chart:
    """Cột ghép: số SV theo mức, GPA danh nghĩa (trước) và TCI (sau), có tooltip."""
    dem = pd.concat([
        sv["Mức theo GPA danh nghĩa"].value_counts().rename_axis("Mức").reset_index(name="Số SV").assign(Loại="GPA danh nghĩa (trước)"),
        sv["Mức theo TCI"].value_counts().rename_axis("Mức").reset_index(name="Số SV").assign(Loại="TCI (sau)")])
    return (alt.Chart(dem).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(x=alt.X("Mức:N", sort=ch3.THU_TU_MUC, title=None),
                    xOffset=alt.XOffset("Loại:N", sort=["GPA danh nghĩa (trước)", "TCI (sau)"]),
                    y=alt.Y("Số SV:Q"),
                    color=alt.Color("Loại:N", scale=alt.Scale(range=[MAU_TRUOC, MAU_SAU]),
                                    legend=alt.Legend(orient="top", title=None)),
                    tooltip=["Mức", "Loại", alt.Tooltip("Số SV:Q", format=",")])
            .properties(height=320))


def bieu_do_phan_phoi(sv: pd.DataFrame) -> alt.Chart:
    """Đường phân phối GPA danh nghĩa và TCI theo khoảng 0,1, có tooltip."""
    dai = pd.concat([pd.DataFrame({"Giá trị": sv["GPA thang 4 danh nghĩa"], "Loại": "GPA danh nghĩa (trước)"}),
                     pd.DataFrame({"Giá trị": sv["TCI"], "Loại": "TCI (sau)"})]).dropna()
    dai["Khoảng"] = (dai["Giá trị"] // 0.1 * 0.1).round(1)
    dem = dai.groupby(["Loại", "Khoảng"]).size().reset_index(name="Số SV")
    return (alt.Chart(dem).mark_line(strokeWidth=2, interpolate="step-after")
            .encode(x=alt.X("Khoảng:Q", title="Thang 4"), y="Số SV:Q",
                    color=alt.Color("Loại:N", scale=alt.Scale(range=[MAU_TRUOC, MAU_SAU]),
                                    legend=alt.Legend(orient="top", title=None)),
                    tooltip=["Loại", alt.Tooltip("Khoảng:Q", format=".1f"), "Số SV"])
            .properties(height=280))


def trang_tong_quan(kq: dict, vai_tro: str) -> None:
    """Tab tổng quan: chỉ số chính, biểu đồ Trước/Sau, ma trận chuyển mức."""
    sv, lop = kq["sv"], kq.get("lop", pd.DataFrame())
    c = st.columns(4)
    c[0].metric("Sinh viên được phân loại", f"{len(sv):,}")
    if len(lop):
        c[1].metric("Lớp bất thường (GP1)", f"{int(lop['anomaly_type'].isin(ch1.NHAN_BAT_THUONG).sum()):,}")
    if "hieu_chinh" in kq:
        c[2].metric("Lớp được hiệu chỉnh (GP2)", f"{int(kq['hieu_chinh'].iloc[:, -1].ne(0).sum()):,}")
    c[3].metric("SV đổi mức (GP3)", f"{int(sv['Thay đổi mức'].ne('Giữ nguyên').sum()):,}")

    st.subheader("Số sinh viên theo mức năng lực – trước và sau hiệu chỉnh")
    st.altair_chart(bieu_do_muc(sv), width="stretch")
    st.subheader("Phân phối GPA danh nghĩa và TCI")
    st.altair_chart(bieu_do_phan_phoi(sv), width="stretch")
    st.caption("Ngưỡng mức: Advanced ≥ 3,60 · Proficient 3,20–<3,60 · Intermediate 2,50–<3,20 · At-Risk < 2,50")

    st.subheader("Ma trận chuyển mức (hàng: theo GPA danh nghĩa · cột: theo TCI)")
    mt = (pd.crosstab(sv["Mức theo GPA danh nghĩa"], sv["Mức theo TCI"])
          .reindex(index=ch3.THU_TU_MUC, columns=ch3.THU_TU_MUC, fill_value=0))
    if vai_tro == CONG_KHAI:
        mt = mt.map(an_nho)
        st.caption("Chế độ công khai: ô dưới 5 sinh viên hiện \"<5\".")
    st.dataframe(mt, width="stretch")


def trang_gp1(kq: dict, vai_tro: str) -> None:
    """Tab Giải pháp 1: bảng xếp hạng lớp nghi vấn (công khai: chỉ lớp ≥ 5 SV, chỉ lớp bất thường)."""
    lop = kq["lop"]
    dem = lop["anomaly_type"].value_counts().rename_axis("Nhãn").reset_index(name="Số lớp")
    dem["Ý nghĩa"] = dem["Nhãn"].map(ch1.Y_NGHIA_NHAN)
    st.dataframe(dem, hide_index=True, width="stretch")
    nhan = st.multiselect("Lọc theo nhãn", list(ch1.Y_NGHIA_NHAN), default=ch1.NHAN_BAT_THUONG)
    bang = lop[lop["anomaly_type"].isin(nhan)]
    if vai_tro == CONG_KHAI:
        bang = bang[bang["n_sv"] >= NGUONG]
    cot = {"rank": "Hạng", "class_id": "Mã lớp", "course": "Mã môn", "year": "Năm học", "sem": "HK",
           "n_sv": "Số SV", "anomaly_score": "Anomaly Score", "anomaly_type": "Nhãn", "severity": "Mức độ",
           "explanation": "Giải thích"}
    st.dataframe(bang[list(cot)].rename(columns=cot), hide_index=True, width="stretch")


def trang_gp2(kq: dict) -> None:
    """Tab Giải pháp 2: mức hiệu chỉnh của từng lớp (chỉ lớp có hiệu chỉnh)."""
    hc = kq["hieu_chinh"]
    cot_dc = hc.columns[-1]  # "Số điểm bị trừ (âm = được cộng)"
    sua = hc[hc[cot_dc].ne(0)].copy()
    st.caption("Chỉ lớp vừa lệch so với mốc vừa có bằng chứng do cách chấm mới được hiệu chỉnh: "
               "Điểm mới = Điểm − (1 − α) × Δ.")
    sua["Điều chỉnh cho cả lớp"] = -sua[cot_dc]
    bd = (alt.Chart(sua).mark_bar(cornerRadiusEnd=4)
          .encode(y=alt.Y("Mã lớp HP:N", sort="x", title=None, axis=alt.Axis(labelFontSize=8)),
                  x=alt.X("Điều chỉnh cho cả lớp:Q", title="Điểm được cộng (+) / bị trừ (−)"),
                  color=alt.condition("datum['Điều chỉnh cho cả lớp'] > 0", alt.value(MAU_TRUOC), alt.value(MAU_SAU)),
                  tooltip=["Mã lớp HP", "Mã môn", "Năm học", "Nhãn GP1", alt.Tooltip("Điều chỉnh cho cả lớp:Q", format="+.2f"),
                           alt.Tooltip("α:Q", format=".2f")])
          .properties(height=max(300, 9 * len(sua))))
    st.altair_chart(bd, width="stretch")
    st.dataframe(sua.drop(columns=["Điều chỉnh cho cả lớp"]), hide_index=True, width="stretch")


def trang_tra_cuu(kq: dict) -> None:
    """Tab tra cứu sinh viên (chỉ nhà trường): TCI, mức, lời giải thích và từng môn."""
    sv, mon = kq["sv"], kq.get("mon", pd.DataFrame())
    ma = st.text_input("Mã SV", placeholder="Ví dụ: S00001").strip().upper()
    if ma:
        dong = sv[sv["Mã SV"] == ma]
        if dong.empty:
            st.warning("Không tìm thấy mã SV này.")
        else:
            r = dong.iloc[0]
            c = st.columns(4)
            c[0].metric("GPA thang 4 danh nghĩa", f"{r['GPA thang 4 danh nghĩa']:.2f}", r["Mức theo GPA danh nghĩa"],
                        delta_color="off")
            c[1].metric("TCI", f"{r['TCI']:.2f}", f"{r['TCI − GPA']:+.2f}")
            c[2].metric("Mức theo TCI", r["Mức theo TCI"], r["Thay đổi mức"], delta_color="off")
            c[3].metric("Độ tin cậy", r["Độ tin cậy"], f"{int(r['Số môn'])} môn", delta_color="off")
            st.info(r["Giải thích"])
            if len(mon):
                st.dataframe(mon[mon["student"] == ma].drop(columns=["student"]), hide_index=True,
                             width="stretch")
    st.download_button("Tải danh sách phân loại toàn trường (CSV)", sv.to_csv(index=False).encode("utf-8-sig"),
                       "phan_loai_sinh_vien.csv", "text/csv")


def trang_chay_moi() -> None:
    """Tab chạy với file điểm mới (chỉ nhà trường): tải Du_lieu.csv → chạy GP1–GP3 → tải kết quả.

    Vì sao cần: đề yêu cầu hệ thống nhận dữ liệu điểm và trả về kết quả phân loại.
    File chỉ xử lý trên máy chạy dashboard, không gửi đi đâu.
    """
    tep = st.file_uploader("File điểm cùng cấu trúc Du_lieu.csv (19 cột)", type="csv")
    if tep is None or not st.button("Chạy phân tích"):
        return
    from eda.load import LoiDuLieu, doc_du_lieu_diem
    from gp1.du_lieu import chuan_bi
    from gp3.quy_trinh import chay_gp3

    with st.spinner("Đang chạy Giải pháp 1 → 3 (khoảng 30 giây)..."), tempfile.TemporaryDirectory() as tam:
        p = Path(tam) / "Du_lieu.csv"
        p.write_bytes(tep.getvalue())
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                kq = chay_gp3(chuan_bi(doc_du_lieu_diem(p)[0]))
        except LoiDuLieu as loi:
            st.error(f"File không đúng cấu trúc: {loi}")
            return
    sv = kq["phan_loai"]
    st.success(f"Đã phân loại {len(sv):,} SV; {int(sv['doi_muc'].ne('Giữ nguyên').sum()):,} SV đổi mức.")
    st.dataframe(sv["muc_sau"].value_counts().reindex(ch3.THU_TU_MUC, fill_value=0).rename("Số SV theo TCI"))
    st.download_button("Tải kết quả phân loại (CSV)", sv.to_csv(index=False).encode("utf-8-sig"),
                       "phan_loai_moi.csv", "text/csv")


def chon_vai_tro() -> str:
    """Thanh bên: chọn vai trò; vai trò nhà trường cần mật khẩu từ biến môi trường."""
    st.sidebar.header("Vai trò")
    vai_tro = st.sidebar.radio("Xem với vai trò", [CONG_KHAI, NHA_TRUONG], label_visibility="collapsed")
    if vai_tro == CONG_KHAI:
        return CONG_KHAI
    mat_khau = os.environ.get("FIT_MAT_KHAU_NHA_TRUONG", "")
    if not mat_khau:
        st.sidebar.warning("Chưa đặt biến môi trường FIT_MAT_KHAU_NHA_TRUONG nên chưa mở được vai trò nhà trường.")
        return CONG_KHAI
    nhap = st.sidebar.text_input("Mật khẩu nhà trường", type="password")
    if nhap and hmac.compare_digest(nhap, mat_khau):
        st.sidebar.success("Đã mở vai trò nhà trường.")
        return NHA_TRUONG
    if nhap:
        st.sidebar.error("Sai mật khẩu.")
    return CONG_KHAI


def main() -> None:
    """Dựng trang: chọn vai trò, đọc kết quả, hiện các tab theo quyền."""
    st.set_page_config(page_title="TCI Dashboard", layout="wide")
    st.title("Liêm chính học thuật & năng lực thực chất")
    vai_tro = chon_vai_tro()
    st.sidebar.caption(f"Đang xem: **{vai_tro}**")
    kq = doc_ket_qua(str(KET_QUA))
    if "sv" not in kq:
        st.error(f"Chưa có kết quả trong {KET_QUA}. Hãy chạy: .venv/Scripts/python.exe -X utf8 03_ma-nguon/run_gp3.py")
        return
    ten_tab = ["Tổng quan", "Lớp bất thường (GP1)", "Hiệu chỉnh điểm (GP2)"]
    if vai_tro == NHA_TRUONG:
        ten_tab += ["Tra cứu sinh viên", "Chạy với file điểm mới"]
    tabs = st.tabs(ten_tab)
    with tabs[0]:
        trang_tong_quan(kq, vai_tro)
    with tabs[1]:
        trang_gp1(kq, vai_tro) if "lop" in kq else st.info("Thiếu kết quả GP1.")
    with tabs[2]:
        trang_gp2(kq) if "hieu_chinh" in kq else st.info("Thiếu kết quả GP2.")
    if vai_tro == NHA_TRUONG:
        with tabs[3]:
            trang_tra_cuu(kq)
        with tabs[4]:
            trang_chay_moi()


main()
