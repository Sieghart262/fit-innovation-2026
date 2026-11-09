"""Ghi kết quả ra file Markdown và lưu hình.

Mọi bảng/hình đều đi qua privacy.kiem_tra_an_toan() TRƯỚC khi ghi. Không có
đường nào khác để đưa số liệu vào báo cáo.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .privacy import kiem_tra_an_toan


def tao_hinh(tieu_de: str, nhan_x: str, nhan_y: str, kich_thuoc=(9, 4.8)):
    """Tạo một khung hình trống có tiêu đề và nhãn trục.

    Tham số:
        tieu_de: tiêu đề hình.
        nhan_x, nhan_y: nhãn trục ngang và dọc.
        kich_thuoc: (rộng, cao) tính bằng inch.
    Trả về:
        (fig, ax): fig là cả hình, ax là vùng vẽ bên trong.
    Vì sao cần: mọi hình có cùng kiểu dáng để báo cáo trông thống nhất.
    """
    fig, ax = plt.subplots(figsize=kich_thuoc)
    ax.set_title(tieu_de)
    ax.set_xlabel(nhan_x)
    ax.set_ylabel(nhan_y)
    ax.grid(alpha=0.3)
    return fig, ax


def _dinh_dang_o(gia_tri: object, ten_cot: str, so_le: int) -> str:
    """Đổi một ô thành chữ để đặt vào bảng Markdown.

    Quy ước:
        - Ô trống -> "–".
        - Cột bắt đầu bằng "ty_le" -> phần trăm (0.625 -> 62.5%).
        - Cột p_value -> "<0.001" nếu rất nhỏ.
        - Số nguyên -> có dấu phẩy ngăn cách hàng nghìn (38,342).
        - Số thực -> làm tròn so_le chữ số.
    Tham số:
        gia_tri: giá trị của ô.
        ten_cot: tên cột chứa ô.
        so_le: số chữ số thập phân.
    Trả về:
        Chuỗi đã định dạng.
    Vì sao cần: bảng dễ đọc hơn nhiều so với in thô "0.62500000001".
    """
    if gia_tri is None or (not isinstance(gia_tri, str) and pd.isna(gia_tri)):
        return "–"
    if isinstance(gia_tri, (bool, np.bool_)):  # kiểm tra bool TRƯỚC int (vì bool cũng là int)
        return "Có" if gia_tri else "Không"
    ten = str(ten_cot)
    if isinstance(gia_tri, (int, np.integer)):
        return f"{int(gia_tri):,}"
    if isinstance(gia_tri, (float, np.floating)):
        if ten.startswith("ty_le"):
            return f"{gia_tri * 100:.1f}%"
        if ten.startswith("p_value"):
            return "<0.001" if gia_tri < 0.001 else f"{gia_tri:.3f}"
        if np.isfinite(gia_tri) and float(gia_tri).is_integer():
            # pandas hay biến số nguyên thành số thực khi cột lẫn kiểu (877 -> 877.0)
            return f"{int(gia_tri):,}"
        return f"{gia_tri:.{so_le}f}"
    return str(gia_tri).replace("|", "\\|")  # "|" là ký tự kẻ cột của Markdown


def bang_markdown(bang: pd.DataFrame, so_le: int = 3) -> str:
    """Chuyển một DataFrame thành bảng Markdown.

    Tham số:
        bang: bảng cần chuyển (chỉ mục sẽ bị bỏ – hãy reset_index trước nếu cần).
        so_le: số chữ số thập phân.
    Trả về:
        Chuỗi Markdown.
    Vì sao cần: tự viết để không phải cài thêm thư viện "tabulate".
    """
    cot = [str(c) for c in bang.columns]
    dong = ["| " + " | ".join(cot) + " |", "|" + "|".join(["---"] * len(cot)) + "|"]
    for hang in bang.itertuples(index=False, name=None):
        dong.append("| " + " | ".join(_dinh_dang_o(v, c, so_le) for v, c in zip(hang, cot)) + " |")
    return "\n".join(dong)


class BaoCao:
    """Gom các phần (tiêu đề, đoạn văn, bảng, hình) rồi ghi ra một file Markdown."""

    def __init__(self, thu_muc_hinh: Path):
        """Khởi tạo báo cáo rỗng.

        Tham số:
            thu_muc_hinh: thư mục lưu hình (tạo mới nếu chưa có).
        Vì sao cần: báo cáo và hình phải đi cùng nhau để file .md hiển thị được hình.
        """
        self._dong: list[str] = []
        self._thu_muc_hinh = thu_muc_hinh
        self._thu_muc_hinh.mkdir(parents=True, exist_ok=True)
        self.so_nhom_da_an = 0  # tổng số nhóm < 5 người đã bị ẩn, ghi ở cuối báo cáo

    def tieu_de(self, chu: str, cap: int = 2) -> None:
        """Thêm tiêu đề Markdown (cấp 1 = "#", cấp 2 = "##"...).

        Tham số:
            chu: nội dung tiêu đề.
            cap: cấp tiêu đề.
        Vì sao cần: chia báo cáo thành các mục theo 4 yêu cầu EDA.
        """
        self._dong += [f"{'#' * cap} {chu}", ""]

    def doan(self, chu: str) -> None:
        """Thêm một đoạn văn.

        Tham số:
            chu: nội dung (được dùng cú pháp Markdown).
        Vì sao cần: giải thích ý nghĩa bảng/hình cho người đọc.
        """
        self._dong += [chu, ""]

    def bang(self, bang: pd.DataFrame, ten_bang: str, cot_dem: str | None = None,
             ly_do_khong_dem: str | None = None, so_le: int = 3, toi_da_dong: int = 40) -> None:
        """Kiểm tra riêng tư rồi thêm bảng vào báo cáo.

        Tham số:
            bang: bảng cần thêm.
            ten_bang: tên bảng (hiện trong thông báo lỗi nếu bị chặn).
            cot_dem / ly_do_khong_dem: xem privacy.kiem_tra_an_toan().
            so_le: số chữ số thập phân.
            toi_da_dong: chỉ in tối đa bao nhiêu dòng (bảng dài sẽ bị cắt, có ghi chú).
        Vì sao cần: đây là cửa duy nhất để bảng vào báo cáo → luôn được kiểm tra.
        """
        if any(ten is not None for ten in bang.index.names):
            bang = bang.reset_index()  # chỉ mục có tên (vd "Năm học") -> đưa thành cột
        else:
            bang = bang.reset_index(drop=True)  # chỉ mục chỉ là số thứ tự -> bỏ
        kiem_tra_an_toan(bang, ten_bang, cot_dem, ly_do_khong_dem)
        self._dong += [bang_markdown(bang.head(toi_da_dong), so_le), ""]
        if len(bang) > toi_da_dong:
            self._dong += [f"_(Chỉ hiện {toi_da_dong}/{len(bang)} dòng.)_", ""]

    def ghi_an_nhom(self, so_nhom: int) -> None:
        """Ghi chú số nhóm < 5 người đã bị ẩn khỏi bảng/hình ngay phía trên.

        Tham số:
            so_nhom: số nhóm bị ẩn (từ privacy.loc_nhom_nho).
        Vì sao cần: minh bạch – người đọc biết bảng không đầy đủ và vì sao.
        """
        if so_nhom:
            self.so_nhom_da_an += so_nhom
            self._dong += [f"_Đã ẩn {so_nhom} nhóm có dưới 5 người (quy tắc riêng tư)._", ""]

    def hinh(self, fig, ten_file: str, chu_thich: str, du_lieu_nguon: pd.DataFrame,
             cot_dem: str | None = None, ly_do_khong_dem: str | None = None) -> None:
        """Kiểm tra riêng tư dữ liệu nguồn, lưu hình PNG và chèn vào báo cáo.

        Tham số:
            fig: hình matplotlib.
            ten_file: tên file PNG (lưu trong thư mục hình).
            chu_thich: dòng mô tả dưới hình.
            du_lieu_nguon: bảng đã dùng để vẽ – được kiểm tra như một bảng thường.
            cot_dem / ly_do_khong_dem: xem privacy.kiem_tra_an_toan().
        Vì sao cần: hình cũng là output; vẽ từ dữ liệu chưa kiểm tra thì có thể lộ
        thông tin dù không có con số nào được in ra.
        """
        try:
            kiem_tra_an_toan(du_lieu_nguon, f"nguồn của hình {ten_file}", cot_dem, ly_do_khong_dem)
            fig.savefig(self._thu_muc_hinh / ten_file, dpi=120, bbox_inches="tight")
        finally:
            plt.close(fig)  # luôn đóng hình để giải phóng bộ nhớ, kể cả khi bị chặn
        self._dong += [f"![{chu_thich}]({self._thu_muc_hinh.name}/{ten_file})", "",
                       f"*{chu_thich}*", ""]

    def ghi(self, duong_dan: Path) -> None:
        """Ghi toàn bộ báo cáo ra file Markdown (UTF-8).

        Tham số:
            duong_dan: đường dẫn file .md.
        Vì sao cần: lưu kết quả để đọc lại, đưa vào báo cáo kỹ thuật sau này.
        """
        duong_dan.parent.mkdir(parents=True, exist_ok=True)
        duong_dan.write_text("\n".join(self._dong), encoding="utf-8")
