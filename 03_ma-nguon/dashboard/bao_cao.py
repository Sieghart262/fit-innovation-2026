"""Tạo file tải về cho một lần phân tích: báo cáo HTML đầy đủ và gói ZIP mọi file kết quả.

Báo cáo HTML là MỘT file tự chứa (biểu đồ nhúng sẵn, không cần Internet), mở bằng trình duyệt
bất kỳ, in ra PDF được. Nội dung theo đúng thứ tự dashboard: tổng quan → lớp học phần → hiệu
chỉnh điểm → xếp mức sinh viên, có lời giải thích. Đây là tài liệu nội bộ của nhà trường: có
mã lớp, nhưng không có danh sách từng sinh viên (danh sách đó nằm trong gói ZIP).
"""

from __future__ import annotations

import base64
import html
import io
import zipfile
from pathlib import Path

import pandas as pd

import giao_dien as gd
import kho_ket_qua as kho
from gp1 import cau_hinh as ch1
from gp3 import cau_hinh as ch3

CSS = """
body { font-family: "Segoe UI", Arial, sans-serif; color: #1b1b1a; background: #f6f5f1; margin: 0; }
main { max-width: 1040px; margin: 0 auto; padding: 32px 28px 60px; background: #ffffff; }
h1 { font-size: 26px; margin: 0 0 4px; } h2 { font-size: 20px; margin: 34px 0 10px; border-bottom: 1px solid #e1e0d9; padding-bottom: 6px; }
h3 { font-size: 16px; margin: 22px 0 8px; }
.phu { color: #52514e; font-size: 14px; margin-bottom: 18px; }
.noi-bo { display: inline-block; background: #fbe3e3; color: #9c2323; border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
.the { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 14px 0 6px; }
.the div { border: 1px solid #e1e0d9; border-radius: 10px; padding: 10px 12px; }
.the .n { color: #52514e; font-size: 13px; } .the .g { font-size: 24px; font-weight: 700; }
.tom-tat { border-left: 4px solid #1c5cab; background: #f6f9fe; padding: 10px 14px; border-radius: 6px; margin: 10px 0; }
table { border-collapse: collapse; width: 100%; font-size: 13px; margin: 8px 0 14px; }
th, td { border: 1px solid #e1e0d9; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #f3f2ee; font-weight: 600; }
td.so, th.so { text-align: right; font-variant-numeric: tabular-nums; }
img { max-width: 100%; border: 1px solid #e1e0d9; border-radius: 6px; margin: 6px 0 14px; }
.ghi-chu { color: #52514e; font-size: 13px; }
@media print { body { background: #fff; } main { padding: 0; } h2 { page-break-before: auto; } }
"""


def _bang(df: pd.DataFrame, cot_so: tuple = ()) -> str:
    """Bảng HTML đơn giản (đã thoát ký tự), cột trong cot_so canh phải."""
    dau = "".join(f'<th class="{"so" if c in cot_so else ""}">{html.escape(str(c))}</th>' for c in df.columns)
    dong = []
    for r in df.itertuples(index=False):
        o = "".join(f'<td class="{"so" if c in cot_so else ""}">{html.escape("" if pd.isna(v) else str(v))}</td>'
                    for c, v in zip(df.columns, r))
        dong.append(f"<tr>{o}</tr>")
    return f"<table><thead><tr>{dau}</tr></thead><tbody>{''.join(dong)}</tbody></table>"


def _hinh(p: Path, chu_thich: str) -> str:
    """Nhúng một ảnh PNG vào HTML (base64) kèm chú thích."""
    if not p.exists():
        return ""
    ma = base64.b64encode(p.read_bytes()).decode("ascii")
    return f'<img alt="{html.escape(chu_thich)}" src="data:image/png;base64,{ma}"><div class="ghi-chu">{html.escape(chu_thich)}</div>'


def _the(cac_the: list[tuple[str, str]]) -> str:
    """Hàng thẻ số liệu."""
    return '<div class="the">' + "".join(f'<div><div class="n">{html.escape(n)}</div><div class="g">{html.escape(g)}</div></div>'
                                         for n, g in cac_the) + "</div>"


def tao_bao_cao_html(thu_muc: Path) -> str:
    """Tạo báo cáo HTML đầy đủ cho một bộ kết quả (thư mục có gp1/, gp2/, gp3/).

    Tham số:
        thu_muc: thư mục kết quả (đang dùng hoặc một mục lịch sử).
    Trả về:
        Chuỗi HTML hoàn chỉnh.
    Vì sao cần: nhà trường tải về một file duy nhất, đủ biểu đồ và lời giải thích như trên dashboard,
    để lưu trữ, gửi đi hoặc in ra.
    """
    tt = kho.doc_thong_tin(thu_muc) or {}
    lop = pd.read_csv(thu_muc / "gp1" / "chi_so_chi_tiet.csv", encoding="utf-8-sig")
    hc = pd.read_csv(thu_muc / "gp2" / "hieu_chinh_theo_lop.csv", encoding="utf-8-sig")
    sv = pd.read_csv(thu_muc / "gp3" / "phan_loai_sinh_vien.csv", encoding="utf-8-sig")
    cot_dc = "Số điểm bị trừ (âm = được cộng)" if "Số điểm bị trừ (âm = được cộng)" in hc.columns else hc.columns[-1]
    sua = hc[hc[cot_dc].ne(0)]
    co_tci = sv["TCI"].notna()
    doi = sv["Thay đổi mức"].ne("Giữ nguyên")
    bat = lop["anomaly_type"].isin(ch1.NHAN_BAT_THUONG)
    thoi_gian = pd.to_datetime(tt.get("thoi_gian")).strftime("%H:%M ngày %d/%m/%Y") if tt.get("thoi_gian") else "–"

    p = [f"<h1>Báo cáo phân tích điểm và năng lực thực chất</h1>",
         f'<div class="phu">Dữ liệu: <b>{html.escape(str(tt.get("ten", "–")))}</b> · phân tích lúc {thoi_gian} · '
         f'{html.escape(str(tt.get("cach_tao", "")))} &nbsp; <span class="noi-bo">Tài liệu nội bộ nhà trường</span></div>']

    # --- Tổng quan ---
    p += ["<h2>1. Tổng quan</h2>",
          f'<div class="tom-tat">Trong <b>{gd.so(co_tci.sum())}</b> sinh viên được xếp mức, có <b>{gd.so(doi.sum())}</b> '
          f'sinh viên đổi mức sau khi hiệu chỉnh điểm: {gd.so(sv["Thay đổi mức"].eq("Lên mức").sum())} lên mức, '
          f'{gd.so(sv["Thay đổi mức"].eq("Xuống mức").sum())} xuống mức.</div>',
          _the([("Sinh viên được xếp mức", gd.so(co_tci.sum())), ("Lớp có dấu hiệu bất thường", gd.so(bat.sum())),
                ("Lớp được hiệu chỉnh điểm", gd.so(len(sua))), ("Sinh viên đổi mức", gd.so(doi.sum()))])]
    muc = pd.DataFrame({"Mức": ch3.THU_TU_MUC + [ch3.CHUA_DU_DU_LIEU]})
    muc["Ý nghĩa"] = muc["Mức"].map(lambda m: f"{gd.MUC_VIET[m][0]} ({gd.MUC_VIET[m][1]})")
    muc["Trước hiệu chỉnh"] = muc["Mức"].map(sv["Mức theo GPA danh nghĩa"].value_counts()).fillna(0).astype(int).map(gd.so)
    muc["Sau hiệu chỉnh (TCI)"] = muc["Mức"].map(sv["Mức theo TCI"].value_counts()).fillna(0).astype(int).map(gd.so)
    p += ["<h3>Số sinh viên ở mỗi mức năng lực</h3>", _bang(muc, ("Trước hiệu chỉnh", "Sau hiệu chỉnh (TCI)")),
          _hinh(thu_muc / "gp3" / "charts" / "1_so_sv_theo_muc.png", "Số sinh viên theo mức: trước và sau hiệu chỉnh"),
          _hinh(thu_muc / "gp3" / "charts" / "2_phan_phoi_gpa_tci.png", "Phân phối GPA danh nghĩa và TCI (thang 4)")]
    mt = pd.crosstab(sv["Mức theo GPA danh nghĩa"], sv["Mức theo TCI"])
    chuyen = [(a, b, int(mt.loc[a, b])) for a in mt.index for b in mt.columns if a != b and mt.loc[a, b] > 0]
    if chuyen:
        bang = pd.DataFrame(sorted(chuyen, key=lambda x: -x[2]), columns=["Từ mức", "Sang mức", "Số sinh viên"])
        p += ["<h3>Sinh viên đổi mức như thế nào</h3>", _bang(bang, ("Số sinh viên",))]

    # --- Lớp học phần ---
    dem = lop["anomaly_type"].value_counts()
    ket_luan = pd.DataFrame({"Kết luận": [gd.TEN_NHAN[n] for n in gd.NHAN_VIET],
                             "Số lớp": [gd.so(int(dem.get(n, 0))) for n in gd.NHAN_VIET],
                             "Ý nghĩa": [gd.GIAI_THICH_NHAN[n] for n in gd.NHAN_VIET]})
    p += ["<h2>2. Lớp học phần (Giải pháp 1)</h2>",
          f'<div class="tom-tat"><b>{gd.so(bat.sum())}</b> trên {gd.so(len(lop))} lớp học phần có dấu hiệu bất thường. '
          "Một lớp chỉ bị coi là bất thường khi vừa lệch so với các lớp tương đương (cùng môn hoặc cùng nhóm môn, "
          "cùng cơ cấu điểm, cách nhau không quá 1 năm học) vừa có bằng chứng do cách chấm.</div>",
          _bang(ket_luan, ("Số lớp",))]
    ds = lop[bat].sort_values("anomaly_score", ascending=False)
    if len(ds):
        bang = pd.DataFrame({"Mã lớp": ds["class_id"], "Mã môn": ds["course"], "Năm học": ds["year"],
                             "Số SV": ds["n_sv"].map(lambda v: gd.so(v)), "Kết luận": ds["anomaly_type"].map(gd.TEN_NHAN),
                             "Mức độ bất thường": ds["anomaly_score"].map(lambda v: gd.so(v, 2)),
                             "Lý do": ds["explanation"]})
        p += ["<h3>Danh sách lớp có dấu hiệu bất thường và lý do</h3>", _bang(bang, ("Số SV", "Mức độ bất thường"))]
    for ten, chu in [("1_phan_phoi_anomaly_score.png", "Phân phối mức độ bất thường của các lớp"),
                     ("3_top20_lop_nghi_van.png", "20 lớp có mức độ bất thường cao nhất"),
                     ("4_phan_phoi_lop_tieu_bieu.png", "Phân phối điểm của một số lớp tiêu biểu so với các lớp tương đương"),
                     ("5_heatmap_diem_nong.png", "Tỷ lệ lớp bất thường theo nhóm môn và năm học")]:
        p.append(_hinh(thu_muc / "gp1" / "charts" / ten, chu))

    # --- Hiệu chỉnh ---
    p += ["<h2>3. Hiệu chỉnh điểm (Giải pháp 2)</h2>",
          f'<div class="tom-tat"><b>{gd.so(len(sua))}</b> lớp được hiệu chỉnh: {gd.so((sua[cot_dc] > 0).sum())} lớp chấm dễ bị trừ bớt, '
          f'{gd.so((sua[cot_dc] < 0).sum())} lớp chấm khắt khe được cộng thêm. Mọi sinh viên trong lớp được cộng hoặc trừ cùng '
          "một mức nên thứ hạng trong lớp không đổi. Công thức: Điểm mới = Điểm cũ − (1 − α) × Δ, mỗi lớp không quá 2 điểm.</div>"]
    if len(sua):
        bang = pd.DataFrame({"Mã lớp": sua["Mã lớp HP"], "Mã môn": sua["Mã môn"], "Năm học": sua["Năm học"],
                             "Kết luận": sua["Nhãn GP1"].map(gd.TEN_NHAN),
                             "Điểm TB lớp": sua["ĐTB lớp"].map(lambda v: gd.so(v, 2)),
                             "Điểm TB các lớp tương đương": sua["ĐTB mốc"].map(lambda v: gd.so(v, 2)),
                             "Điều chỉnh cho cả lớp": (-sua[cot_dc]).map(lambda v: ("+" if v > 0 else "−") + gd.so(abs(v), 2))})
        p.append(_bang(bang, ("Điểm TB lớp", "Điểm TB các lớp tương đương", "Điều chỉnh cho cả lớp")))
    p += [_hinh(thu_muc / "gp2" / "charts" / "2_muc_hieu_chinh_lop.png", "Mức cộng/trừ của từng lớp được hiệu chỉnh"),
          _hinh(thu_muc / "gp2" / "charts" / "1_gpa_truoc_sau.png", "Phân phối GPA hệ 10 trước và sau hiệu chỉnh")]

    # --- Ghi chú ---
    p += ["<h2>4. Ghi chú</h2>", '<ul class="ghi-chu">',
          "<li>TCI tính từ điểm đã hiệu chỉnh, quy đổi thang 4 theo bảng NEU, trọng số theo tín chỉ; mỗi môn lấy lần học điểm cao nhất.</li>",
          "<li>Lượt vắng thi (điểm 0, không có điểm thi) không được tính. Sinh viên học dưới 3 môn có độ tin cậy thấp.</li>",
          "<li>Danh sách xếp mức của từng sinh viên kèm lý do nằm trong gói ZIP tải từ dashboard (file gp3/phan_loai_sinh_vien.csv).</li>",
          "</ul>"]
    return (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>Báo cáo phân tích – {html.escape(str(tt.get('ten', '')))}</title><style>{CSS}</style></head>"
            f"<body><main>{''.join(p)}</main></body></html>")


def nen_zip(thu_muc: Path) -> bytes:
    """Gói mọi file của một bộ kết quả (CSV, biểu đồ, báo cáo Markdown, thông tin, file điểm đầu vào) thành ZIP."""
    bo_nho = io.BytesIO()
    with zipfile.ZipFile(bo_nho, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(thu_muc.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(thu_muc).as_posix())
        z.writestr("bao_cao.html", tao_bao_cao_html(thu_muc))
    return bo_nho.getvalue()
