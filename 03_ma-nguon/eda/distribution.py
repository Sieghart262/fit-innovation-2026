"""Yêu cầu 2 – Phân bố điểm.

Tính cho từng lớp: điểm TB, độ lệch chuẩn σ, tỷ lệ điểm A. Đây chính là
"nguyên liệu thô" của Giải pháp 1 (Anomaly Score). Xem trước phân bố giúp đội
chọn ngưỡng hợp lý thay vì đoán.

Quy ước: thống kê điểm lớp tính trên SV có HP > 0 (bỏ điểm 0 vì gồm cả vắng thi).
Chỉ công bố lớp có ít nhất 5 sinh viên.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cf
from .report import tao_hinh


def thong_ke_theo_lop(bang: pd.DataFrame) -> pd.DataFrame:
    """Tính các chỉ số điểm cho từng lớp học phần.

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        Bảng, mỗi dòng một lớp: Mã lớp, ma_mon, nhom_mon, nam_hoc, hoc_ky, loai_lop,
        giai_doan, n (số SV có HP > 0), tb, sigma, ty_le_A, tb_kttx, tb_thi,
        si_so_file (mọi dòng của lớp), ty_le_hp_0.
    Vì sao cần: đề bài phát hiện bất thường ở cấp LỚP dựa trên đúng các chỉ số này
    (điểm TB lệch, σ → 0, tỷ lệ A > 60%).
    """
    co_hp = bang[bang[cf.COT_HP].notna()]
    duong = co_hp[co_hp[cf.COT_HP] > 0].copy()
    # Tạo cột True/False trước rồi lấy trung bình = tỷ lệ. Cách này nhanh hơn
    # dùng lambda trong groupby – quan trọng khi dữ liệu > 100.000 dòng.
    duong["_la_A"] = duong[cf.COT_HP] >= cf.NGUONG_DIEM_A

    kq = duong.groupby(cf.COT_MA_LOP).agg(
        ma_mon=(cf.COT_MA_MON, "first"),
        nhom_mon=(cf.COT_NHOM_MON, "first"),
        nam_hoc=(cf.COT_NAM_HOC, "first"),
        hoc_ky=(cf.COT_HOC_KY, "first"),
        loai_lop=("loai_lop", "first"),
        giai_doan=("giai_doan", "first"),
        n=(cf.COT_MA_SV, "nunique"),
        tb=(cf.COT_HP, "mean"),
        sigma=(cf.COT_HP, "std"),   # độ lệch chuẩn mẫu (chia cho n − 1)
        ty_le_A=("_la_A", "mean"),
        tb_kttx=(cf.COT_KTTX, "mean"),
        tb_thi=(cf.COT_THI, "mean"),
    )
    kq["si_so_file"] = bang.groupby(cf.COT_MA_LOP).size().reindex(kq.index)
    kq["ty_le_hp_0"] = (co_hp[cf.COT_HP] == 0).groupby(co_hp[cf.COT_MA_LOP]).mean().reindex(kq.index)
    return kq.reset_index()


def lop_du_lon(lop: pd.DataFrame) -> pd.DataFrame:
    """Giữ lại các lớp có ít nhất 5 SV.

    Tham số:
        lop: kết quả của thong_ke_theo_lop().
    Trả về:
        Bảng lớp đã lọc.
    Vì sao cần: (1) quy tắc riêng tư; (2) lớp quá ít người thì σ và tỷ lệ A rất
    "nhảy" – 2/3 SV điểm A đã là 67% – dễ gây báo động giả.
    """
    return lop[lop["n"] >= cf.NGUONG_NHOM_TOI_THIEU].copy()


def mo_ta_chi_so_lop(lop: pd.DataFrame) -> pd.DataFrame:
    """Thống kê mô tả (min, phân vị, max...) của tb, sigma, ty_le_A trên các lớp.

    Tham số:
        lop: bảng lớp đã lọc (≥ 5 SV), chỉ lớp thường.
    Trả về:
        Bảng: chi_so | count | mean | std | min | 25% | 50% | 75% | max.
    Vì sao cần: biết "mặt bằng chung" trông thế nào – vd σ của lớp thường khoảng
    bao nhiêu – để định nghĩa thế nào là "σ quá nhỏ".
    """
    mo_ta = lop[["tb", "sigma", "ty_le_A"]].describe().T
    mo_ta.index = ["tb (điểm TB lớp)", "sigma (độ lệch chuẩn)", "ty_le_A (0–1)"]
    return mo_ta.rename_axis("chi_so").reset_index()


def dem_lop_vuot_nguong_A(lop: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Đếm số lớp có tỷ lệ điểm A > 60%, theo loại lớp và theo năm học.

    Tham số:
        lop: bảng lớp đã lọc (≥ 5 SV).
    Trả về:
        dict {"theo_loai": bảng, "theo_nam": bảng (chỉ lớp thường)}; mỗi bảng có
        so_lop, so_luot (tổng SV của các lớp), so_lop_vuot, ty_le_lop_vuot.
    Vì sao cần: đề bài gợi ý ngưỡng 60%. Nếu quá nhiều lớp vượt ngưỡng (vd 40%),
    ngưỡng này quá thấp với dữ liệu thật; nếu gần như không lớp nào vượt, cần tiêu chí khác.
    """
    lop = lop.assign(_vuot=lop["ty_le_A"] > cf.NGUONG_TY_LE_A)

    def _gom(nhom_theo: str, du_lieu: pd.DataFrame) -> pd.DataFrame:
        """Gom các lớp theo một cột và đếm số lớp vượt ngưỡng.

        Tham số:
            nhom_theo: tên cột để gom (loai_lop hoặc nam_hoc).
            du_lieu: bảng lớp.
        Trả về:
            Bảng đếm. Vì sao cần: dùng chung cho 2 cách gom bên dưới.
        """
        kq = du_lieu.groupby(nhom_theo).agg(
            so_lop=(cf.COT_MA_LOP, "size"), so_luot=("n", "sum"), so_lop_vuot=("_vuot", "sum"))
        kq["ty_le_lop_vuot"] = kq["so_lop_vuot"] / kq["so_lop"]
        return kq.reset_index()

    return {"theo_loai": _gom("loai_lop", lop),
            "theo_nam": _gom("nam_hoc", lop[lop["loai_lop"] == cf.LOAI_THUONG])}


def top_lop(lop: pd.DataFrame, theo: str, tang_dan: bool, so_dong: int = 15) -> pd.DataFrame:
    """Lấy các lớp đứng đầu theo một chỉ số (vd tỷ lệ A cao nhất, σ nhỏ nhất).

    Tham số:
        lop: bảng lớp đã lọc (≥ 5 SV).
        theo: tên cột để sắp xếp.
        tang_dan: True = nhỏ nhất trước (dùng cho σ), False = lớn nhất trước.
        so_dong: số lớp muốn lấy.
    Trả về:
        Bảng rút gọn các cột cần xem.
    Vì sao cần: đây là "ứng viên" cho kịch bản video demo (phát hiện một lớp
    điểm cao bất thường). Chỉ có mã lớp/mã môn, không có thông tin sinh viên.
    """
    cot = [cf.COT_MA_LOP, "ma_mon", "nam_hoc", "hoc_ky", "loai_lop", "n", "tb", "sigma",
           "ty_le_A", "tb_kttx", "tb_thi"]
    return lop.sort_values(theo, ascending=tang_dan).head(so_dong)[cot]


def phan_bo_si_so(bang: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Phân bố sĩ số lớp (số dòng của mỗi lớp trong file).

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        (bảng đếm số lớp theo khoảng sĩ số, bảng mô tả min/TB/trung vị/max của sĩ số).
    Vì sao cần: Z-score và σ không đáng tin ở lớp nhỏ. Biết có bao nhiêu lớp nhỏ
    giúp chọn sĩ số tối thiểu cho Giải pháp 1 và xem nên dùng kỹ thuật "co về
    trung bình" (shrinkage) cho lớp nhỏ không.
    """
    si_so = bang.groupby(cf.COT_MA_LOP).size()
    moc = [0, 4, 14, 29, 49, 79, np.inf]
    nhan = ["1–4", "5–14", "15–29", "30–49", "50–79", "80+"]
    nhom = pd.cut(si_so, bins=moc, labels=nhan)  # (0,4], (4,14], ...
    dem = nhom.value_counts().reindex(nhan).rename_axis("si_so").reset_index(name="so_lop")
    mo_ta = si_so.describe().rename_axis("chi_so").reset_index(name="gia_tri")
    return dem, mo_ta


def dem_diem_theo_khoang(bang: pd.DataFrame, cot: str, buoc: float = 0.5) -> pd.DataFrame:
    """Đếm số lượt và số SV theo từng khoảng điểm (lớp thường).

    Tham số:
        bang: bảng điểm đã xử lý.
        cot: cột điểm (vd HP, KTTX, Thi).
        buoc: độ rộng mỗi khoảng điểm.
    Trả về:
        Bảng: khoang | so_luot | so_sv | ty_le_luot (tỷ lệ trong tổng số lượt).
    Vì sao cần: vẽ histogram mà vẫn tuân thủ quy tắc riêng tư – ta đếm trước,
    ẩn khoảng < 5 người, rồi mới vẽ, thay vì đưa thẳng điểm từng người cho hàm vẽ.
    """
    du_lieu = bang[(bang["loai_lop"] == cf.LOAI_THUONG) & bang[cot].notna()]
    moc = np.arange(0, 10 + buoc, buoc)
    nhan = [f"{a:.1f}–{b:.1f}" for a, b in zip(moc[:-1], moc[1:])]
    khoang = pd.cut(du_lieu[cot], bins=moc, labels=nhan, include_lowest=True).rename("khoang")
    kq = du_lieu.groupby(khoang, observed=False).agg(
        so_luot=(cf.COT_MA_SV, "size"), so_sv=(cf.COT_MA_SV, "nunique")).reset_index()
    kq["khoang"] = kq["khoang"].astype(str)
    kq["ty_le_luot"] = kq["so_luot"] / max(int(kq["so_luot"].sum()), 1)
    return kq


def ve_cot_khoang(cac_bang: dict[str, pd.DataFrame], tieu_de: str):
    """Vẽ phân bố điểm từ các bảng đếm theo khoảng (đã ẩn nhóm nhỏ).

    Tham số:
        cac_bang: {tên đường: bảng từ dem_diem_theo_khoang()}; 1 bảng = vẽ cột,
            nhiều bảng = vẽ đường để so sánh (vd KTTX vs Thi).
        tieu_de: tiêu đề hình.
    Trả về:
        Hình matplotlib.
    Vì sao cần: so sánh hình dạng phân phối – vd KTTX dồn về 8–10 trong khi Thi
    trải rộng là dấu hiệu điểm quá trình bị chấm rộng tay.
    """
    fig, ax = tao_hinh(tieu_de, "Khoảng điểm", "Tỷ lệ lượt điểm")
    # Dựng lại ĐỦ các khoảng 0–10 (cùng độ rộng, cùng cách ghi nhãn như
    # dem_diem_theo_khoang) để khoảng bị ẩn vẫn giữ chỗ trên trục, hiện thành ô
    # trống – nếu không, "0.0–0.5" sẽ nằm sát "1.5–2.0" và người đọc hiểu nhầm.
    mot_nhan = next(iter(cac_bang.values()))["khoang"].iloc[0]
    dau, cuoi = (float(x) for x in mot_nhan.split("–"))
    moc = np.arange(0, 10 + (cuoi - dau), cuoi - dau)
    tat_ca = [f"{a:.1f}–{b:.1f}" for a, b in zip(moc[:-1], moc[1:])]
    vi_tri = np.arange(len(tat_ca))
    for ten, b in cac_bang.items():
        gia_tri = b.set_index("khoang")["ty_le_luot"].reindex(tat_ca)  # khoảng bị ẩn -> NaN
        if len(cac_bang) == 1:
            ax.bar(vi_tri, gia_tri.values, color="#4C72B0", label=ten)
        else:
            ax.plot(vi_tri, gia_tri.values, marker="o", label=ten)
    ax.set_xticks(vi_tri)
    ax.set_xticklabels(tat_ca, rotation=60, fontsize=7)
    ax.legend()
    return fig


def ve_histogram_lop(lop: pd.DataFrame, cot: str, tieu_de: str, nhan_x: str,
                     duong_doc: float | None = None):
    """Vẽ histogram một chỉ số cấp lớp (mỗi lớp là một quan sát).

    Tham số:
        lop: bảng lớp đã lọc (≥ 5 SV).
        cot: chỉ số cần vẽ (tb, ty_le_A, ...).
        tieu_de, nhan_x: chữ trên hình.
        duong_doc: nếu có, vẽ thêm vạch đỏ (vd ngưỡng 60%).
    Trả về:
        Hình matplotlib.
    Vì sao cần: thấy ngay các lớp nằm "lẻ loi" ở đuôi phân phối – ứng viên bất thường.
    """
    fig, ax = tao_hinh(tieu_de, nhan_x, "Số lớp")
    ax.hist(lop[cot].dropna(), bins=30, color="#4C72B0", edgecolor="white")
    if duong_doc is not None:
        ax.axvline(duong_doc, color="red", linestyle="--", label=f"Ngưỡng {duong_doc:g}")
        ax.legend()
    return fig


def ve_tb_va_sigma(lop: pd.DataFrame):
    """Vẽ biểu đồ chấm: trục ngang = điểm TB lớp, trục dọc = σ, màu = loại lớp.

    Tham số:
        lop: bảng lớp đã lọc (≥ 5 SV).
    Trả về:
        Hình matplotlib.
    Vì sao cần: lớp "lạm phát" thường nằm góc phải-dưới (TB cao, σ nhỏ: ai cũng
    điểm cao như nhau). Đây là hình rất hợp để đưa vào báo cáo.
    """
    fig, ax = tao_hinh("Điểm TB lớp và độ lệch chuẩn σ", "Điểm TB lớp (HP > 0)", "σ")
    for loai, nhom in lop.groupby("loai_lop"):
        ax.scatter(nhom["tb"], nhom["sigma"], s=12, alpha=0.6, label=loai)
    ax.legend()
    return fig


def ve_si_so(bang_si_so: pd.DataFrame):
    """Vẽ cột số lớp theo khoảng sĩ số.

    Tham số:
        bang_si_so: bảng đếm từ phan_bo_si_so().
    Trả về:
        Hình matplotlib.
    Vì sao cần: minh họa có bao nhiêu lớp quá nhỏ để tin vào thống kê.
    """
    fig, ax = tao_hinh("Phân bố sĩ số lớp (trong dữ liệu)", "Sĩ số", "Số lớp")
    ax.bar(bang_si_so["si_so"].astype(str), bang_si_so["so_lop"], color="#55A868")
    return fig
