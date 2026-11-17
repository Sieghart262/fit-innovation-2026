"""Dashboard phân tích điểm và năng lực thực chất của sinh viên (Streamlit).

Phân quyền (quyết định của đội):
    - Công khai: chỉ số liệu tổng hợp; ô nào dưới 5 SV hiện "<5"; không có bảng từng lớp
      (từ mã lớp có thể suy ra giảng viên) và không tra cứu từng SV.
    - Nhà trường: xem hết, tra cứu từng SV, tải danh sách phân loại, phân tích file điểm mới.
      Cần mật khẩu đặt trong biến môi trường FIT_MAT_KHAU_NHA_TRUONG (không ghi vào code).

Dữ liệu: đọc kết quả do run_gp3.py ghi ra (mặc định 01_du-lieu/ket-qua/). Đặt biến môi trường
FIT_KET_QUA để trỏ tới thư mục khác (ví dụ kết quả từ DỮ LIỆU GIẢ khi demo công khai).

Chạy (từ thư mục gốc dự án, để Streamlit đọc được .streamlit/config.toml):
    .venv/Scripts/streamlit.exe run 03_ma-nguon/dashboard/app.py

Kiểu dáng (màu, thẻ số liệu, huy hiệu, tên tiếng Việt của nhãn) nằm ở giao_dien.py.
"""

from __future__ import annotations

import hmac
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

THU_MUC_MA = Path(__file__).resolve().parents[1]
for _p in (THU_MUC_MA, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bao_cao  # noqa: E402
import giao_dien as gd  # noqa: E402
import kho_ket_qua as kho  # noqa: E402
from eda import config as cf  # noqa: E402
from eda.load import LoiDuLieu  # noqa: E402
from gp1 import cau_hinh as ch1  # noqa: E402
from gp3 import cau_hinh as ch3  # noqa: E402

KET_QUA = Path(os.environ.get("FIT_KET_QUA", kho.THU_MUC_KET_QUA))
LICH_SU = Path(os.environ.get("FIT_LICH_SU", kho.thu_muc_lich_su(KET_QUA)))
NGUONG = cf.NGUONG_NHOM_TOI_THIEU
CONG_KHAI, NHA_TRUONG = "Công khai", "Nhà trường"
COT_DIEU_CHINH = "Số điểm bị trừ (âm = được cộng)"  # tên cột trong hieu_chinh_theo_lop.csv (gp2/xuat.py)
TRUOC, SAU = "Trước hiệu chỉnh (GPA danh nghĩa)", "Sau hiệu chỉnh (TCI)"
RIENG, GOP = "Phân tích riêng file này", "Gộp thêm vào dữ liệu đang hiển thị"
THU_TU_NHAN = [ch1.HIGH, ch1.STEEP, ch1.DIST, ch1.REVIEW, ch1.NORMAL, ch1.IT_DU_LIEU, ch1.CHUA_DU, ch1.KHONG_MOC]


# ---------------------------------------------------------------------------
# Đọc kết quả
# ---------------------------------------------------------------------------
def file_ket_qua(thu_muc: Path) -> dict[str, Path]:
    """Đường dẫn 4 file kết quả mà dashboard đọc."""
    return {"lop": thu_muc / "gp1" / "chi_so_chi_tiet.csv", "hieu_chinh": thu_muc / "gp2" / "hieu_chinh_theo_lop.csv",
            "sv": thu_muc / "gp3" / "phan_loai_sinh_vien.csv", "mon": thu_muc / "gp3" / "mon_cua_sinh_vien.csv"}


def dau_thoi_gian(thu_muc: Path) -> tuple:
    """Thời điểm sửa cuối của các file kết quả – đổi khi có kết quả mới (chạy lệnh, tải file lên, reset)."""
    cac_file = list(file_ket_qua(thu_muc).values()) + [thu_muc / kho.TEN_THONG_TIN]
    return tuple(p.stat().st_mtime_ns if p.exists() else 0 for p in cac_file)


@st.cache_data(show_spinner=False)
def doc_ket_qua(thu_muc: str, dau: tuple) -> dict:
    """Đọc các file kết quả của 3 giải pháp (CSV UTF-8 có BOM).

    Tham số:
        thu_muc: thư mục gốc kết quả (có gp1/, gp2/, gp3/).
        dau: kết quả của dau_thoi_gian() – chỉ để cache biết khi nào file đã đổi.
    Trả về:
        dict bảng; thiếu file nào thì bỏ qua file đó.
    Vì sao cần: dashboard chỉ đọc kết quả đã tính sẵn nên mở nhanh; cache để không đọc lại mỗi lần
    bấm, nhưng tự đọc lại khi kết quả được tạo mới (không phải tắt mở dashboard).
    """
    return {k: pd.read_csv(p, encoding="utf-8-sig") for k, p in file_ket_qua(Path(thu_muc)).items() if p.exists()}


def an_nho(so_nguoi: int) -> str:
    """Hiện số SV ở chế độ công khai: nhóm dưới 5 người hiện "<5"."""
    return "<5" if 0 < so_nguoi < NGUONG else gd.so(so_nguoi)


def cot_dieu_chinh(hc: pd.DataFrame) -> str:
    """Tên cột "số điểm bị trừ" trong bảng hiệu chỉnh theo lớp."""
    return COT_DIEU_CHINH if COT_DIEU_CHINH in hc.columns else hc.columns[-1]


# ---------------------------------------------------------------------------
# Biểu đồ
# ---------------------------------------------------------------------------
def bieu_do_muc(sv: pd.DataFrame) -> alt.Chart:
    """Cột ghép: số SV ở mỗi mức năng lực, trước và sau hiệu chỉnh; có số trên đầu cột và tooltip."""
    dem = pd.concat([
        sv["Mức theo GPA danh nghĩa"].value_counts().rename_axis("Mức").reset_index(name="Số SV").assign(Loại=TRUOC),
        sv["Mức theo TCI"].value_counts().rename_axis("Mức").reset_index(name="Số SV").assign(Loại=SAU)])
    dem = dem[dem["Mức"].isin(ch3.THU_TU_MUC)]  # bỏ nhóm "Chưa đủ dữ liệu" khỏi biểu đồ mức
    dem["Số sinh viên"] = dem["Số SV"].map(gd.so)
    dem["Ý nghĩa"] = dem["Mức"].map(lambda m: f"{gd.MUC_VIET[m][0]} ({gd.MUC_VIET[m][1]})")
    goc = alt.Chart(dem).encode(
        x=alt.X("Mức:N", sort=ch3.THU_TU_MUC, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=13)),
        xOffset=alt.XOffset("Loại:N", sort=[TRUOC, SAU]),
        y=alt.Y("Số SV:Q", title="Số sinh viên"))
    cot = goc.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        color=alt.Color("Loại:N", sort=[TRUOC, SAU], legend=alt.Legend(orient="top", title=None),
                        scale=alt.Scale(domain=[TRUOC, SAU], range=[gd.MAU_TRUOC, gd.MAU_SAU])),
        tooltip=["Mức", "Ý nghĩa", "Loại", "Số sinh viên"])
    chu = goc.mark_text(dy=-7, fontSize=11, color=gd.MUC_PHU).encode(text="Số sinh viên:N")
    return gd.kieu_bieu_do((cot + chu).properties(height=330))


def bieu_do_phan_phoi(sv: pd.DataFrame) -> alt.Chart:
    """Đường phân phối GPA danh nghĩa và TCI theo khoảng 0,1 điểm, có tooltip."""
    dai = pd.concat([pd.DataFrame({"Giá trị": sv["GPA thang 4 danh nghĩa"], "Loại": TRUOC}),
                     pd.DataFrame({"Giá trị": sv["TCI"], "Loại": SAU})]).dropna()
    # floor(x·10 + ε)/10 thay cho x // 0.1: phép chia số thực xếp 3,0 vào khoảng 2,9 và 3,6 vào khoảng 3,5
    dai["Khoảng"] = np.floor(dai["Giá trị"] * 10 + 1e-9) / 10
    dem = dai.groupby(["Loại", "Khoảng"]).size().reset_index(name="Số SV")
    dem["Khoảng điểm"] = dem["Khoảng"].map(lambda k: f"{gd.so(k, 1)} – {gd.so(k + 0.1, 1)}")
    bd = (alt.Chart(dem).mark_line(strokeWidth=2, interpolate="step-after")
          .encode(x=alt.X("Khoảng:Q", title="Điểm thang 4"), y=alt.Y("Số SV:Q", title="Số sinh viên"),
                  color=alt.Color("Loại:N", sort=[TRUOC, SAU], legend=alt.Legend(orient="top", title=None),
                                  scale=alt.Scale(domain=[TRUOC, SAU], range=[gd.MAU_TRUOC, gd.MAU_SAU])),
                  tooltip=["Loại", "Khoảng điểm", "Số SV"]))
    nguong = (alt.Chart(pd.DataFrame({"x": [n for n, _ in ch3.MUC_NANG_LUC[:-1]]}))
              .mark_rule(strokeDash=[4, 4], color="#c3c2b7").encode(x="x:Q"))
    return gd.kieu_bieu_do((nguong + bd).properties(height=280))


def bieu_do_nhan(dem: pd.DataFrame) -> alt.Chart:
    """Thanh ngang: số lớp theo từng kết luận của Giải pháp 1 (một màu, có số ở cuối thanh)."""
    goc = alt.Chart(dem).encode(
        y=alt.Y("Kết luận:N", sort=list(dem["Kết luận"]), title=None, axis=alt.Axis(labelLimit=420, labelFontSize=13)),
        x=alt.X("Số lớp:Q", title="Số lớp học phần"))
    thanh = goc.mark_bar(cornerRadiusEnd=4, color=gd.MAU_CHINH, height=20).encode(tooltip=["Kết luận", "Số lớp", "Ý nghĩa"])
    chu = goc.mark_text(align="left", dx=6, fontSize=12, color=gd.MUC_PHU).encode(text="Số lớp:Q")
    return gd.kieu_bieu_do((thanh + chu).properties(height=34 * len(dem) + 30))


# ---------------------------------------------------------------------------
# Các trang
# ---------------------------------------------------------------------------
def trang_tong_quan(kq: dict, vai_tro: str, khoa: str = "") -> None:
    """Trang tổng quan: câu tóm tắt, 4 con số chính, biểu đồ Trước/Sau, SV đổi mức."""
    sv, lop = kq["sv"], kq.get("lop", pd.DataFrame())
    co_tci = sv["TCI"].notna()
    doi = sv["Thay đổi mức"].ne("Giữ nguyên")
    len_muc, xuong_muc = int(sv["Thay đổi mức"].eq("Lên mức").sum()), int(sv["Thay đổi mức"].eq("Xuống mức").sum())
    chua_du = int((~co_tci).sum())
    gd.tom_tat(f"Trong <b>{gd.so(co_tci.sum())}</b> sinh viên được xếp mức, có <b>{gd.so(doi.sum())} sinh viên đổi mức</b> "
               f"sau khi hiệu chỉnh điểm: {gd.so(len_muc)} lên mức, {gd.so(xuong_muc)} xuống mức."
               + (f" Ngoài ra {gd.so(chua_du)} sinh viên chưa đủ dữ liệu để xếp mức." if chua_du else ""))

    c = st.columns(4)
    gd.the_so(c[0], "Sinh viên được xếp mức", gd.so(co_tci.sum()), "theo điểm đã hiệu chỉnh")
    if len(lop):
        bat = int(lop["anomaly_type"].isin(ch1.NHAN_BAT_THUONG).sum())
        gd.the_so(c[1], "Lớp có dấu hiệu bất thường", gd.so(bat), f"trên {gd.so(len(lop))} lớp học phần")
    if "hieu_chinh" in kq:
        hc = kq["hieu_chinh"]
        gd.the_so(c[2], "Lớp được hiệu chỉnh điểm", gd.so(int(hc[cot_dieu_chinh(hc)].ne(0).sum())),
                  "có bằng chứng do cách chấm")
    gd.the_so(c[3], "Sinh viên đổi mức", gd.so(doi.sum()), f"{gd.so(len_muc)} lên · {gd.so(xuong_muc)} xuống")

    trai, phai = st.columns([3, 2], gap="large")
    with trai:
        st.subheader("Số sinh viên ở mỗi mức năng lực")
        st.altair_chart(bieu_do_muc(sv), width="stretch", key=f"{khoa}bd_muc")
    with phai:
        st.subheader("Sinh viên đổi mức như thế nào")
        mt = (pd.crosstab(sv["Mức theo GPA danh nghĩa"], sv["Mức theo TCI"])
              .reindex(index=ch3.THU_TU_MUC, columns=ch3.THU_TU_MUC, fill_value=0))
        chuyen = [(a, b, int(mt.loc[a, b])) for a in ch3.THU_TU_MUC for b in ch3.THU_TU_MUC if a != b and mt.loc[a, b] > 0]
        if chuyen:
            bang = pd.DataFrame(sorted(chuyen, key=lambda x: -x[2]), columns=["Từ mức", "Sang mức", "Số sinh viên"])
            bang["Số sinh viên"] = bang["Số sinh viên"].map(an_nho if vai_tro == CONG_KHAI else gd.so)
            st.dataframe(bang, hide_index=True, width="stretch", key=f"{khoa}bang_doi_muc")
        else:
            st.write("Không có sinh viên nào đổi mức.")
        if vai_tro == CONG_KHAI:
            gd.ghi_chu("Chế độ công khai: nhóm dưới 5 sinh viên hiện \"<5\".")
        with st.expander("Xem bảng đầy đủ (hàng: mức trước · cột: mức sau)"):
            st.dataframe(mt.map(an_nho) if vai_tro == CONG_KHAI else mt, width="stretch", key=f"{khoa}ma_tran")

    st.subheader("Phân phối điểm trước và sau hiệu chỉnh")
    st.altair_chart(bieu_do_phan_phoi(sv), width="stretch", key=f"{khoa}bd_phan_phoi")
    gd.ghi_chu("Đường đứt là ngưỡng giữa các mức: 2,50 · 3,20 · 3,60. Lượt vắng thi (điểm 0) không được tính; "
               "sinh viên không có môn nào có điểm hợp lệ được ghi \"Chưa đủ dữ liệu\" và không nằm trong biểu đồ.")

    with st.expander("Cách đọc trang này"):
        st.markdown(
            "- **GPA danh nghĩa** là điểm trung bình thang 4 tính từ điểm gốc.\n"
            "- **TCI** (chỉ số năng lực thực chất) tính y hệt, nhưng từ điểm đã hiệu chỉnh: lớp chấm dễ bị trừ bớt, "
            "lớp chấm khắt khe được cộng thêm.\n"
            "- Một lớp chỉ bị sửa điểm khi vừa **lệch so với các lớp tương đương**, vừa có **bằng chứng do cách chấm**. "
            "Lớp có sinh viên giỏi thật thì không bị sửa.\n"
            "- Bốn mức năng lực: " + " · ".join(f"**{m}** ({gd.MUC_VIET[m][0].lower()}, {gd.MUC_VIET[m][1]})"
                                                for m in ch3.THU_TU_MUC) + ".")


def trang_lop(kq: dict, vai_tro: str, khoa: str = "") -> None:
    """Trang lớp học phần: số lớp theo kết luận; bảng từng lớp và lý do chỉ dành cho vai trò nhà trường.

    Vì sao ẩn bảng từng lớp ở chế độ công khai: từ mã lớp có thể suy ra giảng viên, trong khi
    điều kiện dữ liệu yêu cầu không xác định danh tính sinh viên hay giảng viên.
    Tham số khoa: tiền tố cho tên các ô lọc, để trang này hiện được hai lần trên cùng màn hình
    (dashboard chính và phần xem trước một mục lịch sử) mà không bị trùng.
    """
    lop = kq["lop"]
    so_lop = lop["anomaly_type"].value_counts()
    # 3 nhãn bất thường của đề LUÔN hiện, kể cả khi 0 lớp, để người xem biết hệ thống có kiểm tra đủ cả ba.
    dem = pd.DataFrame({"Mã": [n for n in THU_TU_NHAN if n in ch1.NHAN_BAT_THUONG or so_lop.get(n, 0) > 0]})
    dem["Kết luận"] = dem["Mã"].map(gd.TEN_NHAN)
    dem["Số lớp"] = dem["Mã"].map(so_lop).fillna(0).astype(int)
    dem["Ý nghĩa"] = dem["Mã"].map(gd.GIAI_THICH_NHAN)
    bat = int(lop["anomaly_type"].isin(ch1.NHAN_BAT_THUONG).sum())
    xem_xet = int(so_lop.get(ch1.REVIEW, 0))
    gd.tom_tat(f"<b>{gd.so(bat)}</b> trên {gd.so(len(lop))} lớp học phần có dấu hiệu bất thường. "
               f"Thêm {gd.so(xem_xet)} lớp có điểm lệch nhưng chưa có bằng chứng do cách chấm, chỉ cần xem xét thêm.")

    trai, phai = st.columns([3, 2], gap="large")
    with trai:
        st.subheader("Số lớp theo kết luận")
        st.altair_chart(bieu_do_nhan(dem), width="stretch", key=f"{khoa}bd_nhan")
    with phai:
        st.subheader("Ý nghĩa của từng kết luận")
        for _, d in dem.iterrows():
            st.markdown(f"**{d['Kết luận']}** · {d['Ý nghĩa']}")

    if vai_tro == CONG_KHAI:
        gd.ghi_chu("Chế độ công khai chỉ hiện số liệu tổng hợp. Danh sách từng lớp chỉ vai trò Nhà trường xem được.")
        return

    st.subheader("Danh sách lớp")
    c = st.columns([3, 2, 2])
    mac_dinh = [gd.TEN_NHAN[n] for n in ch1.NHAN_BAT_THUONG]
    chon = c[0].multiselect("Kết luận", list(dem["Kết luận"]), default=mac_dinh, key=f"{khoa}ket_luan")
    nam = c[1].selectbox("Năm học", ["Tất cả"] + sorted(lop["year"].dropna().unique()), key=f"{khoa}nam")
    mon = c[2].selectbox("Mã môn", ["Tất cả"] + sorted(lop["course"].dropna().unique()), key=f"{khoa}mon")
    bang = lop.assign(ket_luan=lop["anomaly_type"].map(gd.TEN_NHAN))
    bang = bang[bang["ket_luan"].isin(chon)]
    if nam != "Tất cả":
        bang = bang[bang["year"] == nam]
    if mon != "Tất cả":
        bang = bang[bang["course"] == mon]
    bang = bang.sort_values("anomaly_score", ascending=False, na_position="last")
    cot = {"class_id": "Mã lớp", "course": "Mã môn", "year": "Năm học", "sem": "Học kỳ", "n_sv": "Số SV",
           "ket_luan": "Kết luận", "anomaly_score": "Mức độ bất thường", "mean": "Điểm TB lớp",
           "ref_mean": "Điểm TB các lớp tương đương"}
    st.dataframe(
        bang[list(cot)].rename(columns=cot), hide_index=True, width="stretch", height=380, key=f"{khoa}ds_lop",
        column_config={
            "Mức độ bất thường": st.column_config.ProgressColumn(
                "Mức độ bất thường", min_value=0.0, max_value=1.0, format="%.2f",
                help="Anomaly Score từ 0 đến 1: càng cao càng đáng ngờ."),
            "Điểm TB lớp": st.column_config.NumberColumn(format="%.2f"),
            "Điểm TB các lớp tương đương": st.column_config.NumberColumn(format="%.2f"),
            "Học kỳ": st.column_config.NumberColumn(format="%d"),
        })
    gd.ghi_chu(f"Đang hiện {gd.so(len(bang))} lớp. \"Lớp tương đương\" là các lớp cùng môn (hoặc cùng nhóm môn), "
               "cùng cơ cấu điểm, cách nhau không quá 1 năm học.")

    if len(bang):
        st.subheader("Vì sao lớp này có kết luận như vậy?")
        ma = st.selectbox("Chọn một lớp trong danh sách trên", list(bang["class_id"]), key=f"{khoa}chon_lop")
        d = bang[bang["class_id"] == ma].iloc[0]
        st.markdown(f"**Lớp {d['class_id']}** · môn {d['course']} · {d['year']}, học kỳ {int(d['sem'])} · "
                    f"{int(d['n_sv'])} sinh viên · kết luận: **{d['ket_luan']}**")
        cac_y = []
        for y in str(d["explanation"]).split("; "):  # ghép lại phần "z=…, q=…" thuộc về ý đứng trước
            if cac_y and y.startswith("z="):
                cac_y[-1] += "; " + y
            else:
                cac_y.append(y)
        gd.danh_sach_ly_do(cac_y)


def trang_hieu_chinh(kq: dict, vai_tro: str, khoa: str = "") -> None:
    """Trang hiệu chỉnh điểm: tóm tắt; biểu đồ và bảng từng lớp chỉ dành cho vai trò nhà trường."""
    hc = kq["hieu_chinh"]
    cot_dc = cot_dieu_chinh(hc)
    sua = hc[hc[cot_dc].ne(0)].copy()
    tru, cong = int((sua[cot_dc] > 0).sum()), int((sua[cot_dc] < 0).sum())
    gd.tom_tat(f"<b>{gd.so(len(sua))}</b> lớp được hiệu chỉnh điểm: {gd.so(tru)} lớp chấm dễ bị trừ bớt, "
               f"{gd.so(cong)} lớp chấm khắt khe được cộng thêm. Mọi lớp khác giữ nguyên điểm.")
    c = st.columns(3)
    gd.the_so(c[0], "Lớp bị trừ điểm", gd.so(tru), "do chấm dễ")
    gd.the_so(c[1], "Lớp được cộng điểm", gd.so(cong), "do chấm khắt khe")
    gd.the_so(c[2], "Mức hiệu chỉnh trung bình", f"{gd.so(sua[cot_dc].abs().mean(), 2)} điểm" if len(sua) else "–",
              f"nhiều nhất {gd.so(sua[cot_dc].abs().max(), 2)} điểm" if len(sua) else "")

    with st.expander("Điểm được hiệu chỉnh như thế nào?"):
        st.markdown(
            "- Chỉ lớp vừa **lệch so với các lớp tương đương**, vừa có **bằng chứng do cách chấm** mới được hiệu chỉnh.\n"
            "- Mọi sinh viên trong lớp được cộng hoặc trừ **cùng một mức**, nên thứ hạng trong lớp không đổi.\n"
            "- Công thức: `Điểm mới = Điểm cũ − (1 − α) × Δ`. **Δ** là phần điểm lệch do cách chấm; "
            "**α** càng nhỏ khi lớp càng bất thường, tức phần lệch được gỡ càng nhiều.\n"
            "- Mỗi lớp không bị cộng hoặc trừ quá 2 điểm. Sinh viên vắng thi giữ nguyên điểm.")

    if vai_tro == CONG_KHAI:
        gd.ghi_chu("Chế độ công khai chỉ hiện số liệu tổng hợp. Chi tiết từng lớp chỉ vai trò Nhà trường xem được.")
        return
    if sua.empty:
        st.write("Không có lớp nào được hiệu chỉnh.")
        return

    st.subheader("Mức hiệu chỉnh của từng lớp")
    sua["Điều chỉnh"] = -sua[cot_dc]
    sua["Hướng điều chỉnh"] = np.where(sua["Điều chỉnh"] > 0, "Cộng điểm", "Trừ điểm")
    sua["Kết luận"] = sua["Nhãn GP1"].map(gd.NHAN_VIET)
    sua["Mức"] = sua["Điều chỉnh"].map(lambda v: f"{'+' if v > 0 else '−'}{gd.so(abs(v), 2)} điểm")
    bd = (alt.Chart(sua).mark_bar(cornerRadiusEnd=3)
          .encode(y=alt.Y("Mã lớp HP:N", sort="x", title=None, axis=alt.Axis(labelFontSize=10)),
                  x=alt.X("Điều chỉnh:Q", title="Điểm cộng thêm (+) hoặc trừ bớt (−) cho cả lớp"),
                  color=alt.Color("Hướng điều chỉnh:N", legend=alt.Legend(orient="top", title=None),
                                  scale=alt.Scale(domain=["Cộng điểm", "Trừ điểm"], range=[gd.MAU_TRUOC, gd.MAU_SAU])),
                  tooltip=["Mã lớp HP", "Mã môn", "Năm học", "Kết luận", "Mức"])
          .properties(height=max(300, 13 * len(sua))))
    st.altair_chart(gd.kieu_bieu_do(bd), width="stretch", key=f"{khoa}bd_hieu_chinh")

    bang = sua.sort_values("Điều chỉnh")[["Mã lớp HP", "Mã môn", "Năm học", "Kết luận", "ĐTB lớp", "ĐTB mốc", "Điều chỉnh"]]
    bang = bang.rename(columns={"Mã lớp HP": "Mã lớp", "ĐTB lớp": "Điểm TB lớp", "ĐTB mốc": "Điểm TB các lớp tương đương",
                                "Điều chỉnh": "Điều chỉnh cho cả lớp"})
    st.dataframe(bang, hide_index=True, width="stretch", key=f"{khoa}bang_hieu_chinh", column_config={
        "Điểm TB lớp": st.column_config.NumberColumn(format="%.2f"),
        "Điểm TB các lớp tương đương": st.column_config.NumberColumn(format="%.2f"),
        "Điều chỉnh cho cả lớp": st.column_config.NumberColumn(format="%+.2f", help="Số điểm cộng (+) hoặc trừ (−)")})
    with st.expander("Bảng chi tiết kỹ thuật (Δ, α)"):
        st.dataframe(sua.drop(columns=["Điều chỉnh", "Hướng điều chỉnh", "Kết luận", "Mức"]), hide_index=True, width="stretch", key=f"{khoa}bang_ky_thuat")


def trang_tra_cuu(kq: dict) -> None:
    """Trang tra cứu sinh viên (chỉ nhà trường): mức năng lực, lý do và điểm từng môn."""
    sv, mon = kq["sv"], kq.get("mon", pd.DataFrame())
    with st.form("tra_cuu"):
        c = st.columns([4, 1], vertical_alignment="bottom")
        ma = c[0].text_input("Mã sinh viên", placeholder="Ví dụ: S00001")
        c[1].form_submit_button("Tra cứu", type="primary", width="stretch")
    ma = ma.strip().upper()
    if ma:
        dong = sv[sv["Mã SV"] == ma]
        if dong.empty:
            st.warning("Không tìm thấy mã sinh viên này. Hãy kiểm tra lại mã.")
        else:
            r = dong.iloc[0]
            st.markdown(f"### Sinh viên {r['Mã SV']} &nbsp; {gd.huy_hieu_muc(r['Mức theo TCI'])}", unsafe_allow_html=True)
            if pd.notna(r["TCI"]):
                c = st.columns(4)
                gd.the_so(c[0], "GPA danh nghĩa (thang 4)", gd.so(r["GPA thang 4 danh nghĩa"], 2), f"mức {r['Mức theo GPA danh nghĩa']}")
                gd.the_so(c[1], "TCI sau hiệu chỉnh", gd.so(r["TCI"], 2),
                          "không đổi" if r["TCI − GPA"] == 0 else f"{'+' if r['TCI − GPA'] > 0 else '−'}{gd.so(abs(r['TCI − GPA']), 2)} so với GPA")
                gd.the_so(c[2], "Thay đổi mức", str(r["Thay đổi mức"]), f"{r['Mức theo GPA danh nghĩa']} → {r['Mức theo TCI']}")
                gd.the_so(c[3], "Độ tin cậy", str(r["Độ tin cậy"]), f"tính trên {int(r['Số môn'])} môn")
            st.subheader("Vì sao sinh viên được xếp mức này?")
            gd.danh_sach_ly_do([y.rstrip(".") for y in str(r["Giải thích"]).split(". ")])
            cua_sv = mon[mon["student"] == ma] if len(mon) else mon
            if len(cua_sv):
                st.subheader("Điểm từng môn")
                bang = pd.DataFrame({
                    "Mã môn": cua_sv["course"], "Lớp": cua_sv["class_id"], "Năm học": cua_sv["year"],
                    "Số TC": cua_sv["credits"], "Điểm gốc": cua_sv["hp_truoc"], "Điểm chữ gốc": cua_sv["chu_truoc"],
                    "Điểm sau hiệu chỉnh": cua_sv["Adjusted_Score"], "Điểm chữ sau": cua_sv["chu_sau"],
                    "Kết luận về lớp": cua_sv["nhan_lop_gp1"].map(gd.NHAN_VIET),
                    "Cần rà soát": np.where(cua_sv["review_flag"].astype(str).isin(["", "nan"]), "", "Có")})
                st.dataframe(bang.sort_values("Năm học"), hide_index=True, width="stretch", column_config={
                    "Số TC": st.column_config.NumberColumn(format="%d"),
                    "Điểm gốc": st.column_config.NumberColumn(format="%.1f"),
                    "Điểm sau hiệu chỉnh": st.column_config.NumberColumn(format="%.2f")})
    st.divider()
    st.download_button("Tải danh sách xếp mức toàn bộ sinh viên (CSV)", sv.to_csv(index=False).encode("utf-8-sig"),
                       "phan_loai_sinh_vien.csv", "text/csv")


def _thoi_gian(tt: dict | None) -> str:
    """Thời điểm phân tích dạng "14:05 ngày 17/11/2026"."""
    if not tt or not tt.get("thoi_gian"):
        return "–"
    return datetime.fromisoformat(tt["thoi_gian"]).strftime("%H:%M ngày %d/%m/%Y")


def khung_reset(co_du_lieu: bool) -> None:
    """Nút Reset có bước xác nhận: cất kết quả đang dùng vào lịch sử rồi làm trống dashboard."""
    st.subheader("Bắt đầu lại từ đầu")
    if not co_du_lieu:
        gd.ghi_chu("Dashboard đang trống. Tải file điểm lên ở bên dưới để tạo dashboard mới.")
        return
    gd.ghi_chu("Reset sẽ làm trống dashboard cho mọi người xem. Kết quả hiện tại không bị mất: "
               "nó được cất vào mục Lịch sử phân tích, mở lại hoặc tải về được.")
    if not st.session_state.get("hoi_reset"):
        if st.button("Reset dashboard"):
            st.session_state["hoi_reset"] = True
            st.rerun()
        return
    st.warning("Bạn chắc chắn muốn reset? Dashboard sẽ trống cho tới khi có file điểm mới được phân tích.")
    c = st.columns([1, 1, 4])
    if c[0].button("Đồng ý reset", type="primary"):
        da_luu = kho.reset(KET_QUA, LICH_SU)
        st.session_state["hoi_reset"] = False
        st.session_state["thong_bao"] = ("Đã reset. Dashboard đang trống." +
                                         (" Kết quả cũ đã được cất vào Lịch sử phân tích." if da_luu else ""))
        st.rerun()
    if c[1].button("Hủy"):
        st.session_state["hoi_reset"] = False
        st.rerun()


def trang_du_lieu_moi(co_du_lieu: bool) -> None:
    """Trang phân tích dữ liệu mới (chỉ nhà trường): reset, tải file điểm, phân tích riêng hoặc gộp.

    Kết quả mới thay cho dashboard của mọi người xem và được lưu vào lịch sử (quyết định của đội).
    Vì sao cần: đề yêu cầu hệ thống nhận dữ liệu điểm và trả về kết quả phân loại; nhà trường
    muốn phân tích nhóm dữ liệu khác mà vẫn giữ được các lần phân tích trước.
    File chỉ xử lý trên máy đang chạy dashboard, không gửi đi đâu.
    """
    tt = kho.doc_thong_tin(KET_QUA)
    if co_du_lieu:
        ten = tt["ten"] if tt else "Kết quả phân tích trước đây"
        gd.tom_tat(f"Dashboard đang hiển thị: <b>{gd.html.escape(ten)}</b> (phân tích lúc {_thoi_gian(tt)}).")
    else:
        gd.tom_tat("Dashboard đang <b>trống</b>. Tải file điểm lên để tạo dashboard mới.")
    khung_reset(co_du_lieu)

    st.subheader("Phân tích file điểm mới")
    c = st.columns(3, gap="large")
    c[0].markdown("**Bước 1 · Chuẩn bị file**\n\nFile CSV có đủ 19 cột, cùng tên cột như file điểm gốc. "
                  "Tải file mẫu bên dưới để xem tên cột.")
    c[1].markdown("**Bước 2 · Tải file lên và chọn cách phân tích**\n\nKéo thả file vào ô bên dưới, hoặc bấm *Upload*.")
    c[2].markdown("**Bước 3 · Bấm Phân tích**\n\nChờ khoảng 30 giây. Dashboard tự chuyển sang kết quả mới.")
    st.download_button("Tải file mẫu (chỉ có dòng tên cột)", (",".join(cf.COT_BAT_BUOC) + "\n").encode("utf-8-sig"),
                       "mau_du_lieu_diem.csv", "text/csv")
    tep = st.file_uploader("File điểm (CSV)", type="csv")
    co_the_gop = co_du_lieu and kho.file_du_lieu(KET_QUA) is not None
    lua_chon = [RIENG, GOP] if co_the_gop else [RIENG]
    cach = st.radio("Cách phân tích", lua_chon, captions=[
        "Dashboard chỉ dùng dữ liệu trong file này. Kết quả đang hiển thị được cất vào lịch sử.",
        "Ghép file này với dữ liệu đang hiển thị rồi phân tích lại toàn bộ. Nếu cùng một sinh viên trong "
        "cùng một lớp có ở cả hai, dùng dòng của file mới."][:len(lua_chon)])
    if co_du_lieu and not co_the_gop:
        gd.ghi_chu("Không gộp được vì không tìm thấy file điểm của dữ liệu đang hiển thị.")
    gd.ghi_chu("Sau khi phân tích, mọi người mở dashboard đều thấy kết quả mới. Chế độ công khai vẫn chỉ có số liệu tổng hợp.")
    if tep is not None and st.button("Phân tích", type="primary"):
        with st.spinner("Đang phân tích (khoảng 30 giây)..."):
            try:
                tt_moi = kho.phan_tich_moi(tep.getvalue(), tep.name, cach == GOP, KET_QUA, LICH_SU)
                loi_gop = (f" Đã gộp {gd.so(tt_moi['so_dong_cu'])} dòng đang có với {gd.so(tt_moi['so_dong_moi'])} dòng mới"
                           f" ({gd.so(tt_moi['so_dong_thay'])} dòng trùng được thay bằng dòng mới)." if "so_dong_cu" in tt_moi else "")
                st.session_state["thong_bao"] = (f"Đã phân tích xong \"{tt_moi['ten']}\": {gd.so(tt_moi['so_sv'])} sinh viên, "
                                                 f"{gd.so(tt_moi['so_lop'])} lớp. Dashboard đã chuyển sang kết quả mới." + loi_gop)
                st.rerun()
            except LoiDuLieu as loi:
                st.error(f"File chưa đúng yêu cầu. {loi}")
            except Exception as loi:  # noqa: BLE001 – người dùng không cần thấy thông báo kỹ thuật dài
                traceback.print_exc()  # chi tiết kỹ thuật in ra cửa sổ đang chạy dashboard
                st.error("Không phân tích được file này. Hãy kiểm tra file có đủ 19 cột và dữ liệu đúng kiểu như "
                         f"file điểm gốc. Dashboard vẫn giữ nguyên kết quả cũ. (Mã lỗi: {type(loi).__name__})")


def trang_lich_su() -> None:
    """Trang lịch sử phân tích (chỉ nhà trường): danh sách mọi lần phân tích, xem trước và tải về.

    Vì sao cần: reset hay phân tích file mới không làm mất kết quả cũ; nhà trường mở lại được bất kỳ
    lần nào, xem như trên dashboard, và tải về bản đầy đủ biểu đồ và lời giải thích.
    """
    ds = kho.danh_sach_lich_su(LICH_SU)
    if not ds:
        gd.tom_tat("Chưa có lần phân tích nào trong lịch sử.")
        return
    gd.tom_tat(f"Có <b>{len(ds)}</b> lần phân tích được lưu. Chọn một lần để xem trước hoặc tải về.")
    id_hien_tai = (kho.doc_thong_tin(KET_QUA) or {}).get("id")
    bang = pd.DataFrame([{
        "Thời gian": _thoi_gian(tt), "Dữ liệu": tt.get("ten", "–"), "Cách tạo": tt.get("cach_tao", "–"),
        "Số SV": gd.so(tt.get("so_sv")), "Số lớp": gd.so(tt.get("so_lop")),
        "Lớp bất thường": gd.so(tt.get("so_lop_bat_thuong")), "SV đổi mức": gd.so(tt.get("so_sv_doi_muc")),
        "Đang hiển thị": "Có" if tt.get("id") == id_hien_tai else ""} for _, tt in ds])
    st.dataframe(bang, hide_index=True, width="stretch", key="bang_lich_su")

    nhan = [f"{_thoi_gian(tt)} · {tt.get('ten', '–')}" for _, tt in ds]
    i = st.selectbox("Chọn một lần phân tích", range(len(ds)), format_func=lambda k: nhan[k], key="chon_lich_su")
    thu_muc, tt = ds[i]
    ten_file = f"bao_cao_{tt['id']}"
    c = st.columns(2)
    c[0].download_button("Tải báo cáo đầy đủ (HTML – mở bằng trình duyệt, in ra PDF được)",
                         bao_cao.tao_bao_cao_html(thu_muc).encode("utf-8"), f"{ten_file}.html", "text/html",
                         type="primary", width="stretch", key=f"tai_html_{tt['id']}")
    c[1].download_button("Tải toàn bộ file kết quả (ZIP)", bao_cao.nen_zip(thu_muc), f"ket_qua_{tt['id']}.zip",
                         "application/zip", width="stretch", key=f"tai_zip_{tt['id']}")
    gd.ghi_chu("Báo cáo HTML có đủ biểu đồ và lời giải thích như trên dashboard. Gói ZIP có thêm danh sách xếp mức "
               "từng sinh viên, điểm đã hiệu chỉnh và file điểm đầu vào.")

    if st.toggle("Xem trước lần phân tích này", key=f"xem_truoc_{tt['id']}"):
        kq = doc_ket_qua(str(thu_muc), dau_thoi_gian(thu_muc))
        if "sv" not in kq:
            st.error("Mục lịch sử này thiếu file kết quả.")
            return
        st.markdown(f"#### Xem trước: {gd.html.escape(tt.get('ten', ''))} ({_thoi_gian(tt)})")
        t = st.tabs(["Tổng quan", "Lớp học phần", "Hiệu chỉnh điểm"])
        with t[0]:
            trang_tong_quan(kq, NHA_TRUONG, khoa=f"ls_{tt['id']}_")
        with t[1]:
            trang_lop(kq, NHA_TRUONG, khoa=f"ls_{tt['id']}_")
        with t[2]:
            trang_hieu_chinh(kq, NHA_TRUONG, khoa=f"ls_{tt['id']}_")


# ---------------------------------------------------------------------------
# Thanh bên và khung trang
# ---------------------------------------------------------------------------
def chon_vai_tro() -> str:
    """Thanh bên: hiện vai trò đang xem; đăng nhập vai trò nhà trường bằng mật khẩu từ biến môi trường."""
    with st.sidebar:
        st.markdown("## Vai trò")
        if st.session_state.get("la_nha_truong"):
            st.success("Đang xem với vai trò **Nhà trường**: thấy đầy đủ từng lớp và từng sinh viên.")
            if st.button("Đăng xuất"):
                st.session_state["la_nha_truong"] = False
                st.rerun()
            return NHA_TRUONG
        st.info("Đang xem **công khai**: chỉ có số liệu tổng hợp.")
        mat_khau = os.environ.get("FIT_MAT_KHAU_NHA_TRUONG", "")
        with st.expander("Đăng nhập vai trò Nhà trường"):
            if not mat_khau:
                st.warning("Chưa đặt mật khẩu (biến môi trường FIT_MAT_KHAU_NHA_TRUONG) nên chưa đăng nhập được.")
            else:
                with st.form("dang_nhap"):
                    nhap = st.text_input("Mật khẩu", type="password")
                    if st.form_submit_button("Đăng nhập", type="primary"):
                        # So sánh dạng byte: compare_digest không nhận chuỗi có dấu tiếng Việt (chỉ nhận ASCII)
                        if nhap and hmac.compare_digest(nhap.encode("utf-8"), mat_khau.encode("utf-8")):
                            st.session_state["la_nha_truong"] = True
                            st.rerun()
                        else:
                            st.error("Sai mật khẩu.")
        return CONG_KHAI


def thong_tin_thanh_ben(kq: dict) -> None:
    """Thanh bên: dữ liệu đang hiển thị và chú giải các mức năng lực."""
    with st.sidebar:
        st.markdown("## Dữ liệu đang hiển thị")
        tt = kho.doc_thong_tin(KET_QUA)
        if tt:
            st.caption(f"{tt.get('ten', '–')} · phân tích lúc {_thoi_gian(tt)}")
        if "lop" in kq:
            st.caption(f"{gd.so(len(kq['sv']))} sinh viên · {gd.so(len(kq['lop']))} lớp học phần")
        st.markdown("## Các mức năng lực")
        for muc in ch3.THU_TU_MUC:
            st.markdown(f"{gd.huy_hieu_muc(muc)}<div class='ghi-chu' style='margin:0.1rem 0 0.55rem 0.2rem'>"
                        f"{gd.MUC_VIET[muc][1]}</div>", unsafe_allow_html=True)


def main() -> None:
    """Dựng trang: kiểu dáng, vai trò, đọc kết quả, hiện các trang theo quyền."""
    st.set_page_config(page_title="Phân tích điểm và năng lực sinh viên", layout="wide")
    gd.nap_css()
    st.title("Phân tích điểm và năng lực thực chất của sinh viên")
    st.markdown('<div class="phu-de">Phát hiện lớp chấm điểm bất thường · Hiệu chỉnh điểm cho công bằng · '
                'Xếp mức năng lực theo điểm đã hiệu chỉnh</div>', unsafe_allow_html=True)
    vai_tro = chon_vai_tro()
    if "thong_bao" in st.session_state:  # thông báo sau khi reset/phân tích (trang vừa được tải lại)
        st.success(st.session_state.pop("thong_bao"))
    kq = doc_ket_qua(str(KET_QUA), dau_thoi_gian(KET_QUA))
    co_du_lieu = "sv" in kq

    if not co_du_lieu:  # dashboard trống (đã reset, hoặc chưa phân tích lần nào)
        if vai_tro == CONG_KHAI:
            gd.tom_tat("Hiện chưa có dữ liệu phân tích. Dashboard sẽ hiển thị khi nhà trường tải dữ liệu điểm lên.")
            return
        t = st.tabs(["Phân tích dữ liệu mới", "Lịch sử phân tích"])
        with t[0]:
            trang_du_lieu_moi(False)
        with t[1]:
            trang_lich_su()
        return

    thong_tin_thanh_ben(kq)
    ten_tab = ["Tổng quan", "Lớp học phần", "Hiệu chỉnh điểm"]
    if vai_tro == NHA_TRUONG:
        ten_tab += ["Tra cứu sinh viên", "Phân tích dữ liệu mới", "Lịch sử phân tích"]
    tabs = st.tabs(ten_tab)
    with tabs[0]:
        trang_tong_quan(kq, vai_tro)
    # Viết if/else thường, không viết "a if ... else b": Streamlit tự hiện kết quả của biểu thức
    # đứng một mình (magic), nên dạng rút gọn làm trang hiện thêm chữ "None".
    with tabs[1]:
        if "lop" in kq:
            trang_lop(kq, vai_tro)
        else:
            st.info("Chưa có kết quả về lớp học phần.")
    with tabs[2]:
        if "hieu_chinh" in kq:
            trang_hieu_chinh(kq, vai_tro)
        else:
            st.info("Chưa có kết quả hiệu chỉnh điểm.")
    if vai_tro == NHA_TRUONG:
        with tabs[3]:
            trang_tra_cuu(kq)
        with tabs[4]:
            trang_du_lieu_moi(True)
        with tabs[5]:
            trang_lich_su()


main()

