"""Chạy toàn bộ bước khám phá dữ liệu (EDA) và ghi báo cáo.

Cách chạy (từ thư mục gốc dự án):
    .venv\\Scripts\\python.exe 03_ma-nguon\\run_eda.py

Kết quả:
    02_phan-tich/02-ket-qua-eda.md   – báo cáo (chỉ số liệu tổng hợp)
    02_phan-tich/hinh/*.png          – biểu đồ

Màn hình chỉ in tiến độ, KHÔNG in dữ liệu.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from eda import baseline, config as cf, distribution, hypotheses, quality
from eda.load import LoiDuLieu, doc_du_lieu_diem, doc_thoi_khoa_bieu
from eda.privacy import LoiRiengTu, loc_nhom_nho
from eda.report import BaoCao

# Lý do bỏ qua bước đếm người (bắt buộc ghi khi bảng không có "nhóm người").
LD_TOAN_BO = "Chỉ số tính trên toàn bộ dữ liệu, không chia nhóm người."
LD_DEM_LOP = "Đếm số lớp, không chứa điểm hay thông tin cá nhân."
LD_TUONG_QUAN = "Hệ số tương quan trên các lớp, mỗi lớp đã có ≥ 5 SV."


def doc_tham_so() -> argparse.Namespace:
    """Đọc tham số dòng lệnh (đường dẫn file vào/ra).

    Trả về:
        Đối tượng chứa du_lieu, tkb, bao_cao.
    Vì sao cần: mặc định dùng đường dẫn trong config.py, nhưng có thể chỉ sang file
    khác – ví dụ file dữ liệu giả lập để thử code mà không đụng dữ liệu thật.
    """
    p = argparse.ArgumentParser(description="EDA dữ liệu điểm FIT Innovation 2026")
    p.add_argument("--du-lieu", type=Path, default=cf.FILE_DIEM, help="Đường dẫn Du_lieu.csv")
    p.add_argument("--tkb", type=Path, default=cf.FILE_TKB, help="Đường dẫn Thoi_khoa_bieu.csv")
    p.add_argument("--bao-cao", type=Path, default=cf.FILE_BAO_CAO, help="File Markdown đầu ra")
    return p.parse_args()


def phan_mo_dau(bc: BaoCao, ten_file: str) -> None:
    """Viết phần đầu báo cáo: thời điểm chạy, quy tắc riêng tư, chú giải tên cột.

    Tham số:
        bc: báo cáo đang viết.
        ten_file: tên file dữ liệu đã đọc.
    Vì sao cần: người đọc (kể cả giám khảo) hiểu ngay các ký hiệu trong bảng.
    """
    bc.tieu_de("Kết quả khám phá dữ liệu (EDA)", 1)
    bc.doan(f"Chạy lúc {datetime.now():%d/%m/%Y %H:%M} trên file `{ten_file}`. "
            "Báo cáo chỉ chứa số liệu tổng hợp: không có Mã SV, mọi nhóm đều có ≥ 5 người.")
    bc.doan(
        "**Chú giải:** `n` / `so_sv` = số sinh viên khác nhau · `so_luot` = số dòng điểm · "
        "`tb` = trung bình · `sigma` = độ lệch chuẩn · `ty_le_A` = tỷ lệ HP ≥ 8,5 · "
        "`ty_le_hp_0` = tỷ lệ HP = 0 · `z` = số độ lệch chuẩn cách trung bình · "
        "`p_value` < 0,05 thường coi là khác biệt có ý nghĩa thống kê. "
        "Thống kê điểm lớp tính trên SV có HP > 0 (điểm 0 gồm cả vắng thi)."
    )


def muc_chat_luong(bc: BaoCao, bang, thong_tin: dict, tkb) -> None:
    """Viết mục 1 – Chất lượng dữ liệu.

    Tham số:
        bc: báo cáo; bang: bảng điểm; thong_tin: từ load; tkb: thời khóa biểu hoặc None.
    Vì sao cần: yêu cầu 1 của kế hoạch EDA.
    """
    bc.tieu_de("1. Chất lượng dữ liệu")
    bc.tieu_de("1.1 Đối chiếu với mô tả của BTC", 3)
    bc.bang(quality.doi_chieu_kich_thuoc(bang, thong_tin, tkb), "kích thước", ly_do_khong_dem=LD_TOAN_BO)
    bc.tieu_de("1.2 Lỗi theo từng cột (đủ 19 cột)", 3)
    loi = quality.kiem_tra_loi_theo_cot(bang, thong_tin)
    bc.doan(f"Tổng: **{int(loi['so_luong'].gt(0).sum())}** loại lỗi có xuất hiện trên "
            f"{len(loi)} phép kiểm tra. Số 0 = đã kiểm tra và không thấy lỗi. "
            f"Ô trống ở cột điểm, Khóa SV ({bang[cf.COT_KHOA_SV].isna().mean():.2%}) và "
            "Cơ cấu trọng số được mô tả cho phép nên không tính là lỗi.")
    bc.bang(loi, "lỗi theo cột", ly_do_khong_dem=LD_TOAN_BO, toi_da_dong=80)

    bc.tieu_de("1.3 Tỷ lệ ô trống theo năm học", 3)
    trong, an = loc_nhom_nho(quality.ty_le_trong_theo_nam(bang), "so_sv")
    bc.bang(trong, "ô trống theo năm", cot_dem="so_sv")
    bc.ghi_an_nhom(an)
    bc.hinh(quality.ve_ty_le_trong(trong), "01_ty_le_trong_theo_nam.png",
            "Tỷ lệ ô trống của các cột điểm theo năm học", trong, cot_dem="so_sv")

    bc.tieu_de("1.4 Điểm 0", 3)
    diem_0 = quality.thong_ke_diem_0(bang)
    bc.bang(diem_0["theo_cot"], "điểm 0 theo cột", ly_do_khong_dem=LD_TOAN_BO)
    theo_nam, an = loc_nhom_nho(diem_0["theo_nam"], "so_sv")
    bc.doan("HP = 0 theo năm học và loại lớp:")
    bc.bang(theo_nam, "điểm 0 theo năm", cot_dem="so_sv")
    bc.ghi_an_nhom(an)
    kieu, an = loc_nhom_nho(diem_0["kieu_hp_0"], "so_sv")
    bc.doan("HP = 0 đi kèm điểm Thi thế nào (gợi ý: HP=0 & Thi trống thường là vắng thi/bỏ học):")
    bc.bang(kieu, "kiểu điểm 0", cot_dem="so_sv")
    bc.ghi_an_nhom(an)
    bc.bang(diem_0["theo_lop"], "điểm 0 theo lớp", ly_do_khong_dem=LD_DEM_LOP)


def muc_phan_bo(bc: BaoCao, bang):
    """Viết mục 2 – Phân bố điểm. Trả về bảng lớp (≥ 5 SV) để dùng ở mục 3.

    Tham số:
        bc: báo cáo; bang: bảng điểm.
    Trả về:
        Bảng thống kê lớp đã lọc (≥ 5 SV).
    Vì sao cần: yêu cầu 2 của kế hoạch EDA.
    """
    bc.tieu_de("2. Phân bố điểm")
    bc.tieu_de("2.1 Phân bố điểm từng lượt (lớp thường)", 3)
    khoang = {}
    for ten, cot in [("HP", cf.COT_HP), ("KTTX", cf.COT_KTTX), ("Thi", cf.COT_THI)]:
        khoang[ten], an = loc_nhom_nho(distribution.dem_diem_theo_khoang(bang, cot), "so_sv")
        bc.ghi_an_nhom(an)
    bc.hinh(distribution.ve_cot_khoang({"HP": khoang["HP"]}, "Phân bố Điểm HP (lớp thường)"),
            "02_phan_bo_diem_hp.png", "Phân bố Điểm HP theo khoảng 0,5 điểm",
            khoang["HP"], cot_dem="so_sv")
    bc.hinh(distribution.ve_cot_khoang({"KTTX": khoang["KTTX"], "Thi": khoang["Thi"]},
                                       "So sánh phân bố KTTX và Thi (lớp thường)"),
            "03_kttx_vs_thi.png", "KTTX (GV tự chấm) so với Thi (2 GV chấm)",
            khoang["KTTX"], cot_dem="so_sv")

    lop = distribution.lop_du_lon(distribution.thong_ke_theo_lop(bang))
    lop_thuong = lop[lop["loai_lop"] == cf.LOAI_THUONG]

    bc.tieu_de("2.2 Chỉ số cấp lớp (lớp thường, ≥ 5 SV)", 3)
    bc.bang(distribution.mo_ta_chi_so_lop(lop_thuong), "mô tả chỉ số lớp", ly_do_khong_dem=LD_DEM_LOP)
    bc.hinh(distribution.ve_histogram_lop(lop_thuong, "tb", "Điểm TB của các lớp thường", "Điểm TB lớp"),
            "04_tb_lop.png", "Phân bố điểm TB lớp", lop_thuong, cot_dem="n")
    bc.hinh(distribution.ve_tb_va_sigma(lop), "05_tb_vs_sigma.png",
            "Điểm TB lớp và σ (góc phải-dưới: điểm cao và đồng đều)", lop, cot_dem="n")

    bc.tieu_de(f"2.3 Lớp có tỷ lệ A > {cf.NGUONG_TY_LE_A:.0%}", 3)
    vuot = distribution.dem_lop_vuot_nguong_A(lop)
    bc.bang(vuot["theo_loai"], "vượt ngưỡng theo loại", cot_dem="so_luot")
    bc.doan("Lớp thường theo năm học:")
    bc.bang(vuot["theo_nam"], "vượt ngưỡng theo năm", cot_dem="so_luot")
    bc.hinh(distribution.ve_histogram_lop(lop_thuong, "ty_le_A", "Tỷ lệ điểm A của các lớp thường",
                                          "Tỷ lệ A", duong_doc=cf.NGUONG_TY_LE_A),
            "06_ty_le_A_lop.png", "Phân bố tỷ lệ điểm A, vạch đỏ = ngưỡng 60%", lop_thuong, cot_dem="n")
    bc.doan("15 lớp thường có tỷ lệ A cao nhất (ứng viên cho kịch bản video demo):")
    bc.bang(distribution.top_lop(lop_thuong, "ty_le_A", tang_dan=False), "top tỷ lệ A", cot_dem="n")
    bc.doan("10 lớp thường có σ nhỏ nhất (tiêu chí σ → 0):")
    bc.bang(distribution.top_lop(lop_thuong, "sigma", tang_dan=True, so_dong=10), "top σ nhỏ", cot_dem="n")

    bc.tieu_de("2.4 Sĩ số lớp", 3)
    dem_si_so, mo_ta_si_so = distribution.phan_bo_si_so(bang)
    bc.bang(dem_si_so, "sĩ số", ly_do_khong_dem=LD_DEM_LOP)
    bc.bang(mo_ta_si_so, "mô tả sĩ số", ly_do_khong_dem=LD_DEM_LOP)
    bc.hinh(distribution.ve_si_so(dem_si_so), "07_si_so.png", "Số lớp theo sĩ số",
            dem_si_so, ly_do_khong_dem=LD_DEM_LOP)
    return lop


def muc_gia_thuyet(bc: BaoCao, bang, lop) -> None:
    """Viết mục 3 – Kiểm tra giả thuyết A (KTTX − Thi), B (giai đoạn), C (loại lớp).

    Tham số:
        bc: báo cáo; bang: bảng điểm; lop: bảng lớp (≥ 5 SV) từ mục 2.
    Vì sao cần: yêu cầu 3 của kế hoạch EDA.
    """
    bc.tieu_de("3. Kiểm tra giả thuyết")

    bc.tieu_de("3.1 Giả thuyết A – Chênh lệch KTTX − Thi theo lớp", 3)
    lop_chenh = hypotheses.chenh_lech_kttx_thi(bang)
    tt = hypotheses.tom_tat_chenh_lech(lop_chenh)
    bc.bang(tt["tong_quan"], "tổng quan chênh lệch", ly_do_khong_dem=LD_DEM_LOP)
    bc.bang(tt["theo_giai_doan"], "chênh lệch theo giai đoạn", cot_dem="so_luot")
    bc.doan("15 lớp có KTTX cao bất thường nhất so với các lớp khác cùng môn:")
    bc.bang(tt["top"], "top z chênh lệch", cot_dem="n")
    bc.bang(hypotheses.tuong_quan_chenh_va_ty_le_A(lop_chenh, lop), "tương quan",
            ly_do_khong_dem=LD_TUONG_QUAN)
    bc.hinh(hypotheses.ve_z_chenh(lop_chenh), "08_z_chenh_kttx_thi.png",
            "z-score chênh lệch KTTX − Thi; ngoài hai vạch đỏ là bất thường", lop_chenh, cot_dem="n")

    bc.tieu_de("3.2 Giả thuyết B – Trước và từ HK2 2021-22 (đổi trọng số)", 3)
    gd = hypotheses.so_sanh_giai_doan(bang)
    bc.bang(gd["tom_tat"], "tóm tắt giai đoạn", cot_dem="so_sv")
    bc.bang(gd["kiem_dinh"], "kiểm định giai đoạn", ly_do_khong_dem=LD_TOAN_BO)
    bc.doan("So sánh trên cùng một môn ở hai giai đoạn:")
    bc.bang(gd["theo_mon"], "so sánh cùng môn", ly_do_khong_dem=LD_DEM_LOP)
    ky, an = loc_nhom_nho(hypotheses.xu_huong_theo_ky(bang), "so_sv")
    bc.bang(ky.drop(columns="ky_so"), "xu hướng theo kỳ", cot_dem="so_sv")
    bc.ghi_an_nhom(an)
    bc.hinh(hypotheses.ve_xu_huong(ky), "09_xu_huong_theo_ky.png",
            "Điểm TB theo học kỳ; vạch đỏ = mốc đổi trọng số", ky, cot_dem="so_sv")
    cc, an = loc_nhom_nho(hypotheses.co_cau_trong_so(bang), "so_sv")
    bc.doan("Cơ cấu trọng số (suy ra) phổ biến nhất mỗi giai đoạn:")
    bc.bang(cc, "cơ cấu trọng số", cot_dem="so_sv")
    bc.ghi_an_nhom(an)

    bc.tieu_de("3.3 Giả thuyết C – Lớp EP, đồ án và lớp thường", 3)
    chi_so, kiem_dinh = hypotheses.so_sanh_loai_lop(bang)
    chi_so, an = loc_nhom_nho(chi_so, "so_sv")
    bc.bang(chi_so, "loại lớp", cot_dem="so_sv")
    bc.ghi_an_nhom(an)
    bc.bang(kiem_dinh, "kiểm định loại lớp", ly_do_khong_dem=LD_TOAN_BO)
    bc.hinh(hypotheses.ve_loai_lop(chi_so), "10_loai_lop.png",
            "Điểm TB và tỷ lệ A theo loại lớp", chi_so, cot_dem="so_sv")


def muc_nang_luc_nen(bc: BaoCao, bang) -> None:
    """Viết mục 4 – Số môn mỗi SV đã học (cơ sở cho năng lực nền).

    Tham số:
        bc: báo cáo; bang: bảng điểm.
    Vì sao cần: yêu cầu 4 của kế hoạch EDA.
    """
    bc.tieu_de("4. Năng lực nền – số môn mỗi sinh viên đã học")
    so_mon = baseline.so_mon_moi_sv(bang)  # có Mã SV – chỉ dùng nội bộ, không xuất
    bc.bang(baseline.mo_ta_so_mon(so_mon), "mô tả số môn",
            ly_do_khong_dem="Phân vị trên toàn bộ SV; không ghi min/max.")
    phan_bo, an = loc_nhom_nho(baseline.phan_bo_so_mon(so_mon), "so_sv")
    bc.bang(phan_bo, "phân bố số môn", cot_dem="so_sv")
    bc.ghi_an_nhom(an)
    bc.hinh(baseline.ve_so_mon(phan_bo), "11_so_mon_moi_sv.png", "Số SV theo số môn đã học",
            phan_bo, cot_dem="so_sv")
    bc.doan("Tỷ lệ SV và lượt điểm có đủ môn KHÁC để tính năng lực nền:")
    kha_thi, an = loc_nhom_nho(baseline.kha_thi_nang_luc_nen(bang, so_mon), "so_sv")
    bc.bang(kha_thi, "khả thi năng lực nền", cot_dem="so_sv")
    bc.ghi_an_nhom(an)
    theo_khoa, an = loc_nhom_nho(baseline.so_mon_theo_khoa_sv(bang, so_mon), "so_sv")
    bc.doan("Theo khóa tuyển sinh:")
    bc.bang(theo_khoa, "số môn theo khóa", cot_dem="so_sv")
    bc.ghi_an_nhom(an)


def main() -> None:
    """Chạy lần lượt 4 mục EDA và ghi báo cáo.

    Vì sao cần: một lệnh duy nhất cho ra toàn bộ kết quả, chạy lại được bất cứ lúc
    nào (vd khi BTC gửi dữ liệu mới).
    """
    try:  # để màn hình Windows hiện đúng tiếng Việt
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ts = doc_tham_so()
    bat_dau = time.perf_counter()

    print("[1/5] Đọc dữ liệu...")
    bang, thong_tin = doc_du_lieu_diem(ts.du_lieu)
    tkb = doc_thoi_khoa_bieu(ts.tkb)

    bc = BaoCao(ts.bao_cao.parent / cf.TEN_THU_MUC_HINH)
    phan_mo_dau(bc, ts.du_lieu.name)
    print("[2/5] Chất lượng dữ liệu...")
    muc_chat_luong(bc, bang, thong_tin, tkb)
    print("[3/5] Phân bố điểm...")
    lop = muc_phan_bo(bc, bang)
    print("[4/5] Kiểm tra giả thuyết...")
    muc_gia_thuyet(bc, bang, lop)
    print("[5/5] Năng lực nền...")
    muc_nang_luc_nen(bc, bang)

    giay = time.perf_counter() - bat_dau
    bc.tieu_de("Ghi chú cuối")
    bc.doan(f"Tổng số nhóm đã ẩn vì dưới 5 người: {bc.so_nhom_da_an}. "
            f"Thời gian chạy: {giay:.1f} giây cho {len(bang):,} dòng.")
    bc.ghi(ts.bao_cao)
    print(f"Xong sau {giay:.1f} giây. Báo cáo: {ts.bao_cao}")


if __name__ == "__main__":
    try:
        main()
    except LoiRiengTu as loi:
        print(f"DỪNG vì quy tắc riêng tư – chưa ghi báo cáo.\n{loi}")
        sys.exit(2)
    except LoiDuLieu as loi:
        print(f"Lỗi dữ liệu: {loi}")
        sys.exit(1)
