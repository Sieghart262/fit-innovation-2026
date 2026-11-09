"""Yêu cầu 3 – Kiểm tra giả thuyết.

Giả thuyết A: Lạm phát nằm ở điểm quá trình (KTTX, GV tự chấm) hơn là điểm thi
(2 GV chấm). Đo bằng chênh lệch KTTX − Thi của từng lớp, so với các lớp KHÁC cùng môn.

Giả thuyết B: Điểm tăng từ HK2 2021-22 một phần do đổi trọng số (KTTX 20% → 40%),
không hẳn do "chấm dễ". Phải tách yếu tố này trước khi kết luận lạm phát.

Giả thuyết C: Lớp EP và đồ án/thực tập có mặt bằng điểm khác lớp thường → cần
so sánh riêng, không trộn chung.

Ghi nhớ về p-value: p < 0,05 thường được coi là "khác biệt có ý nghĩa thống kê",
nhưng với hàng chục nghìn lượt điểm, chênh lệch rất nhỏ cũng cho p rất nhỏ.
Luôn đọc p-value CÙNG với độ lớn chênh lệch.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import config as cf
from .report import tao_hinh


# ---------------------------------------------------------------------------
# Giả thuyết A – chênh lệch KTTX − Thi
# ---------------------------------------------------------------------------
def chenh_lech_kttx_thi(bang: pd.DataFrame) -> pd.DataFrame:
    """Tính chênh lệch KTTX − Thi của từng lớp và z-score so với các lớp khác cùng môn.

    Cách tính:
        1. Với mỗi SV (lớp không phải đồ án, có cả KTTX và Thi, Thi > 0):
           chenh = KTTX − Thi.
        2. Mỗi lớp: chenh_tb = trung bình chenh của SV trong lớp.
        3. "Leave-one-out" (để riêng một ra): so lớp X với trung bình và độ lệch
           chuẩn của các lớp CÒN LẠI cùng môn, không tính chính lớp X. Nếu tính cả
           X thì lớp càng bất thường càng kéo trung bình về phía nó, làm z nhỏ đi.
           z = (chenh_tb của X − TB các lớp khác) / σ các lớp khác.
    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        Bảng mỗi dòng một lớp (≥ 5 SV): Mã lớp, ma_mon, nam_hoc, hoc_ky, loai_lop,
        giai_doan, n, tb_kttx, tb_thi, chenh_tb, so_lop_khac_cung_mon,
        tb_chenh_lop_khac, z_chenh (trống nếu môn có < 3 lớp khác).
    Vì sao cần: so với chính môn đó (đúng khuyến nghị trong file mô tả) giúp loại
    ảnh hưởng của hình thức thi; một lớp có KTTX cao vọt so với Thi trong khi các
    lớp khác cùng môn không như vậy là tín hiệu mạnh cho HIGH_INFLATION.
    """
    loc = ((bang["loai_lop"] != cf.LOAI_DO_AN) & bang[cf.COT_KTTX].notna()
           & bang[cf.COT_THI].notna() & (bang[cf.COT_THI] > 0))
    du_lieu = bang.loc[loc].copy()
    du_lieu["chenh"] = du_lieu[cf.COT_KTTX] - du_lieu[cf.COT_THI]

    lop = du_lieu.groupby(cf.COT_MA_LOP).agg(
        ma_mon=(cf.COT_MA_MON, "first"), nam_hoc=(cf.COT_NAM_HOC, "first"),
        hoc_ky=(cf.COT_HOC_KY, "first"), loai_lop=("loai_lop", "first"),
        giai_doan=("giai_doan", "first"), n=(cf.COT_MA_SV, "nunique"),
        tb_kttx=(cf.COT_KTTX, "mean"), tb_thi=(cf.COT_THI, "mean"),
        chenh_tb=("chenh", "mean"),
    ).reset_index()
    lop = lop[lop["n"] >= cf.NGUONG_NHOM_TOI_THIEU].copy()

    # Tính TB và σ của "các lớp khác cùng môn" bằng công thức tổng, không cần vòng lặp:
    #   tổng các lớp khác       = tổng cả môn − x
    #   phương sai các lớp khác = (Σx² − x² − m·TB_khác²) / (m − 1),  m = số lớp khác
    x = lop["chenh_tb"]
    theo_mon = x.groupby(lop["ma_mon"])
    m = theo_mon.transform("count") - 1
    tb_khac = (theo_mon.transform("sum") - x) / m
    tong_binh_phuong = (x ** 2).groupby(lop["ma_mon"]).transform("sum")
    phuong_sai_khac = (tong_binh_phuong - x ** 2 - m * tb_khac ** 2) / (m - 1)
    sigma_khac = np.sqrt(phuong_sai_khac.clip(lower=0))  # clip: chặn số âm rất nhỏ do làm tròn

    du_lop = m >= cf.SO_LOP_KHAC_TOI_THIEU
    lop["so_lop_khac_cung_mon"] = m
    lop["tb_chenh_lop_khac"] = tb_khac.where(du_lop)
    lop["z_chenh"] = ((x - tb_khac) / sigma_khac).where(du_lop & (sigma_khac > 0))
    return lop


def tom_tat_chenh_lech(lop_chenh: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Tóm tắt kết quả chênh lệch KTTX − Thi.

    Tham số:
        lop_chenh: kết quả của chenh_lech_kttx_thi().
    Trả về:
        dict:
            "tong_quan"   : số lớp, số lớp tính được z, số lớp z > 2 và z < −2.
            "theo_giai_doan": TB chênh lệch trước/sau mốc đổi trọng số.
            "top"         : 15 lớp có z cao nhất (KTTX cao bất thường so với Thi).
    Vì sao cần: biết giả thuyết A có "ăn" không – nếu chỉ vài lớp có z > 2 thì đây
    là tiêu chí phân biệt tốt; nếu rất nhiều lớp thì cần siết ngưỡng.
    """
    z = lop_chenh["z_chenh"]
    tong_quan = pd.DataFrame([
        {"chi_so": "Số lớp có KTTX và Thi (≥ 5 SV)", "gia_tri": int(len(lop_chenh))},
        {"chi_so": f"Số lớp tính được z (môn có ≥ {cf.SO_LOP_KHAC_TOI_THIEU} lớp khác)",
         "gia_tri": int(z.notna().sum())},
        {"chi_so": "TB chênh lệch KTTX − Thi (điểm)", "gia_tri": float(lop_chenh["chenh_tb"].mean())},
        {"chi_so": f"Số lớp z > {cf.NGUONG_Z:g} (KTTX cao bất thường)", "gia_tri": int((z > cf.NGUONG_Z).sum())},
        {"chi_so": f"Số lớp z < −{cf.NGUONG_Z:g} (KTTX thấp bất thường)", "gia_tri": int((z < -cf.NGUONG_Z).sum())},
    ])
    theo_giai_doan = lop_chenh.groupby("giai_doan").agg(
        so_lop=(cf.COT_MA_LOP, "size"), so_luot=("n", "sum"),
        tb_kttx=("tb_kttx", "mean"), tb_thi=("tb_thi", "mean"), chenh_tb=("chenh_tb", "mean"),
    ).reset_index()
    top = (lop_chenh.dropna(subset=["z_chenh"]).sort_values("z_chenh", ascending=False).head(15)
           [[cf.COT_MA_LOP, "ma_mon", "nam_hoc", "hoc_ky", "loai_lop", "n", "tb_kttx", "tb_thi",
             "chenh_tb", "tb_chenh_lop_khac", "z_chenh"]])
    return {"tong_quan": tong_quan, "theo_giai_doan": theo_giai_doan, "top": top}


def tuong_quan_chenh_va_ty_le_A(lop_chenh: pd.DataFrame, lop_thong_ke: pd.DataFrame) -> pd.DataFrame:
    """Đo mức "đi cùng nhau" giữa chênh lệch KTTX − Thi và tỷ lệ điểm A của lớp.

    Dùng hệ số tương quan Spearman (rho, từ −1 đến 1): xét thứ hạng thay vì giá
    trị, nên ít bị ảnh hưởng bởi vài lớp cực đoan. rho > 0: lớp có chênh lệch lớn
    thường cũng có nhiều điểm A.
    Tham số:
        lop_chenh: kết quả của chenh_lech_kttx_thi().
        lop_thong_ke: bảng lớp từ distribution.thong_ke_theo_lop() (đã lọc ≥ 5 SV).
    Trả về:
        Bảng: cap_bien | so_lop | rho | p_value.
    Vì sao cần: nếu rho dương rõ rệt, chênh lệch KTTX − Thi là một "nguyên nhân"
    giải thích được của tỷ lệ A cao → rất hợp cho phần Explainable AI.
    """
    gop = lop_chenh.merge(lop_thong_ke[[cf.COT_MA_LOP, "ty_le_A"]], on=cf.COT_MA_LOP)
    dong = []
    for x, nhan in [("chenh_tb", "chenh_tb ~ ty_le_A"), ("z_chenh", "z_chenh ~ ty_le_A")]:
        cap = gop[[x, "ty_le_A"]].dropna()
        if len(cap) >= 3:
            rho, p = stats.spearmanr(cap[x], cap["ty_le_A"])
        else:
            rho, p = np.nan, np.nan
        dong.append({"cap_bien": nhan, "so_lop": len(cap), "rho": rho, "p_value": p})
    return pd.DataFrame(dong)


def ve_z_chenh(lop_chenh: pd.DataFrame):
    """Vẽ histogram z-score của chênh lệch KTTX − Thi.

    Tham số:
        lop_chenh: kết quả của chenh_lech_kttx_thi().
    Trả về:
        Hình matplotlib.
    Vì sao cần: các lớp ngoài hai vạch ±2 là ứng viên bất thường.
    """
    fig, ax = tao_hinh("z-score chênh lệch KTTX − Thi (so với lớp khác cùng môn)", "z", "Số lớp")
    ax.hist(lop_chenh["z_chenh"].dropna(), bins=40, color="#8172B2", edgecolor="white")
    for v in (-cf.NGUONG_Z, cf.NGUONG_Z):
        ax.axvline(v, color="red", linestyle="--")
    return fig


# ---------------------------------------------------------------------------
# Giả thuyết B – trước / sau mốc đổi trọng số
# ---------------------------------------------------------------------------
def _lop_thuong_co_diem(bang: pd.DataFrame) -> pd.DataFrame:
    """Lọc lượt điểm của lớp thường, HP > 0, biết rõ giai đoạn.

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        Bảng con đã lọc, có thêm cột _la_A.
    Vì sao cần: dùng chung cho các hàm so sánh giai đoạn; bỏ đồ án/EP và điểm 0
    để phép so sánh "táo với táo".
    """
    du_lieu = bang[(bang["loai_lop"] == cf.LOAI_THUONG) & (bang[cf.COT_HP] > 0)
                   & (bang["giai_doan"] != cf.GIAI_DOAN_KHONG_RO)].copy()
    du_lieu["_la_A"] = du_lieu[cf.COT_HP] >= cf.NGUONG_DIEM_A
    return du_lieu


def so_sanh_giai_doan(bang: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """So sánh điểm trước và từ HK2 2021-22 (mốc đổi trọng số 10/20/70 → 10/40/50).

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        dict:
            "tom_tat"   : số SV, số lớp, TB và σ của HP, tỷ lệ A, TB CC/KTTX/Thi mỗi giai đoạn.
            "kiem_dinh" : kiểm định Welch t-test cho HP, KTTX, Thi, CC (sau − trước).
            "theo_mon"  : so sánh CÙNG MÔN ở hai giai đoạn (Wilcoxon) – loại ảnh hưởng
                          của việc mở thêm/bớt môn giữa hai giai đoạn.
    Vì sao cần: nếu Thi gần như không đổi mà HP tăng, nhiều khả năng do KTTX được
    tăng trọng số (KTTX vốn cao hơn Thi). Khi đó "điểm tăng" chưa chắc là lạm phát.
    """
    du_lieu = _lop_thuong_co_diem(bang)
    tom_tat = du_lieu.groupby("giai_doan").agg(
        so_sv=(cf.COT_MA_SV, "nunique"), so_lop=(cf.COT_MA_LOP, "nunique"),
        so_luot=(cf.COT_HP, "size"), tb_hp=(cf.COT_HP, "mean"), sigma_hp=(cf.COT_HP, "std"),
        ty_le_A=("_la_A", "mean"), tb_cc=(cf.COT_CC, "mean"), tb_kttx=(cf.COT_KTTX, "mean"),
        tb_thi=(cf.COT_THI, "mean"),
    ).reindex([cf.GIAI_DOAN_TRUOC, cf.GIAI_DOAN_SAU]).dropna(how="all").reset_index()

    truoc = du_lieu[du_lieu["giai_doan"] == cf.GIAI_DOAN_TRUOC]
    sau = du_lieu[du_lieu["giai_doan"] == cf.GIAI_DOAN_SAU]
    dong = []
    for ten, cot in [("Điểm HP", cf.COT_HP), ("KTTX (TB)", cf.COT_KTTX),
                     ("Thi", cf.COT_THI), ("CC", cf.COT_CC)]:
        a, b = truoc[cot].dropna(), sau[cot].dropna()
        if len(a) >= 2 and len(b) >= 2:
            # Welch t-test: so sánh 2 trung bình, không giả định 2 nhóm có cùng phương sai.
            t, p = stats.ttest_ind(b, a, equal_var=False)
        else:
            t, p = np.nan, np.nan
        dong.append({"thanh_phan": ten, "so_luot_truoc": len(a), "so_luot_sau": len(b),
                     "tb_truoc": a.mean(), "tb_sau": b.mean(), "chenh_sau_tru_truoc": b.mean() - a.mean(),
                     "t": t, "p_value": p})
    kiem_dinh = pd.DataFrame(dong)

    # So sánh cùng môn: mỗi môn có TB HP ở cả hai giai đoạn (mỗi giai đoạn ≥ 5 SV)
    mon = du_lieu.groupby([cf.COT_MA_MON, "giai_doan"]).agg(
        n=(cf.COT_MA_SV, "nunique"), tb=(cf.COT_HP, "mean")).reset_index()
    mon = mon[mon["n"] >= cf.NGUONG_NHOM_TOI_THIEU]
    rong = mon.pivot(index=cf.COT_MA_MON, columns="giai_doan", values="tb")  # 1 dòng/môn, 1 cột/giai đoạn
    if {cf.GIAI_DOAN_TRUOC, cf.GIAI_DOAN_SAU} <= set(rong.columns):
        chenh = (rong[cf.GIAI_DOAN_SAU] - rong[cf.GIAI_DOAN_TRUOC]).dropna()
    else:
        chenh = pd.Series(dtype=float)
    p_w = np.nan
    if len(chenh) >= 5:
        try:
            # Wilcoxon: kiểm định "chênh lệch theo cặp có lệch khỏi 0 không", không cần phân phối chuẩn.
            p_w = stats.wilcoxon(chenh).pvalue
        except ValueError:  # vd mọi chênh lệch đều bằng 0
            p_w = np.nan
    theo_mon = pd.DataFrame([
        {"chi_so": "Số môn có mặt ở cả hai giai đoạn", "gia_tri": int(len(chenh))},
        {"chi_so": "TB chênh lệch HP (sau − trước), điểm", "gia_tri": float(chenh.mean()) if len(chenh) else np.nan},
        {"chi_so": "Trung vị chênh lệch, điểm", "gia_tri": float(chenh.median()) if len(chenh) else np.nan},
        {"chi_so": "Số môn tăng điểm", "gia_tri": int((chenh > 0).sum())},
        {"chi_so": "Số môn giảm điểm", "gia_tri": int((chenh < 0).sum())},
        # Ghi sẵn thành chữ vì cột gia_tri lẫn nhiều loại số, report không biết dòng nào là p-value.
        {"chi_so": "p_value (Wilcoxon)",
         "gia_tri": "–" if pd.isna(p_w) else ("<0.001" if p_w < 0.001 else f"{p_w:.3f}")},
    ])
    return {"tom_tat": tom_tat, "kiem_dinh": kiem_dinh, "theo_mon": theo_mon}


def xu_huong_theo_ky(bang: pd.DataFrame) -> pd.DataFrame:
    """Điểm TB của HP, KTTX, Thi và tỷ lệ A theo từng học kỳ (lớp thường).

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        Bảng: ky_so | nhan_ky | so_sv | tb_hp | tb_kttx | tb_thi | ty_le_A (sắp theo thời gian).
    Vì sao cần: nhìn xu hướng để thấy điểm có "nhảy bậc" đúng ở mốc HK2 2021-22
    hay tăng dần đều (lạm phát kéo dài).
    """
    du_lieu = _lop_thuong_co_diem(bang)
    return du_lieu.groupby(["ky_so", "nhan_ky"]).agg(
        so_sv=(cf.COT_MA_SV, "nunique"), tb_hp=(cf.COT_HP, "mean"), tb_kttx=(cf.COT_KTTX, "mean"),
        tb_thi=(cf.COT_THI, "mean"), ty_le_A=("_la_A", "mean"),
    ).reset_index().sort_values("ky_so")


def ve_xu_huong(ky: pd.DataFrame):
    """Vẽ đường điểm TB HP/KTTX/Thi theo học kỳ, có vạch mốc đổi trọng số.

    Tham số:
        ky: kết quả của xu_huong_theo_ky() (đã ẩn nhóm nhỏ).
    Trả về:
        Hình matplotlib.
    Vì sao cần: hình chính cho giả thuyết B trong báo cáo.
    """
    fig, ax = tao_hinh("Điểm TB theo học kỳ (lớp thường, HP > 0)", "Học kỳ", "Điểm TB")
    vi_tri = np.arange(len(ky))
    for cot, nhan in [("tb_hp", "HP"), ("tb_kttx", "KTTX"), ("tb_thi", "Thi")]:
        ax.plot(vi_tri, ky[cot], marker="o", label=nhan)
    moc = cf.MOC_DOI_TRONG_SO[0] * 10 + cf.MOC_DOI_TRONG_SO[1]
    sau_moc = np.nonzero(ky["ky_so"].to_numpy() >= moc)[0]  # vị trí các kỳ từ mốc trở đi
    if len(sau_moc):
        ax.axvline(sau_moc[0] - 0.5, color="red", linestyle="--", label="Đổi trọng số")
    ax.set_xticks(vi_tri)
    ax.set_xticklabels(ky["nhan_ky"], rotation=60, fontsize=7)
    ax.legend()
    return fig


def co_cau_trong_so(bang: pd.DataFrame, so_dong_moi_giai_doan: int = 6) -> pd.DataFrame:
    """Các cơ cấu trọng số (suy ra) phổ biến nhất trong từng giai đoạn.

    Tham số:
        bang: bảng điểm đã xử lý.
        so_dong_moi_giai_doan: lấy bao nhiêu cơ cấu đứng đầu mỗi giai đoạn.
    Trả về:
        Bảng: giai_doan | co_cau_trong_so | so_luot | so_sv | ty_le_trong_giai_doan.
    Vì sao cần: xác nhận bằng dữ liệu rằng mốc đổi 10/20/70 → 10/40/50 đúng như mô tả,
    trước khi dùng mốc này để giải thích xu hướng điểm.
    """
    du_lieu = bang[bang["loai_lop"] != cf.LOAI_DO_AN]
    du_lieu = du_lieu.assign(co_cau_trong_so=du_lieu[cf.COT_TRONG_SO].fillna("(trống)"))
    kq = du_lieu.groupby(["giai_doan", "co_cau_trong_so"]).agg(
        so_luot=(cf.COT_MA_SV, "size"), so_sv=(cf.COT_MA_SV, "nunique")).reset_index()
    kq["ty_le_trong_giai_doan"] = kq["so_luot"] / kq.groupby("giai_doan")["so_luot"].transform("sum")
    kq = kq.sort_values(["giai_doan", "so_luot"], ascending=[True, False])
    return kq.groupby("giai_doan").head(so_dong_moi_giai_doan)


# ---------------------------------------------------------------------------
# Giả thuyết C – lớp EP, đồ án và lớp thường
# ---------------------------------------------------------------------------
def so_sanh_loai_lop(bang: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """So sánh mặt bằng điểm giữa Lớp thường, Lớp EP và Đồ án/TT/KL.

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        (bảng chỉ số theo loại lớp, bảng kiểm định Welch EP vs thường và đồ án vs thường).
        Bảng chỉ số gồm: so_lop, so_sv, so_luot, ty_le_dat, ty_le_hp_0 (trên mọi lượt có HP),
        tb_hp, sigma_hp, ty_le_A (trên HP > 0), ty_le_trong_CC, ty_le_trong_KTTX.
    Vì sao cần: nếu đồ án có tỷ lệ A rất cao "một cách tự nhiên" (chấm theo từng SV),
    trộn chung sẽ khiến thuật toán gắn nhãn lạm phát sai cho mọi lớp đồ án.
    """
    co_hp = bang[bang[cf.COT_HP].notna()].copy()
    co_hp["_dat"] = co_hp[cf.COT_HP] >= cf.NGUONG_DAT
    co_hp["_hp_0"] = co_hp[cf.COT_HP] == 0
    chung = co_hp.groupby("loai_lop").agg(
        so_lop=(cf.COT_MA_LOP, "nunique"), so_sv=(cf.COT_MA_SV, "nunique"),
        so_luot=(cf.COT_HP, "size"), ty_le_dat=("_dat", "mean"), ty_le_hp_0=("_hp_0", "mean"))

    duong = co_hp[co_hp[cf.COT_HP] > 0].copy()
    duong["_la_A"] = duong[cf.COT_HP] >= cf.NGUONG_DIEM_A
    diem = duong.groupby("loai_lop").agg(
        tb_hp=(cf.COT_HP, "mean"), sigma_hp=(cf.COT_HP, "std"), ty_le_A=("_la_A", "mean"))

    trong = bang[[cf.COT_CC, cf.COT_KTTX]].isna().groupby(bang["loai_lop"]).mean()
    trong.columns = ["ty_le_trong_CC", "ty_le_trong_KTTX"]
    chi_so = chung.join(diem).join(trong).reset_index()

    dong = []
    thuong = duong.loc[duong["loai_lop"] == cf.LOAI_THUONG, cf.COT_HP]
    for loai in (cf.LOAI_EP, cf.LOAI_DO_AN):
        khac = duong.loc[duong["loai_lop"] == loai, cf.COT_HP]
        if len(khac) >= 2 and len(thuong) >= 2:
            t, p = stats.ttest_ind(khac, thuong, equal_var=False)
        else:
            t, p = np.nan, np.nan
        dong.append({"so_sanh": f"{loai} vs {cf.LOAI_THUONG}", "so_luot_nhom": len(khac),
                     "chenh_tb_hp": khac.mean() - thuong.mean(), "t": t, "p_value": p})
    return chi_so, pd.DataFrame(dong)


def ve_loai_lop(chi_so: pd.DataFrame):
    """Vẽ hai biểu đồ cột: điểm TB và tỷ lệ A theo loại lớp.

    Tham số:
        chi_so: bảng chỉ số từ so_sanh_loai_lop().
    Trả về:
        Hình matplotlib.
    Vì sao cần: minh họa nhanh lý do phải tách loại lớp.
    """
    fig, ax = tao_hinh("Điểm TB (cột) và tỷ lệ A (đường) theo loại lớp", "Loại lớp", "Điểm TB HP")
    ax.bar(chi_so["loai_lop"], chi_so["tb_hp"], color="#4C72B0")
    ax.set_ylim(0, 10)
    ax2 = ax.twinx()  # trục dọc thứ hai bên phải cho tỷ lệ
    ax2.plot(chi_so["loai_lop"], chi_so["ty_le_A"], color="red", marker="o")
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("Tỷ lệ điểm A")
    return fig
