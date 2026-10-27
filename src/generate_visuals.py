"""Generate editable, data-grounded SVG documentation. No image dependencies.

Run after generate_demo: python -m src.generate_visuals
"""
from datetime import timedelta
from html import escape
import json
from pathlib import Path

from .models import timestamp

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
INK, MUTED, BLUE, GREEN, AMBER = "#263246", "#67758b", "#315deb", "#19705b", "#9d691c"


def text(x: float, y: float, value: object, size: int = 18, color: str = INK, weight: int = 400, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>'


def rect(x: float, y: float, width: float, height: float, fill: str = "#fff", stroke: str = "#dce3ee", radius: int = 12) -> str:
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def line(x1: float, y1: float, x2: float, y2: float, color: str = "#dce3ee", width: int = 2, dashed: bool = False, arrow: bool = False) -> str:
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"' + (' stroke-dasharray="6 5"' if dashed else '') + (' marker-end="url(#arrow)"' if arrow else '') + '/>'


def circle(x: float, y: float, radius: int = 5, color: str = BLUE) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>'


def label(x: float, y: float, value: str, color: str = BLUE, width: int = 220) -> str:
    return rect(x, y, width, 36, "#eef3ff", "none", 6) + text(x + 13, y + 25, value, 18, color, 650)


def document(filename: str, height: int, title: str, subtitle: str, body: list[str]) -> None:
    header = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{height}" viewBox="0 0 1440 {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 8 4 0 8" fill="none" stroke="#315deb" stroke-width="1.4"/></marker></defs>',
        '<style>text{font-family:Arial,"Malgun Gothic","Apple SD Gothic Neo",sans-serif}path{stroke-linecap:round}</style>',
        rect(0.5, 0.5, 1439, height - 1, "#f7f9fc", "#e3e8f1", 16),
        text(48, 40, "FASHION REVIEW / ENGINEERING NOTES", 13, BLUE, 650),
        text(48, 90, title, 34, INK, 700), text(48, 124, subtitle, 17, MUTED)]
    (ASSETS / filename).write_text("\n".join(header + body + ["</svg>"]) + "\n", encoding="utf-8")


def pipeline(product: dict, as_of: str) -> None:
    q, t = product["windows"]["7"]["quality"], product["windows"]["7"]["trend"]
    valid = [o for o in product["observations"] if o["count"] is not None]
    first, last = valid[0], valid[-1]
    cards = [
        ("01 / INPUT", "시점별 원본을 보존", [product["product_id"], f"{timestamp(first['at']).strftime('%m/%d %H:%M')} → {first['count']}건", f"{timestamp(last['at']).strftime('%m/%d %H:%M')} → {last['count']}건", "상품 정보와 관측값 분리"], "SYNTHETIC CSV"),
        ("02 / CONTRACT", "입력 계약을 검증", ["상품 식별 · 비음수 정수", "타임존을 KST로 정규화", "완전 중복 축약 · 충돌 거부", "결측값과 실제 0 구분"], "VALIDATED SNAPSHOTS"),
        ("03 / ANALYTICS", "실제 시간으로 비교", [f"변화량  {last['count']} − {first['count']} = +{t['delta']}", f"관측 기간  {q['span_hours']:g}h = {q['span_hours']/24:g}일", f"평균 속도  +{t['reviews_per_day']:g}건 / 일", f"7일 품질  {q['grade']}"], "TREND + QUALITY"),
        ("04 / SERVING", "근거와 함께 시각화", ["docs/data/demo.json", "기간 · 카테고리 · 검색", "상품별 변화 추이와 순위", "관측 품질 · 가상 실행 현황"], "STATIC BI / PAGES"),
    ]
    body = []
    for i, (kicker, title, details, foot) in enumerate(cards):
        x = 48 + i * 345
        body += [rect(x, 170, 309, 300), text(x + 22, 204, kicker, 14, BLUE, 650),
                 text(x + 22, 248, title, 24, INK, 650)]
        body += [text(x + 22, 292 + j * 34, detail, 17, INK if j == 0 else MUTED) for j, detail in enumerate(details)]
        body += [line(x + 22, 420, x + 287, 420), text(x + 22, 448, foot, 12, MUTED, 650)]
        if i < 3:
            body.append(line(x + 315, 320, x + 338, 320, BLUE, arrow=True))
    body += [rect(48, 500, 1344, 92, "#edf2ff", "none")]
    metrics = [("유효 관측", f"{q['snapshots']}회"), ("서로 다른 KST 날짜", f"{q['distinct_dates']}일"),
               ("실제 관측 기간", f"{q['span_hours']:g}h"), ("마지막 관측 이후", f"{q['age_hours']:g}h")]
    for i, (name, value) in enumerate(metrics):
        x = 72 + i * 336
        body += [text(x, 531, name, 16, MUTED), text(x, 569, value, 28, BLUE, 650)]
    body.append(text(48, 624, f"SYNTHETIC DATA · {product['product_id']} · 기준 {timestamp(as_of).strftime('%Y-%m-%d %H:%M')} KST · 속도는 실제 관측 구간의 평균", 14, MUTED))
    document("pipeline-walkthrough.svg", 648, "한 상품의 스냅샷이 분석 신호가 되기까지", "합성 상품 DEMO-013의 실제 계산값으로 따라가는 공개 데모의 실행 경로", body)


def quality(products: dict, as_of: str) -> None:
    end = timestamp(as_of)
    start = end - timedelta(days=7)
    x0, span = 330, 650
    def x(at: str) -> float:
        return round(x0 + (timestamp(at) - start).total_seconds() / (7 * 86400) * span, 2)
    body = [text(48, 178, "같은 7일 창, 다른 관측 근거", 20, INK, 650), text(1025, 178, "판정과 해석", 18, MUTED)]
    for i in range(8):
        xx = x0 + i * span / 7
        body += [line(xx, 212, xx, 602, "#e5eaf3", 1), text(xx, 203, "T" if i == 7 else f"T−{7-i}일", 13, MUTED, anchor="middle")]
    rows = [("DEMO-013", BLUE, "횟수와 날짜는 다릅니다", "13회 관측 → KST 날짜 7일"),
            ("DEMO-004", GREEN, "비교의 최소 조건 충족", "2일 · 36h · 최근 3h"),
            ("DEMO-005", AMBER, "최근성 기준 미달", "123h 경과 → 72h 초과"),
            ("DEMO-006", AMBER, "관측 기간과 날짜 부족", "최근 3h여도 1일 · 0h")]
    for i, (identifier, color, note, reason) in enumerate(rows):
        p = products[identifier]
        q = p["windows"]["7"]["quality"]
        yy = 255 + i * 98
        valid = [o for o in p["observations"] if o["count"] is not None and start <= timestamp(o["at"]) <= end]
        body += [text(48, yy - 5, identifier, 21, INK, 650), text(48, yy + 23, f"{q['snapshots']}회 / KST {q['distinct_dates']}일 / {q['span_hours']:g}h", 16, MUTED),
                 line(x0, yy, x0 + span, yy, "#dfe6f1", 3)]
        if len(valid) > 1:
            body.append(line(x(valid[0]["at"]), yy, x(valid[-1]["at"]), yy, color, 5))
        body.append(line(x(valid[-1]["at"]), yy, x0 + span, yy, color, 2, dashed=True))
        for observation in valid:
            body += [circle(x(observation["at"]), yy, 6, color)]
        body += [label(1025, yy - 28, q["grade"], color, 280), text(1025, yy + 35, note, 17, INK, 650), text(1025, yy + 59, reason, 15, MUTED)]
    body += [text(330, 623, "선: 최초~최종 유효 관측 기간     점: 유효 스냅샷     점선: 마지막 관측 이후", 15, MUTED)]
    rules = [("반복 관측", "날짜 ≥ 3 · 기간 ≥ 48h", "최근성 ≤ 72h", BLUE),
             ("비교 가능", "날짜 ≥ 2 · 기간 ≥ 24h", "최근성 ≤ 72h · 반복 관측 미달", GREEN),
             ("추가 관측 필요", "기간 · 날짜 · 최근성 중 기준 미달", "실패한 추출은 유효 관측에서 제외", AMBER)]
    for i, (name, rule, extra, color) in enumerate(rules):
        xx = 48 + i * 454
        body += [rect(xx, 649, 436, 116), text(xx + 20, 681, name, 21, color, 650),
                 text(xx + 20, 715, rule, 17), text(xx + 20, 743, extra, 16, MUTED)]
    body.append(text(48, 798, f"SYNTHETIC DATA · T = {end.strftime('%Y-%m-%d %H:%M')} KST · 운영상 비교 가능성 지표이며 통계적 신뢰도나 예측 정확도가 아닙니다.", 14, MUTED))
    document("observation-quality.svg", 824, "증가량 옆에 관측의 충분성을 함께 표시합니다", "실제 합성 관측 이력으로 비교한 날짜 수 · 관측 기간 · 최근성의 역할", body)


def extraction() -> None:
    body = []
    gates = [("01 / IDENTITY", "요청·응답 상품 일치", ["허용 도메인과 상품 경로", "요청 ID = 응답 ID", "다른 상품 응답은 거부"]),
             ("02 / PRODUCT", "Product 객체 확인", ["@type = Product", "Product URL의 식별 일치", "관계없는 객체는 채택하지 않음"]),
             ("03 / CANDIDATES", "유효 후보의 유일성", ["비음수 정수만 허용", "42, 42 → 유일한 값 42", "42, 43 → 모호한 값 거부"]),
             ("04 / ACCEPT", "검증된 값만 채택", ["42 → 검증된 리뷰 수", "0 → 유효한 실제 0", "None → 확인되지 않은 값"])]
    for i, (kicker, title, details) in enumerate(gates):
        xx = 48 + 348 * i
        body += [rect(xx, 174, 300, 218), text(xx + 22, 208, kicker, 13, BLUE, 650), text(xx + 22, 248, title, 22, INK, 650)]
        body += [text(xx + 22, 290 + j * 32, value, 17, MUTED) for j, value in enumerate(details)]
        if i < 3:
            body += [line(xx + 308, 279, xx + 340, 279, BLUE, arrow=True), line(xx + 150, 398, xx + 150, 445, AMBER, dashed=True)]
    body += [rect(48, 453, 1344, 82, "#fcf4e8", "#ebd8b8"),
             text(72, 486, "검증 실패 → NULL / 오류로 반환", 23, AMBER, 650),
             text(72, 516, "상품 불일치 · 잘못된 형식 · 후보 충돌을 0으로 대체하지 않습니다.", 18, MUTED),
             text(48, 575, "오프라인 JSON-LD 검증 계약의 설명도 · 42는 fixture 예시 값 · 실제 사이트 조회나 운영 DB 적재 결과가 아닙니다.", 15, MUTED)]
    document("review-validation.svg", 602, "상품 식별을 통과한 리뷰 수만 채택합니다", "__NEXT_DATA__ 추출 실패를 보완할 때도 JSON-LD의 임의 숫자를 채택하지 않는 검증 순서", body)


def scheduling() -> None:
    body = [rect(48, 174, 370, 352), text(72, 214, "선정에 고려한 조건", 23, INK, 650)]
    for i, value in enumerate(("관측 이력 없음 · 부족", "리뷰 증가 확인", "장기 미관측", "최근 관측 시각", "중복 선정 방지", "실패 재시도 유예")):
        body += [circle(78, 251 + i * 44, 4), text(94, 258 + i * 44, value, 19, MUTED)]
    body += [line(432, 348, 470, 348, BLUE, arrow=True)]
    for i, category in enumerate(("상의", "하의", "아우터", "원피스")):
        xx, yy = 490 + (i % 2) * 462, 174 + (i // 2) * 188
        body += [rect(xx, yy, 440, 164), text(xx + 24, yy + 40, category, 25, INK, 650), text(xx + 416, yy + 40, "5개 배정", 17, BLUE, 650, "end")]
        for slot in range(5):
            cx = xx + 50 + slot * 82
            body += [circle(cx, yy + 91, 20, "#e8efff"), text(cx, yy + 97, slot + 1, 17, BLUE, 650, "middle")]
        body.append(text(xx + 24, yy + 143, "배정 슬롯 · 수집 성공 수가 아닙니다", 15, MUTED))
    body += [rect(48, 558, 1344, 76, "#edf2ff", "none"),
             text(72, 588, "09:00  검색어 순환", 21, BLUE, 650), text(460, 588, "13:00  카테고리 균형 재관측", 21, BLUE, 650),
             text(72, 617, "카테고리별 5개 × 4개 카테고리 = 하루 최대 20개 재관측", 17, MUTED),
             text(48, 672, "업무 설계의 개념도 · 공개 데모는 가상 실행 기록만 사용 · 설정 적용 이후 최초 예약 실행의 효과는 별도 검증 대상", 14, MUTED)]
    document("balanced-observation.svg", 698, "카테고리 균형과 관측 이력을 함께 관리합니다", "관측 후보를 고르는 조건과 13:00 재관측의 배정 구조 · 가중치나 우선순위 점수를 임의로 만들지 않았습니다", body)


def main() -> None:
    data = json.loads((ROOT / "docs/data/demo.json").read_text(encoding="utf-8"))
    if data.get("synthetic") is not True:
        raise ValueError("Documentation figures require synthetic demo data")
    products = {p["product_id"]: p for p in data["products"]}
    ASSETS.mkdir(exist_ok=True)
    pipeline(products["DEMO-013"], data["as_of"])
    quality(products, data["as_of"])
    extraction()
    scheduling()
    print("Generated 4 SVG engineering figures from synthetic data and documented rules")


if __name__ == "__main__":
    main()
