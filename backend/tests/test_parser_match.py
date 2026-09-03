"""结构匹配辅助逻辑单测（不依赖完整 CDXML）。"""

from __future__ import annotations

from cdxml_parser.parser import (
    assign_other_texts_to_compounds,
    find_next_structure_below,
    other_text_in_y_band,
    other_text_y_upper,
    strip_trailing_paren_group,
)


def _bbox(x1, y1, x2, y2):
    return {
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "center_x": (x1 + x2) / 2,
        "center_y": (y1 + y2) / 2,
    }


def test_strip_trailing_paren_group():
    assert strip_trailing_paren_group("HW1800023(VET,102354)") == "HW1800023"
    assert strip_trailing_paren_group("HW1800023(VET,102354) ") == "HW1800023"
    assert strip_trailing_paren_group("HW1800023") == "HW1800023"
    assert strip_trailing_paren_group("HW(AB)1800023") == "HW(AB)1800023"


def test_find_next_structure_below_x_overlap_nearest():
    top = {"bbox": _bbox(0, 0, 100, 50)}
    below = {"bbox": _bbox(10, 200, 90, 250)}
    farther = {"bbox": _bbox(10, 400, 90, 450)}
    side = {"bbox": _bbox(300, 200, 400, 250)}
    structures = [top, below, farther, side]
    nxt = find_next_structure_below(top["bbox"], structures)
    assert nxt is below


def test_other_text_y_band_capped_by_next():
    struct = _bbox(0, 0, 100, 50)
    next_struct = {"bbox": _bbox(0, 180, 100, 230)}
    # match_y_down 很大，但被下一结构顶边 180 封顶
    assert other_text_y_upper(struct, 500, next_struct) == 180
    text_ok = _bbox(0, 100, 80, 120)
    text_past = _bbox(0, 185, 80, 200)
    assert other_text_in_y_band(struct, text_ok, 500, next_struct)
    assert not other_text_in_y_band(struct, text_past, 500, next_struct)


def test_other_text_y_band_without_next_uses_match_y_down():
    struct = _bbox(0, 0, 100, 50)
    assert other_text_y_upper(struct, 300, None) == 350
    text = _bbox(0, 320, 80, 340)
    assert other_text_in_y_band(struct, text, 300, None)
    text_far = _bbox(0, 400, 80, 420)
    assert not other_text_in_y_band(struct, text_far, 300, None)


def test_assign_other_texts_exclusive_nearest():
    upper = {
        "bbox": _bbox(0, 0, 100, 50),
        "text": "",
    }
    lower = {
        "bbox": _bbox(0, 200, 100, 250),
        "text": "",
    }
    structures = [upper, lower]
    # 落在 upper 与 lower 之间，更靠近 upper 底边
    near_upper = {"content": "A", "bbox": _bbox(10, 80, 90, 100)}
    # 落在 lower 下方区间
    near_lower = {"content": "B", "bbox": _bbox(10, 260, 90, 280)}
    used = assign_other_texts_to_compounds(
        [upper, lower],
        [near_upper, near_lower],
        structures,
        match_y_down=300,
    )
    assert used == {0, 1}
    assert upper["text"] == "A"
    assert lower["text"] == "B"


def test_assign_does_not_cross_next_structure():
    upper = {"bbox": _bbox(0, 0, 100, 50), "text": ""}
    lower = {"bbox": _bbox(0, 200, 100, 250), "text": ""}
    # 文字在 lower 底边之下；upper 的上界被 lower.y1=200 封顶，不能跨行抢走
    below_lower = {"content": "X", "bbox": _bbox(10, 260, 90, 280)}
    assign_other_texts_to_compounds(
        [upper, lower],
        [below_lower],
        [upper, lower],
        match_y_down=1000,
    )
    assert upper["text"] == ""
    assert lower["text"] == "X"
