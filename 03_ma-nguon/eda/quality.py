"""Yêu cầu 1 – Chất lượng dữ liệu.

Trả lời các câu hỏi: dữ liệu có đúng như BTC mô tả không? Thiếu ở đâu?
Điểm 0 nằm ở đâu? Không hiểu dữ liệu "bẩn" thế nào thì mọi thuật toán phía sau
(Anomaly Score, TCI) đều có thể sai mà không biết.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cf
from .load import chuan_hoa_chu
from .report import tao_hinh


def _dong(chi_so: str, ky_vong: object, thuc_te: object) -> dict:
    """Tạo một dòng cho bảng đối chiếu "mô tả vs thực tế".

    Tham số:
        chi_so: tên chỉ số (vd "Số dòng").
        ky_vong: con số trong file mô tả của BTC.
        thuc_te: con số đếm được từ dữ liệu.
    Trả về:
        dict có 4 khóa: chi_so, theo_mo_ta, thuc_te, khop.
    Vì sao cần: viết gọn bảng đối chiếu ở hàm bên dưới.
    """
    return {"chi_so": chi_so, "theo_mo_ta": ky_vong, "thuc_te": thuc_te,
            "khop": "✅" if ky_vong == thuc_te else "❌"}


def doi_chieu_kich_thuoc(bang: pd.DataFrame, thong_tin: dict,
                         tkb: pd.DataFrame | None) -> pd.DataFrame:
    """So số dòng, số cột, số SV/lớp/môn... với con số BTC ghi trong mô tả.

    Tham số:
        bang: bảng điểm đã xử lý.
        thong_tin: dict từ load.doc_du_lieu_diem (cần "so_cot_goc").
        tkb: bảng thời khóa biểu hoặc None.
    Trả về:
        Bảng: chi_so | theo_mo_ta | thuc_te | khop.
    Vì sao cần: nếu số liệu lệch (vd thiếu dòng khi đọc file), phải biết ngay
    trước khi phân tích; đây cũng là bằng chứng "đã kiểm tra dữ liệu" cho báo cáo.
    """
    kv = cf.MO_TA_KY_VONG
    dong = [
        _dong("Số dòng (lượt điểm)", kv["so_dong"], len(bang)),
        _dong("Số cột", kv["so_cot"], thong_tin["so_cot_goc"]),
        _dong("Số sinh viên", kv["so_sv"], bang[cf.COT_MA_SV].nunique()),
        _dong("Số lớp học phần", kv["so_lop"], bang[cf.COT_MA_LOP].nunique()),
        _dong("Số môn", kv["so_mon"], bang[cf.COT_MA_MON].nunique()),
        _dong("Số dòng đồ án/TT/KL", kv["so_dong_do_an"], int(bang[cf.COT_DO_AN].sum())),
        _dong("Số dòng lớp EP", kv["so_dong_ep"], int(bang[cf.COT_EP].sum())),
        _dong("Số dòng học kỳ 3", kv["so_dong_hoc_ky_3"], int((bang[cf.COT_HOC_KY] == 3).sum())),
    ]
    if tkb is not None:
        dong += [
            _dong("TKB – số dòng", kv["tkb_so_dong"], len(tkb)),
            _dong("TKB – số cột", kv["tkb_so_cot"], tkb.shape[1]),
            _dong("TKB – số Mã LHP", kv["tkb_so_lop"],
                  tkb[cf.COT_TKB_MA_LHP].nunique() if cf.COT_TKB_MA_LHP in tkb.columns else "không có cột"),
        ]
    return pd.DataFrame(dong)


def _sai_dinh_dang(cot: pd.Series, mau: str) -> pd.Series:
    """True ở ô CÓ giá trị nhưng không khớp mẫu định dạng (ô trống không tính).

    Tham số:
        cot: cột chữ.
        mau: biểu thức chính quy (phải khớp TOÀN BỘ ô, vd "M\\d{3}").
    Trả về:
        Cột True/False.
    """
    chu = cot.dropna().map(chuan_hoa_chu)  # NFC: "KH-khác" có thể được lưu theo 2 kiểu Unicode
    sai = ~chu.str.fullmatch(mau)
    return sai.reindex(cot.index, fill_value=False)


def kiem_tra_loi_theo_cot(bang: pd.DataFrame, thong_tin: dict) -> pd.DataFrame:
    """Đếm lỗi của TỪNG cột trong 19 cột, theo từng loại lỗi.

    Các loại lỗi (chỉ áp dụng loại nào hợp với cột đó):
        - trống ở cột bắt buộc (config.COT_KHONG_DUOC_TRONG);
        - sai định dạng mã/văn bản (config.DINH_DANG), riêng Năm học còn phải
          có năm sau = năm trước + 1;
        - chữ thay vì số, và số ngoài khoảng cho phép (config.KHOANG_HOP_LE);
        - giá trị lạ ở cột Có/Không;
        - lớp lẫn nhiều năm/kỳ/môn; sĩ số ghi ≠ số dòng; trùng cặp (lớp, SV);
        - tổng cơ cấu trọng số ≠ 100.
    Mỗi ô lỗi chỉ được đếm vào MỘT loại: ô trống không tính là sai định dạng,
    ô chữ không tính là ngoài khoảng, lớp có sĩ số là chữ không tính là lệch sĩ số.
    Tham số:
        bang: bảng điểm đã xử lý.
        thong_tin: dict từ load.doc_du_lieu_diem (cần "o_loi", "o_trong").
    Trả về:
        Bảng: cot | loai_loi | don_vi | so_luong – đủ 19 cột, kể cả loại lỗi bằng 0,
        để người đọc thấy rõ cột nào ĐÃ được kiểm tra.
    Vì sao cần: số 0 chỉ có nghĩa khi biết chắc đã kiểm tra. Ô lỗi bị coi là
    trống sẽ âm thầm làm sai thống kê → phải biết trước khi tính Anomaly Score.
    """
    o_loi, o_trong = thong_tin["o_loi"], thong_tin["o_trong"]
    dong: list[dict] = []

    def them(cot, loai, so, don_vi="ô"):
        dong.append({"cot": cot, "loai_loi": loai, "don_vi": don_vi, "so_luong": int(so)})

    for cot in cf.COT_BAT_BUOC:
        if cot in cf.COT_KHONG_DUOC_TRONG:
            them(cot, cf.LOI_TRONG, o_trong[cot])
        if cot in cf.DINH_DANG:
            sai = _sai_dinh_dang(bang[cot], cf.DINH_DANG[cot])
            if cot == cf.COT_NAM_HOC:  # "2021-2023" đúng mẫu nhưng sai: năm sau phải = năm trước + 1
                hai_nam = bang[cot].str.extract(r"^(\d{4})-(\d{4})$").astype(float)
                sai |= (hai_nam[1] - hai_nam[0]).ne(1) & hai_nam[0].notna()
            them(cot, cf.LOI_DINH_DANG, sai.sum())
        if cot in cf.KHOANG_HOP_LE:
            them(cot, cf.LOI_CHU, o_loi[cot])
            nho, lon, nguyen = cf.KHOANG_HOP_LE[cot]
            gt = bang[cot]
            ngoai = (gt < nho) | ((gt > lon) if lon is not None else False)
            if nguyen:
                ngoai |= gt.notna() & (gt % 1 != 0)  # vd Học kỳ = 1.5
            them(cot, cf.LOI_NGOAI, ngoai.sum())
        if cot in cf.COT_CO_KHONG:
            them(cot, cf.LOI_LA, o_loi[cot])

        if cot == cf.COT_MA_LOP:
            # nunique() bỏ qua ô trống; > 1 giá trị nghĩa là lớp bị "lẫn" nhiều năm/kỳ/môn
            so_gt = bang.groupby(cot)[[cf.COT_NAM_HOC, cf.COT_HOC_KY, cf.COT_MA_MON]].nunique()
            them(cot, cf.LOI_LAN, so_gt.gt(1).any(axis=1).sum(), "lớp")
        if cot == cf.COT_SI_SO:
            dem = bang.groupby(cf.COT_MA_LOP).size()
            ghi = bang.groupby(cf.COT_MA_LOP)[cot].first()
            # Chỉ so lớp có sĩ số đọc được – sĩ số là chữ đã tính ở lỗi "không đọc được".
            them(cot, cf.LOI_SI_SO, (ghi.notna() & (ghi != dem)).sum(), "lớp")
        if cot == cf.COT_MA_SV:
            # Bỏ dòng thiếu Mã SV: hai ô trống không phải là "cùng một SV" (đã tính ở lỗi trống).
            co_ma = bang.dropna(subset=[cf.COT_MA_LOP, cot])
            them(cot, cf.LOI_TRUNG, co_ma.duplicated([cf.COT_MA_LOP, cot]).sum(), "dòng thừa")
        if cot == cf.COT_TRONG_SO:
            ba_so = bang[cot].str.extract(r"^(\d+)/(\d+)/(\d+)$").astype(float)
            them(cot, cf.LOI_TONG, (ba_so.sum(axis=1, min_count=3) != 100)[ba_so[0].notna()].sum())
    return pd.DataFrame(dong)


def ty_le_trong_theo_nam(bang: pd.DataFrame) -> pd.DataFrame:
    """Tỷ lệ ô trống của từng cột điểm, chia theo năm học.

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        Bảng: Năm học | so_sv | so_luot | ty_le_trong_<cột> ...
    Vì sao cần: mô tả nói 2019-2020 thiếu CC/KTTX, 2025-2026 thiếu Thi. Bảng này cho
    biết chính xác thiếu bao nhiêu → quyết định năm nào dùng được cho từng giải pháp.
    """
    # isna() biến bảng thành True/False; trung bình của True/False = tỷ lệ True.
    trong = bang[cf.COT_DIEM].isna().groupby(bang[cf.COT_NAM_HOC]).mean()
    trong.columns = [f"ty_le_trong_{c}" for c in trong.columns]
    dem = bang.groupby(cf.COT_NAM_HOC).agg(so_sv=(cf.COT_MA_SV, "nunique"),
                                           so_luot=(cf.COT_MA_SV, "size"))
    return dem.join(trong).reset_index()


def ve_ty_le_trong(bang_trong: pd.DataFrame):
    """Vẽ đường tỷ lệ ô trống của các cột điểm qua các năm học.

    Tham số:
        bang_trong: kết quả của ty_le_trong_theo_nam().
    Trả về:
        Hình matplotlib (Figure).
    Vì sao cần: nhìn hình dễ thấy năm nào "thủng" dữ liệu hơn đọc bảng số.
    """
    fig, ax = tao_hinh("Tỷ lệ ô trống của các cột điểm theo năm học", "Năm học", "Tỷ lệ trống")
    for cot in [c for c in bang_trong.columns if c.startswith("ty_le_trong_")]:
        ax.plot(bang_trong[cf.COT_NAM_HOC], bang_trong[cot], marker="o",
                label=cot.replace("ty_le_trong_", ""))
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=30)
    return fig


def thong_ke_diem_0(bang: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Đếm điểm 0 và cho biết chúng nằm ở đâu.

    Tham số:
        bang: bảng điểm đã xử lý.
    Trả về:
        dict gồm 4 bảng:
            "theo_cot"  : mỗi cột điểm có bao nhiêu điểm 0, chiếm bao nhiêu % ô có điểm.
            "theo_nam"  : số và tỷ lệ HP = 0 theo năm học × loại lớp.
            "kieu_hp_0" : HP = 0 đi kèm Thi trống / Thi = 0 / Thi > 0.
            "theo_lop"  : bao nhiêu lớp có HP = 0, bao nhiêu lớp có trên 20% HP = 0.
    Vì sao cần: HP = 0 gồm cả SV vắng thi/bỏ học – không phản ánh năng lực.
    Nếu để lẫn vào, điểm TB lớp bị kéo xuống và σ bị phóng to → báo động giả
    "UNUSUALLY_STEEP". Phải biết điểm 0 nằm ở đâu để quyết định cách loại.
    """
    co_diem = bang[cf.COT_DIEM].notna().sum()
    bang_0 = (bang[cf.COT_DIEM] == 0).sum()
    theo_cot = pd.DataFrame({"cot": cf.COT_DIEM, "so_o_co_diem": co_diem.values,
                             "so_diem_0": bang_0.values})
    theo_cot["ty_le_diem_0"] = theo_cot["so_diem_0"] / theo_cot["so_o_co_diem"].replace(0, np.nan)

    co_hp = bang[bang[cf.COT_HP].notna()].copy()
    co_hp["_hp_0"] = co_hp[cf.COT_HP] == 0
    theo_nam = co_hp.groupby([cf.COT_NAM_HOC, "loai_lop"]).agg(
        so_sv=(cf.COT_MA_SV, "nunique"), so_luot=(cf.COT_HP, "size"),
        so_hp_0=("_hp_0", "sum"), ty_le_hp_0=("_hp_0", "mean"),
    ).reset_index()

    hp_0 = co_hp[co_hp["_hp_0"]]
    kieu = np.select(
        [hp_0[cf.COT_THI].isna(), hp_0[cf.COT_THI] == 0, hp_0[cf.COT_THI] > 0],
        ["HP=0, Thi trống", "HP=0, Thi = 0", "HP=0, Thi > 0"], default="Khác",
    )
    kieu_hp_0 = (hp_0.assign(kieu=kieu).groupby("kieu")
                 .agg(so_sv=(cf.COT_MA_SV, "nunique"), so_luot=(cf.COT_MA_SV, "size"))
                 .reset_index())

    ty_le_0_lop = co_hp.groupby(cf.COT_MA_LOP)["_hp_0"].mean()
    theo_lop = pd.DataFrame([
        {"chi_so": "Số lớp có điểm HP", "gia_tri": int(ty_le_0_lop.size)},
        {"chi_so": "Số lớp có ít nhất 1 HP = 0", "gia_tri": int((ty_le_0_lop > 0).sum())},
        {"chi_so": "Số lớp có trên 20% HP = 0", "gia_tri": int((ty_le_0_lop > 0.2).sum())},
    ])
    return {"theo_cot": theo_cot, "theo_nam": theo_nam, "kieu_hp_0": kieu_hp_0, "theo_lop": theo_lop}
