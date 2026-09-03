
import xml.etree.ElementTree as ET
import re
import csv
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from rdkit import Chem
    from rdkit.Chem import rdmolops
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    print("警告: RDKit未安装，SMILES转换功能不可用")


def parse_fragment_to_smiles(frag):
    if not RDKIT_AVAILABLE:
        return ""
    
    try:
        atoms = []
        atom_map = {}
        
        nested_info_list = []
        frag_node_to_nested = {}
        
        for n in frag.findall('./n'):
            if n.get('NodeType') == 'Fragment':
                frag_node_id = n.get('id')
                
                nested_frag = None
                for child in n:
                    if child.tag == 'fragment':
                        nested_frag = child
                        break
                
                if nested_frag is not None:
                    ext_conn_point = None
                    target_atom_in_nested = None
                    
                    for nf_atom in nested_frag.findall('./n'):
                        if nf_atom.get('NodeType') == 'ExternalConnectionPoint':
                            ext_conn_point = nf_atom.get('id')
                            break
                    
                    if ext_conn_point:
                        for b in nested_frag.findall('./b'):
                            b_begin = b.get('B')
                            b_end = b.get('E')
                            if b_begin == ext_conn_point:
                                target_atom_in_nested = b_end
                                break
                            elif b_end == ext_conn_point:
                                target_atom_in_nested = b_begin
                                break
                    
                    nested_info = {
                        'fragment': nested_frag,
                        'ext_conn_point': ext_conn_point,
                        'target_atom': target_atom_in_nested
                    }
                    nested_info_list.append(nested_info)
                    frag_node_to_nested[frag_node_id] = nested_info
        
        frag_node_mapping = {}
        for n in frag.findall('./n'):
            if n.get('NodeType') == 'Fragment':
                node_id = n.get('id')
                
                connected_to = None
                for b in frag.findall('./b'):
                    b_begin = b.get('B')
                    b_end = b.get('E')
                    if b_begin == node_id:
                        connected_to = b_end
                        break
                    elif b_end == node_id:
                        connected_to = b_begin
                        break
                
                frag_node_mapping[node_id] = connected_to
        
        for n in frag.findall('./n'):
            atom_id = n.get('id')
            node_type = n.get('NodeType')
            
            if node_type == 'ExternalConnectionPoint':
                continue
            
            if node_type == 'Fragment':
                continue
            
            element_num = n.get('Element')
            charge = n.get('Charge', '0')
            num_hydrogens = n.get('NumHydrogens')
            
            if element_num:
                element_num = int(element_num)
            else:
                element_num = 6
            
            atoms.append({
                'id': atom_id,
                'element': element_num,
                'charge': int(charge),
                'num_hydrogens': int(num_hydrogens) if num_hydrogens else None
            })
            atom_map[atom_id] = len(atoms) - 1
        
        for nested_info in nested_info_list:
            nested_frag = nested_info['fragment']
            for n in nested_frag.findall('./n'):
                atom_id = n.get('id')
                node_type = n.get('NodeType')
                
                if node_type == 'ExternalConnectionPoint':
                    continue
                
                element_num = n.get('Element')
                charge = n.get('Charge', '0')
                num_hydrogens = n.get('NumHydrogens')
                
                if element_num:
                    element_num = int(element_num)
                else:
                    element_num = 6
                
                atoms.append({
                    'id': atom_id,
                    'element': element_num,
                    'charge': int(charge),
                    'num_hydrogens': int(num_hydrogens) if num_hydrogens else None
                })
                atom_map[atom_id] = len(atoms) - 1
        
        if not atoms:
            return ""
        
        mol = Chem.EditableMol(Chem.Mol())
        
        for atom in atoms:
            rd_atom = Chem.Atom(atom['element'])
            if atom['charge'] != 0:
                rd_atom.SetFormalCharge(atom['charge'])
            if atom['num_hydrogens'] is not None:
                rd_atom.SetNumExplicitHs(atom['num_hydrogens'])
            mol.AddAtom(rd_atom)
        
        for b in frag.findall('./b'):
            begin_id = b.get('B')
            end_id = b.get('E')
            order = b.get('Order', '1')
            
            if begin_id in atom_map and end_id in atom_map:
                begin_idx = atom_map[begin_id]
                end_idx = atom_map[end_id]
                
                bond_order = Chem.BondType.SINGLE
                if order == '2':
                    bond_order = Chem.BondType.DOUBLE
                elif order == '3':
                    bond_order = Chem.BondType.TRIPLE
                elif order == '4':
                    bond_order = Chem.BondType.QUADRUPLE
                elif order == 'A':
                    bond_order = Chem.BondType.AROMATIC
                
                mol.AddBond(begin_idx, end_idx, bond_order)
        
        for nested_info in nested_info_list:
            nested_frag = nested_info['fragment']
            for b in nested_frag.findall('./b'):
                begin_id = b.get('B')
                end_id = b.get('E')
                order = b.get('Order', '1')
                
                if begin_id in atom_map and end_id in atom_map:
                    begin_idx = atom_map[begin_id]
                    end_idx = atom_map[end_id]
                    
                    bond_order = Chem.BondType.SINGLE
                    if order == '2':
                        bond_order = Chem.BondType.DOUBLE
                    elif order == '3':
                        bond_order = Chem.BondType.TRIPLE
                    elif order == '4':
                        bond_order = Chem.BondType.QUADRUPLE
                    elif order == 'A':
                        bond_order = Chem.BondType.AROMATIC
                    
                    try:
                        mol.AddBond(begin_idx, end_idx, bond_order)
                    except:
                        pass
        
        for frag_node_id, connected_atom in frag_node_mapping.items():
            if frag_node_id in frag_node_to_nested:
                nested_info = frag_node_to_nested[frag_node_id]
                target_atom = nested_info['target_atom']
                if target_atom and connected_atom in atom_map and target_atom in atom_map:
                    begin_idx = atom_map[connected_atom]
                    end_idx = atom_map[target_atom]
                    
                    try:
                        mol.AddBond(begin_idx, end_idx, Chem.BondType.SINGLE)
                    except:
                        pass
        
        final_mol = mol.GetMol()
        
        try:
            Chem.SanitizeMol(final_mol, sanitizeOps=Chem.SanitizeFlags.SANITIZE_ALL ^ Chem.SanitizeFlags.SANITIZE_SETAROMATICITY)
        except Exception as e:
            try:
                Chem.SanitizeMol(final_mol, sanitizeOps=Chem.SanitizeFlags.SANITIZE_ALL ^ Chem.SanitizeFlags.SANITIZE_SETAROMATICITY ^ Chem.SanitizeFlags.SANITIZE_ADJUSTHS)
            except:
                pass
        
        try:
            Chem.Kekulize(final_mol)
        except:
            pass
        
        # 禁止对整条 SMILES 做 upper()：Cl、Br、Si 等必须保留大小写，否则会变成非法/错误元素符号（如 CL）。
        return Chem.MolToSmiles(
            final_mol, isomericSmiles=False, allBondsExplicit=False, kekuleSmiles=True
        )
    
    except Exception as e:
        print(f"SMILES转换出错: {e}")
        import traceback
        traceback.print_exc()
        return ""


def _bbox_to_row(bbox: Dict[str, float]) -> Dict[str, float]:
    return {
        "x1": bbox["x1"],
        "y1": bbox["y1"],
        "x2": bbox["x2"],
        "y2": bbox["y2"],
        "center_x": bbox["center_x"],
        "center_y": bbox["center_y"],
    }


@dataclass
class ParseResult:
    """解析结果：成功匹配行 + 各类未纳入或需人工复核项。"""

    success: bool
    message: str = ""
    compound_count: int = 0
    output_csv_path: str = ""
    compounds_sorted: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_hw: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_structures: List[Dict[str, Any]] = field(default_factory=list)
    unused_property_texts: List[Dict[str, Any]] = field(default_factory=list)
    unused_other_texts: List[Dict[str, Any]] = field(default_factory=list)
    matched_but_empty_smiles: List[Dict[str, Any]] = field(default_factory=list)


def parse_result_to_json_dict(
    result: ParseResult,
    log_lines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """供 Electron 等子进程读取：可 JSON 序列化的解析结果（不含 XML 节点引用）。"""
    compounds: List[Dict[str, str]] = []
    for c in result.compounds_sorted:
        compounds.append(
            {
                "compound_id": c.get("name", "") or "",
                "smiles": c.get("smiles", "") or "",
                "tpsa": c.get("tpsa", "") or "",
                "clogp": c.get("clogp", "") or "",
                "text": c.get("text", "") or "",
            }
        )
    return {
        "success": result.success,
        "message": result.message,
        "compound_count": result.compound_count,
        "output_csv_path": result.output_csv_path,
        "log_lines": log_lines or [],
        "compounds": compounds,
        "unmatched_hw": result.unmatched_hw,
        "unmatched_structures": result.unmatched_structures,
        "unused_property_texts": result.unused_property_texts,
        "unused_other_texts": result.unused_other_texts,
        "matched_but_empty_smiles": result.matched_but_empty_smiles,
    }


def get_bounding_box(elem):
    """仅解析 BoundingBox 属性；缺失、解析失败或四元全 0 时返回 None。"""
    bbox = elem.get('BoundingBox')
    if bbox:
        try:
            coords = list(map(float, bbox.split()))
            if len(coords) == 4:
                if coords[0] == 0 and coords[1] == 0 and coords[2] == 0 and coords[3] == 0:
                    return None
                return {
                    'x1': coords[0],
                    'y1': coords[1],
                    'x2': coords[2],
                    'y2': coords[3],
                    'center_x': (coords[0] + coords[2]) / 2,
                    'center_y': (coords[1] + coords[3]) / 2
                }
        except Exception:
            pass
    return None


def parse_p_point(s: Optional[str]) -> Optional[Tuple[float, float]]:
    if not s or not str(s).strip():
        return None
    try:
        parts = str(s).split()
        if len(parts) >= 2:
            return (float(parts[0]), float(parts[1]))
    except (ValueError, TypeError):
        pass
    return None


def bbox_dict_from_xyxy(x1: float, y1: float, x2: float, y2: float) -> Dict[str, float]:
    return {
        'x1': x1,
        'y1': y1,
        'x2': x2,
        'y2': y2,
        'center_x': (x1 + x2) / 2,
        'center_y': (y1 + y2) / 2,
    }


def compute_fragment_bbox_from_n_points(fragment_el) -> Optional[Dict[str, float]]:
    xs: List[float] = []
    ys: List[float] = []
    for n in fragment_el.findall('.//n'):
        pt = parse_p_point(n.get('p'))
        if pt is not None:
            xs.append(pt[0])
            ys.append(pt[1])
    if not xs:
        return None
    return bbox_dict_from_xyxy(min(xs), min(ys), max(xs), max(ys))


def find_immediate_parent(container, target):
    for parent in container.iter():
        for c in parent:
            if c is target:
                return parent
    return None


def resolve_bbox_fragment(fragment_el):
    bb = get_bounding_box(fragment_el)
    if bb is not None:
        return bb
    return compute_fragment_bbox_from_n_points(fragment_el)


def resolve_bbox_t(t_elem, page):
    bb = get_bounding_box(t_elem)
    if bb is not None:
        return bb
    pt = parse_p_point(t_elem.get('p'))
    if pt is not None:
        x, y = pt
        return bbox_dict_from_xyxy(x, y, x, y)
    el = t_elem
    while True:
        parent = find_immediate_parent(page, el)
        if parent is None:
            break
        if parent.tag == 'n':
            pt2 = parse_p_point(parent.get('p'))
            if pt2 is not None:
                x, y = pt2
                return bbox_dict_from_xyxy(x, y, x, y)
            return None
        el = parent
    return None


def get_text_content(elem):
    content_parts = []
    for s in elem.findall('./s'):
        if s.text:
            content_parts.append(s.text)
    return ''.join(content_parts)


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def has_x_overlap(
    bbox1: Dict[str, float],
    bbox2: Dict[str, float],
    x_extend_left: float = 0.0,
    x_extend_right: float = 0.0,
) -> bool:
    """判断结构框 bbox1 与文字框 bbox2 在 X 方向是否重叠。

    在结构框两侧按 CDXML 坐标绝对值扩展：左侧向左扩展 x_extend_left，右侧向右扩展 x_extend_right，再与 bbox2 做区间相交判断。
    """
    el = max(0.0, float(x_extend_left))
    er = max(0.0, float(x_extend_right))
    x1 = bbox1["x1"] - el
    x2 = bbox1["x2"] + er
    return x1 <= bbox2["x2"] and bbox2["x1"] <= x2


def strip_trailing_paren_group(text: str) -> str:
    """去掉末尾一对圆括号及其中内容，例如 HW1800023(VET,102354) → HW1800023。"""
    m = re.match(r"^(.*)(\([^)]*\))\s*$", text)
    if not m:
        return text
    return m.group(1).rstrip()


def find_next_structure_below(
    struct_bbox: Dict[str, float],
    structures: List[Dict[str, Any]],
    x_extend_left: float = 0.0,
    x_extend_right: float = 0.0,
) -> Optional[Dict[str, Any]]:
    """在 X 重叠且中心 Y 更大的结构中，取竖直方向最近的下一个结构。"""
    best: Optional[Dict[str, Any]] = None
    best_dy = float("inf")
    cy = struct_bbox["center_y"]
    for struct in structures:
        other = struct["bbox"]
        if other is struct_bbox:
            continue
        if other["center_y"] <= cy:
            continue
        if not has_x_overlap(
            struct_bbox, other, x_extend_left, x_extend_right
        ):
            continue
        dy = other["center_y"] - cy
        if dy < best_dy:
            best_dy = dy
            best = struct
    return best


def other_text_y_upper(
    struct_bbox: Dict[str, float],
    match_y_down: float,
    next_struct: Optional[Dict[str, Any]] = None,
) -> float:
    """其他文字归属的 Y 上界：min(底边+match_y_down, 下一结构顶边)。"""
    upper = struct_bbox["y2"] + float(match_y_down)
    if next_struct is not None:
        upper = min(upper, next_struct["bbox"]["y1"])
    return upper


def other_text_in_y_band(
    struct_bbox: Dict[str, float],
    text_bbox: Dict[str, float],
    match_y_down: float,
    next_struct: Optional[Dict[str, Any]] = None,
) -> bool:
    """文字顶边中点（用 y1）是否落在 [结构底边, Y 上界] 内。"""
    y_top = text_bbox["y1"]
    y_bottom = struct_bbox["y2"]
    upper = other_text_y_upper(struct_bbox, match_y_down, next_struct)
    return y_bottom <= y_top <= upper


def assign_other_texts_to_compounds(
    compounds: List[Dict[str, Any]],
    other_texts: List[Dict[str, Any]],
    structures: List[Dict[str, Any]],
    *,
    match_x_extend_left: float = 0.0,
    match_x_extend_right: float = 0.0,
    match_y_down: float = 300.0,
) -> set:
    """将其他说明文字独占分配到化合物；返回已使用的 other_texts 下标集合。"""
    used_other: set = set()
    pending: Dict[int, List[Tuple[int, str, float]]] = {
        i: [] for i in range(len(compounds))
    }

    next_by_compound: List[Optional[Dict[str, Any]]] = []
    for compound in compounds:
        next_by_compound.append(
            find_next_structure_below(
                compound["bbox"],
                structures,
                match_x_extend_left,
                match_x_extend_right,
            )
        )

    for k, other in enumerate(other_texts):
        best_i: Optional[int] = None
        best_dist = float("inf")
        text_top_center = (
            (other["bbox"]["x1"] + other["bbox"]["x2"]) / 2,
            other["bbox"]["y1"],
        )
        for i, compound in enumerate(compounds):
            struct_bbox = compound["bbox"]
            if not has_x_overlap(
                struct_bbox,
                other["bbox"],
                match_x_extend_left,
                match_x_extend_right,
            ):
                continue
            if not other_text_in_y_band(
                struct_bbox,
                other["bbox"],
                match_y_down,
                next_by_compound[i],
            ):
                continue
            struct_bottom_center = (
                (struct_bbox["x1"] + struct_bbox["x2"]) / 2,
                struct_bbox["y2"],
            )
            dist = distance(struct_bottom_center, text_top_center)
            if dist < best_dist:
                best_dist = dist
                best_i = i
        if best_i is not None:
            pending[best_i].append((k, other["content"], best_dist))
            used_other.add(k)

    for i, compound in enumerate(compounds):
        items = sorted(pending[i], key=lambda x: x[2])
        if items:
            compound["text"] = " ".join(content for _, content, _ in items)
            for k, _, _ in items:
                used_other.add(k)
        else:
            compound["text"] = ""

    return used_other


def main(
    cdxml_path: str,
    output_path: Optional[str] = None,
    log: Callable[..., None] = print,
    *,
    match_x_extend_left: float = 0.0,
    match_x_extend_right: float = 0.0,
    match_y_down: float = 300.0,
) -> ParseResult:
    if match_x_extend_left < 0:
        match_x_extend_left = 0.0
    if match_x_extend_left > 1e6:
        match_x_extend_left = 1e6
    if match_x_extend_right < 0:
        match_x_extend_right = 0.0
    if match_x_extend_right > 1e6:
        match_x_extend_right = 1e6
    if match_y_down <= 0:
        match_y_down = 300.0

    tree = ET.parse(cdxml_path)
    root = tree.getroot()
    page = root.find(".//page")

    if page is None:
        return ParseResult(success=False, message="CDXML 中未找到 <page> 节点")

    log("=== 开始解析CDXML文件 ===")

    structures: List[Dict[str, Any]] = []
    hw_texts: List[Dict[str, Any]] = []
    tpsa_texts: List[Dict[str, Any]] = []
    clogp_texts: List[Dict[str, Any]] = []
    other_texts: List[Dict[str, Any]] = []

    for child in page:
        if child.tag == "fragment":
            bbox = resolve_bbox_fragment(child)
        elif child.tag == "t":
            bbox = resolve_bbox_t(child, page)
        else:
            bbox = None

        if child.tag == "fragment" and bbox:
            has_atoms = len(child.findall("./n")) > 0
            has_bonds = len(child.findall("./b")) > 0
            if has_atoms and has_bonds:
                smiles = ""
                if RDKIT_AVAILABLE:
                    smiles = parse_fragment_to_smiles(child)

                structures.append(
                    {
                        "element": child,
                        "bbox": bbox,
                        "smiles": smiles,
                        "name": "",
                        "tpsa": "",
                        "clogp": "",
                        "text": "",
                    }
                )

        elif child.tag == "t" and bbox:
            content = get_text_content(child)
            if content:
                if content.startswith("HW"):
                    hw_texts.append({"content": content, "bbox": bbox})
                else:
                    if "tPSA" in content or "CLogP" in content:
                        tpsa_texts.append({"content": content, "bbox": bbox})
                        clogp_texts.append({"content": content, "bbox": bbox})
                    else:
                        other_texts.append({"content": content, "bbox": bbox})

    log(f"找到 {len(structures)} 个化合物结构")
    log(f"找到 {len(hw_texts)} 个HW开头的文字")
    log(f"找到 {len(tpsa_texts)} 个tPSA相关文字")
    log(f"找到 {len(clogp_texts)} 个CLogP相关文字")
    log(f"找到 {len(other_texts)} 个其他文字\n")

    log(
        f"=== 开始匹配 ===（结构 X 左扩展={match_x_extend_left}，右扩展={match_x_extend_right}，"
        f"Y 向下匹配距离上限={match_y_down}）"
    )

    used_hw: set = set()
    used_tpsa: set = set()
    used_clogp: set = set()
    used_struct_indices: set = set()

    compounds: List[Dict[str, Any]] = []
    unmatched_hw: List[Dict[str, Any]] = []

    for i, hw in enumerate(hw_texts):
        if i in used_hw:
            continue

        hw_bbox = hw["bbox"]

        best_struct = None
        best_dist = float("inf")
        for j, struct in enumerate(structures):
            if any(s["element"] is struct["element"] for s in compounds):
                continue

            struct_bbox = struct["bbox"]

            if not has_x_overlap(
                struct_bbox, hw_bbox, match_x_extend_left, match_x_extend_right
            ):
                continue

            dist = abs(hw_bbox["center_y"] - struct_bbox["center_y"])
            if dist < match_y_down and dist < best_dist:
                best_dist = dist
                best_struct = (j, struct)

        if best_struct is None:
            unmatched_hw.append(
                {
                    "content": hw["content"],
                    **_bbox_to_row(hw_bbox),
                }
            )
            continue

        idx, struct = best_struct
        used_struct_indices.add(idx)
        struct_bbox = struct["bbox"]
        struct_center = (struct_bbox["center_x"], struct_bbox["center_y"])

        compound = {
            "element": struct["element"],
            "bbox": struct_bbox,
            "smiles": struct["smiles"],
            "name": strip_trailing_paren_group(hw["content"]),
            "tpsa": "",
            "clogp": "",
            "text": "",
        }

        used_hw.add(i)

        best_tpsa = None
        best_tpsa_dist = float("inf")
        for k, tpsa in enumerate(tpsa_texts):
            if k in used_tpsa:
                continue

            if not has_x_overlap(
                struct_bbox, tpsa["bbox"], match_x_extend_left, match_x_extend_right
            ):
                continue

            tpsa_center = (tpsa["bbox"]["center_x"], tpsa["bbox"]["center_y"])
            dist = distance(struct_center, tpsa_center)
            if dist < match_y_down and dist < best_tpsa_dist:
                best_tpsa_dist = dist
                best_tpsa = (k, tpsa)

        if best_tpsa is not None:
            tpsa_match = re.search(r"tPSA[:\s]*([\d.]+)", best_tpsa[1]["content"], re.IGNORECASE)
            if tpsa_match:
                compound["tpsa"] = tpsa_match.group(1)
            used_tpsa.add(best_tpsa[0])

        best_clogp = None
        best_clogp_dist = float("inf")
        for k, clogp in enumerate(clogp_texts):
            if k in used_clogp:
                continue

            if not has_x_overlap(
                struct_bbox, clogp["bbox"], match_x_extend_left, match_x_extend_right
            ):
                continue

            clogp_center = (clogp["bbox"]["center_x"], clogp["bbox"]["center_y"])
            dist = distance(struct_center, clogp_center)
            if dist < match_y_down and dist < best_clogp_dist:
                best_clogp_dist = dist
                best_clogp = (k, clogp)

        if best_clogp is not None:
            clogp_match = re.search(r"CLogP[:\s]*([\d.]+)", best_clogp[1]["content"], re.IGNORECASE)
            if clogp_match:
                compound["clogp"] = clogp_match.group(1)
            used_clogp.add(best_clogp[0])

        compounds.append(compound)

    used_other = assign_other_texts_to_compounds(
        compounds,
        other_texts,
        structures,
        match_x_extend_left=match_x_extend_left,
        match_x_extend_right=match_x_extend_right,
        match_y_down=match_y_down,
    )

    log(f"\n成功匹配到 {len(compounds)} 个化合物\n")

    compounds_sorted = sorted(
        compounds, key=lambda c: (c["bbox"]["center_y"], -c["bbox"]["center_x"])
    )

    log("=== 前20个化合物 ===")
    for i, comp in enumerate(compounds_sorted[:20], 1):
        log(f"{i:2d}: {comp['name'][:25]:25s} tPSA={comp['tpsa']:8s} CLogP={comp['clogp']:8s}")

    if output_path:
        log("\n=== 生成CSV文件 ===")
        header = ["Compound_ID", "structure", "tPSA", "CLogP", "text"]

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            for compound in compounds_sorted:
                row = [
                    compound["name"],
                    compound["smiles"],
                    compound["tpsa"],
                    compound["clogp"],
                    compound["text"],
                ]
                writer.writerow(row)

        log(f"CSV文件已生成: {output_path}")
    else:
        log("\n=== 未写入 CSV（未指定输出路径，仅返回解析结果）===")

    unmatched_structures: List[Dict[str, Any]] = []
    for j, struct in enumerate(structures):
        if j not in used_struct_indices:
            bb = struct["bbox"]
            unmatched_structures.append(
                {
                    "structure_index": j + 1,
                    "smiles": struct["smiles"],
                    **_bbox_to_row(bb),
                }
            )

    unused_property_texts: List[Dict[str, Any]] = []
    for k in range(len(tpsa_texts)):
        if k not in used_tpsa and k not in used_clogp:
            bb = tpsa_texts[k]["bbox"]
            unused_property_texts.append(
                {
                    "content": tpsa_texts[k]["content"],
                    **_bbox_to_row(bb),
                }
            )

    unused_other_texts: List[Dict[str, Any]] = []
    for k in range(len(other_texts)):
        if k not in used_other:
            bb = other_texts[k]["bbox"]
            unused_other_texts.append(
                {
                    "content": other_texts[k]["content"],
                    **_bbox_to_row(bb),
                }
            )

    matched_but_empty_smiles: List[Dict[str, Any]] = []
    for compound in compounds_sorted:
        if not (compound.get("smiles") or "").strip():
            bb = compound["bbox"]
            matched_but_empty_smiles.append(
                {
                    "Compound_ID": compound["name"],
                    **_bbox_to_row(bb),
                }
            )

    return ParseResult(
        success=True,
        message="解析完成",
        compound_count=len(compounds_sorted),
        output_csv_path=output_path or "",
        compounds_sorted=compounds_sorted,
        unmatched_hw=unmatched_hw,
        unmatched_structures=unmatched_structures,
        unused_property_texts=unused_property_texts,
        unused_other_texts=unused_other_texts,
        matched_but_empty_smiles=matched_but_empty_smiles,
    )

