"""Xuất kết quả Giải pháp 1: bảng CSV, biểu đồ và báo cáo Markdown.

Kết quả là bảng THEO LỚP (không có Mã SV), dành cho nhà trường nên giữ đủ mọi lớp,
kể cả lớp nhỏ. Mặc định ghi vào 01_du-lieu/ket-qua/gp1/ (bị .gitignore chặn).
Khi đưa số liệu vào báo cáo công khai (PDF, video) phải lọc qua eda.privacy.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # vẽ ra file, không mở cửa sổ
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from eda import config as cf  # noqa: E402
from eda.report import bang_markdown  # noqa: E402
from . import cau_hinh as ch  # noqa: E402

MAU = {ch.NORMAL: "#9e9e9e", ch.REVIEW: "#c0a060", ch.HIGH: "#e53935",
       ch.STEEP: "#1e88e5", ch.DIST: "#fb8c00"}

COT_XEP_HANG = {
    "rank": "Hạng", "class_id": "Mã lớp HP", "course": "Mã môn", "group": "Nhóm môn",
    "year": "Năm học", "sem": "Học kỳ", "is_project": "Đồ án/TT", "is_ep": "Lớp EP",
    "co_cau": "Cơ cấu điểm", "n_sv": "Số SV", "n": "Số điểm hợp lệ",
    "anomaly_score": "Anomaly Score", "anomaly_type": "Nhãn", "y_nghia_nhan": "Ý nghĩa nhãn",
    "severity": "Mức độ", "secondary_flags": "Nhãn phụ",
    "du_dieu_kien_hieu_chinh": "Đủ điều kiện hiệu chỉnh (GP2)", "huong_hieu_chinh": "Hướng hiệu chỉnh",
    "mean": "ĐTB lớp", "ref_mean": "ĐTB mốc", "ref_level": "Mốc so sánh", "ref_n_classes": "Số lớp mốc",
    "z_mean": "z ĐTB", "z_adj": "z sau khi trừ năng lực nền", "q_value": "q-value (FDR)",
    "std": "σ", "sigma_ratio": "σ / σ mốc", "a_rate": "Tỷ lệ A", "a_ucl": "Giới hạn kiểm soát tỷ lệ A",
    "fail_rate": "Tỷ lệ trượt", "proc_exam_gap": "KTTX − Thi", "kttx_eq_exam": "Tỷ lệ KTTX = Thi",
    "rho_ability": "ρ với năng lực nền", "dev_up": "Điểm lệch lên", "dev_down": "Điểm lệch xuống",
    "E_up": "Bằng chứng (lệch lên)", "E_down": "Bằng chứng (lệch xuống)",
    "rule_score": "Điểm quy tắc", "ml_score": "Điểm Isolation Forest",
    "ca_hai_cung_nghi": "Quy tắc và học máy cùng nghi", "explanation": "Giải thích",
}


def kiem_tra_khong_co_ma_sv(bang: pd.DataFrame, ten: str) -> None:
    """Dừng nếu bảng kết quả có cột Mã SV (kết quả GP1 chỉ ở mức lớp).

    Tham số:
        bang: bảng sắp ghi ra file; ten: tên bảng để báo lỗi.
    Vì sao cần: chặn nhầm lẫn đưa dữ liệu từng SV vào file kết quả theo lớp.
    """
    if {"student", cf.COT_MA_SV} & set(bang.columns):
        raise ValueError(f"Bảng {ten} có cột Mã SV – không được ghi ra kết quả GP1.")


def diem_nong(kq: pd.DataFrame) -> pd.DataFrame:
    """Đếm lớp bị gắn nhãn bất thường theo từng môn (giữ từ bản gốc).

    Tham số:
        kq: bảng kết quả.
    Trả về:
        Bảng mỗi môn: số lớp được chấm, số lớp bất thường, Anomaly Score TB/lớn nhất, ĐTB, tỷ lệ A, nhãn chủ đạo.
    Vì sao cần: môn có nhiều lớp bất thường là "điểm nóng" để nhà trường ưu tiên rà soát.
    """
    el = kq[kq["anomaly_score"].notna()].copy()
    el["co"] = el["anomaly_type"].isin(ch.NHAN_BAT_THUONG)
    hs = el.groupby(["course", "group"]).agg(
        so_lop=("class_id", "count"), so_lop_bat_thuong=("co", "sum"),
        so_lop_can_xem_xet=("anomaly_type", lambda s: int((s == ch.REVIEW).sum())),
        anomaly_tb=("anomaly_score", "mean"), anomaly_max=("anomaly_score", "max"),
        dtb_mon=("mean", "mean"), ty_le_A_tb=("a_rate", "mean")).reset_index()
    hs["ty_le_bat_thuong"] = hs["so_lop_bat_thuong"] / hs["so_lop"]
    chu_dao = el[el["co"]].groupby("course")["anomaly_type"].agg(lambda s: s.value_counts().index[0])
    hs["nhan_chu_dao"] = hs["course"].map(chu_dao).fillna("")
    return hs.sort_values(["so_lop_bat_thuong", "anomaly_tb"], ascending=False)


def xu_huong(kq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Xu hướng ĐTB, tỷ lệ A và số lớp bất thường theo nhóm môn × năm học (giữ từ bản gốc).

    Tham số:
        kq: bảng kết quả.
    Trả về:
        (bảng theo nhóm môn × năm, bảng độ dốc tăng mỗi năm theo nhóm môn).
    Vì sao cần: tách "lạm phát dài hạn của cả nhóm môn" khỏi "một lớp bất thường".
    """
    el = kq[kq["anomaly_score"].notna() & ~kq["is_project"].astype(bool)].copy()
    el["co"] = el["anomaly_type"].isin(ch.NHAN_BAT_THUONG)
    t = el.groupby(["group", "year"]).agg(so_lop=("class_id", "count"), dtb=("mean", "mean"),
                                          ty_le_A=("a_rate", "mean"), so_lop_bat_thuong=("co", "sum")).reset_index()
    doc = []
    for nhom, s in t.groupby("group"):
        nam = s["year"].str[:4].astype(int).to_numpy()
        if len(nam) >= 3:
            m, a = stats.linregress(nam, s["dtb"]), stats.linregress(nam, s["ty_le_A"])
            doc.append(dict(group=nhom, tang_dtb_moi_nam=m.slope, p_value_dtb=m.pvalue,
                            tang_ty_le_A_moi_nam=a.slope, p_value_A=a.pvalue))
    return t, pd.DataFrame(doc)


def ve_bieu_do(kq: pd.DataFrame, diem: dict, ds_moc: dict, xh: pd.DataFrame, thu_muc: Path) -> dict:
    """Vẽ 5 biểu đồ (giữ từ bản gốc, thêm nhãn NEEDS_REVIEW).

    Tham số:
        kq: bảng kết quả; diem: {lớp: điểm HP}; ds_moc: {lớp: các lớp mốc};
        xh: bảng xu hướng nhóm môn × năm; thu_muc: nơi lưu PNG.
    Trả về:
        {tên: đường dẫn PNG}.
    Vì sao cần: biểu đồ giúp nhà trường và giám khảo nhìn nhanh kết quả.
    """
    thu_muc.mkdir(parents=True, exist_ok=True)
    el = kq[kq["anomaly_score"].notna()]
    thu_tu = [ch.NORMAL, ch.REVIEW] + ch.NHAN_BAT_THUONG
    ra = {}

    def luu(fig, ten):
        p = thu_muc / ten
        fig.tight_layout()
        fig.savefig(p, dpi=130)
        plt.close(fig)
        ra[ten] = p

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for nhan in thu_tu:
        s = el.loc[el["anomaly_type"] == nhan, "anomaly_score"]
        ax.hist(s, bins=np.linspace(0, 1, 41), color=MAU[nhan], alpha=0.85, label=f"{nhan} ({len(s)})")
    ax.set(xlabel="Anomaly Score", ylabel="Số lớp học phần", title="Phân phối Anomaly Score các lớp học phần")
    ax.legend()
    luu(fig, "1_phan_phoi_anomaly_score.png")

    fig, ax = plt.subplots(figsize=(9, 6))
    for nhan in thu_tu:
        s = el[el["anomaly_type"] == nhan]
        ax.scatter(s["z_mean"].clip(-8, 8), s["a_rate"], s=s["n"] * 1.5, c=MAU[nhan],
                   alpha=0.6, edgecolor="w", lw=0.5, label=nhan)
    ax.axvline(2, ls=":", c="k")
    ax.axvline(-2, ls=":", c="k")
    ax.set(xlabel="z ĐTB lớp so với mốc (cắt ±8)", ylabel="Tỷ lệ điểm A (≥ 8,5)",
           title="Bản đồ lớp học phần: độ lệch so với mốc và tỷ lệ A")
    ax.legend(loc="upper left")
    luu(fig, "2_ban_do_z_ty_le_A.png")

    top = el.head(20).iloc[::-1]
    if len(top):
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.barh(top["class_id"] + " · " + top["course"] + " · " + top["year"].astype(str),
                top["anomaly_score"], color=[MAU[t] for t in top["anomaly_type"]])
        for i, v in enumerate(top["anomaly_score"]):
            ax.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=8)
        ax.set(xlim=(0, 1.05), xlabel="Anomaly Score", title="Top 20 lớp học phần nghi vấn")
        luu(fig, "3_top20_lop_nghi_van.png")

    chon = [r for nhan in ch.NHAN_BAT_THUONG for r in el[el["anomaly_type"] == nhan].head(2).itertuples()]
    if chon:
        fig, axes = plt.subplots(2, 3, figsize=(14, 7.5))
        for ax, r in zip(axes.flat, chon):
            moc = ds_moc.get(r.class_id, [])
            khoang = np.arange(0, 10.51, 0.5)
            if moc:
                ax.hist(np.concatenate([diem[c] for c in moc]), bins=khoang, density=True,
                        color="#bdbdbd", label=f"Mốc: {r.ref_level}")
            ax.hist(diem[r.class_id], bins=khoang, density=True, histtype="step", lw=2.2,
                    color=MAU[r.anomaly_type], label=r.class_id)
            ax.set_title(f"{r.class_id} ({r.course}) – {r.anomaly_type}\nScore={r.anomaly_score:.2f}", fontsize=9)
            ax.legend(fontsize=7)
        for ax in list(axes.flat)[len(chon):]:
            ax.axis("off")
        fig.suptitle("Phân phối Điểm HP của lớp nghi vấn tiêu biểu so với mốc")
        luu(fig, "4_phan_phoi_lop_tieu_bieu.png")

    if len(xh):
        pv = xh.assign(r=xh["so_lop_bat_thuong"] / xh["so_lop"]).pivot(index="group", columns="year", values="r")
        fig, ax = plt.subplots(figsize=(10, 4.5))
        im = ax.imshow(pv.to_numpy(float), cmap="Reds", vmin=0, vmax=max(0.5, np.nanmax(pv.to_numpy(float))))
        ax.set_xticks(range(len(pv.columns)), pv.columns, rotation=30)
        ax.set_yticks(range(len(pv.index)), pv.index)
        for i in range(pv.shape[0]):
            for j in range(pv.shape[1]):
                if not np.isnan(pv.iat[i, j]):
                    ax.text(j, i, f"{pv.iat[i, j]:.0%}", ha="center", va="center", fontsize=8)
        fig.colorbar(im, ax=ax, label="Tỷ lệ lớp bất thường")
        ax.set_title("Điểm nóng: tỷ lệ lớp bất thường theo nhóm môn × năm học")
        luu(fig, "5_heatmap_diem_nong.png")
    return ra


def ghi_ket_qua(kq: pd.DataFrame, hs: pd.DataFrame, xh: pd.DataFrame, doc: pd.DataFrame,
                kc: pd.DataFrame | None, cfg: ch.CauHinh, thu_muc: Path) -> list[Path]:
    """Ghi các bảng kết quả ra CSV (UTF-8 có BOM để Excel đọc đúng tiếng Việt).

    Tham số:
        kq, hs, xh, doc: bảng kết quả, điểm nóng, xu hướng, độ dốc; kc: bảng kiểm chứng (có thể None);
        cfg: cấu hình; thu_muc: thư mục ghi.
    Trả về:
        Danh sách file đã ghi.
    Vì sao cần: bảng xếp hạng là đầu ra bắt buộc; bảng chi tiết là đầu vào cho Giải pháp 2.
    """
    thu_muc.mkdir(parents=True, exist_ok=True)
    bang = {
        "bang_xep_hang_lop.csv": kq.reindex(columns=list(COT_XEP_HANG)).rename(columns=COT_XEP_HANG),
        "chi_so_chi_tiet.csv": kq,
        "diem_nong_theo_mon.csv": hs,
        "xu_huong_nhom_mon.csv": xh,
        "do_doc_lam_phat.csv": doc,
        "tham_so.csv": pd.DataFrame(list(asdict(cfg).items()), columns=["tham_so", "gia_tri"]),
    }
    if kc is not None:
        bang["kiem_chung_mo_phong.csv"] = kc
    else:  # kết quả chính vừa được tạo lại → bảng kiểm chứng cũ không còn khớp, xóa để khỏi đọc nhầm
        (thu_muc / "kiem_chung_mo_phong.csv").unlink(missing_ok=True)
    ra = []
    for ten, b in bang.items():
        kiem_tra_khong_co_ma_sv(b, ten)
        p = thu_muc / ten
        b.to_csv(p, index=False, encoding="utf-8-sig")
        ra.append(p)
    return ra


def ghi_bao_cao(kq: pd.DataFrame, hs: pd.DataFrame, doc: pd.DataFrame, kc: pd.DataFrame | None,
                b: float, hinh: dict, thu_muc: Path) -> Path:
    """Ghi báo cáo tóm tắt Markdown (dành cho nhà trường – có mã lớp).

    Tham số:
        kq, hs, doc, kc: các bảng kết quả; b: hệ số năng lực nền; hinh: biểu đồ; thu_muc: nơi ghi.
    Trả về:
        Đường dẫn file báo cáo.
    Vì sao cần: đọc nhanh kết quả mà không phải mở CSV.
    """
    dem = kq["anomaly_type"].value_counts().rename_axis("nhan").reset_index(name="so_lop")
    dem["y_nghia"] = dem["nhan"].map(ch.Y_NGHIA_NHAN)
    el = kq[kq["anomaly_score"].notna()]
    bat = el[el["anomaly_type"].isin(ch.NHAN_BAT_THUONG)]
    dong = [
        "# Báo cáo Giải pháp 1 – Phát hiện lớp học phần có điểm bất thường", "",
        f"- Tổng số lớp: **{len(kq)}**; được chấm (đủ dữ liệu và có mốc): **{len(el)}**",
        f"- Lớp bất thường (lệch + có bằng chứng, hoặc phân phối biến dạng): **{len(bat)}** "
        f"({len(bat) / max(len(el), 1):.1%} số lớp được chấm)",
        f"- Đủ điều kiện hiệu chỉnh ở Giải pháp 2: **{int(kq['du_dieu_kien_hieu_chinh'].sum())}** lớp",
        f"- Hệ số năng lực nền b = {b:.2f} (b ≈ 1: năng lực nền giải thích điểm môn rất mạnh)", "",
        "## Số lớp theo nhãn", "", bang_markdown(dem), "",
        "## Top 15 lớp nghi vấn", "",
        bang_markdown(el.head(15)[["rank", "class_id", "course", "year", "sem", "n", "mean", "std", "a_rate",
                                   "anomaly_score", "anomaly_type", "explanation"]], so_le=2), "",
        "## Điểm nóng theo môn (≥ 2 lớp bất thường)", "",
        bang_markdown(hs[hs["so_lop_bat_thuong"] >= 2].head(15), so_le=2), "",
    ]
    if len(doc):
        dong += ["## Xu hướng tăng điểm dài hạn theo nhóm môn", "", bang_markdown(doc, so_le=4), ""]
    if kc is not None:
        dong += ["## Kiểm chứng bằng mô phỏng", "", bang_markdown(kc, so_le=2), ""]
    dong += ["## Biểu đồ", ""] + [f"![{ten}](charts/{ten})" for ten in hinh]
    p = thu_muc / "BaoCao_GiaiPhap1.md"
    p.write_text("\n".join(dong), encoding="utf-8")
    return p
