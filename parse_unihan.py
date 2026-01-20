#!/usr/bin/env python3
from __future__ import annotations

"""
Chinese Word Hunt - Radical Database Parser

Parses the IDS (Ideographic Description Sequence) database to extract Chinese characters
and map them to their component Kangxi radicals. Only characters composed of 2+ base
radicals are included for the game.

Output: radical_database.json containing:
- radicals: List of 214 Kangxi radicals with metadata
- characters: Dict mapping characters to their component radicals and complexity score
- radical_to_chars: Reverse mapping from radical combinations to characters
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Kangxi Radicals (U+2F00 - U+2FD5) mapped to their equivalent CJK Unified Ideographs
# Format: (kangxi_radical, cjk_equivalent, radical_number, stroke_count, meaning)
KANGXI_RADICALS = [
    ("⼀", "一", 1, 1, "one"),
    ("⼁", "丨", 2, 1, "line"),
    ("⼂", "丶", 3, 1, "dot"),
    ("⼃", "丿", 4, 1, "slash"),
    ("⼄", "乙", 5, 1, "second"),
    ("⼅", "亅", 6, 1, "hook"),
    ("⼆", "二", 7, 2, "two"),
    ("⼇", "亠", 8, 2, "lid"),
    ("⼈", "人", 9, 2, "man"),
    ("⼉", "儿", 10, 2, "legs"),
    ("⼊", "入", 11, 2, "enter"),
    ("⼋", "八", 12, 2, "eight"),
    ("⼌", "冂", 13, 2, "down box"),
    ("⼍", "冖", 14, 2, "cover"),
    ("⼎", "冫", 15, 2, "ice"),
    ("⼏", "几", 16, 2, "table"),
    ("⼐", "凵", 17, 2, "open box"),
    ("⼑", "刀", 18, 2, "knife"),
    ("⼒", "力", 19, 2, "power"),
    ("⼓", "勹", 20, 2, "wrap"),
    ("⼔", "匕", 21, 2, "spoon"),
    ("⼕", "匚", 22, 2, "right open box"),
    ("⼖", "匸", 23, 2, "hiding enclosure"),
    ("⼗", "十", 24, 2, "ten"),
    ("⼘", "卜", 25, 2, "divination"),
    ("⼙", "卩", 26, 2, "seal"),
    ("⼚", "厂", 27, 2, "cliff"),
    ("⼛", "厶", 28, 2, "private"),
    ("⼜", "又", 29, 2, "again"),
    ("⼝", "口", 30, 3, "mouth"),
    ("⼞", "囗", 31, 3, "enclosure"),
    ("⼟", "土", 32, 3, "earth"),
    ("⼠", "士", 33, 3, "scholar"),
    ("⼡", "夂", 34, 3, "go"),
    ("⼢", "夊", 35, 3, "go slowly"),
    ("⼣", "夕", 36, 3, "evening"),
    ("⼤", "大", 37, 3, "big"),
    ("⼥", "女", 38, 3, "woman"),
    ("⼦", "子", 39, 3, "child"),
    ("⼧", "宀", 40, 3, "roof"),
    ("⼨", "寸", 41, 3, "inch"),
    ("⼩", "小", 42, 3, "small"),
    ("⼪", "尢", 43, 3, "lame"),
    ("⼫", "尸", 44, 3, "corpse"),
    ("⼬", "屮", 45, 3, "sprout"),
    ("⼭", "山", 46, 3, "mountain"),
    ("⼮", "巛", 47, 3, "river"),
    ("⼯", "工", 48, 3, "work"),
    ("⼰", "己", 49, 3, "oneself"),
    ("⼱", "巾", 50, 3, "turban"),
    ("⼲", "干", 51, 3, "dry"),
    ("⼳", "幺", 52, 3, "short thread"),
    ("⼴", "广", 53, 3, "dotted cliff"),
    ("⼵", "廴", 54, 3, "long stride"),
    ("⼶", "廾", 55, 3, "two hands"),
    ("⼷", "弋", 56, 3, "shoot"),
    ("⼸", "弓", 57, 3, "bow"),
    ("⼹", "彐", 58, 3, "snout"),
    ("⼺", "彡", 59, 3, "bristle"),
    ("⼻", "彳", 60, 3, "step"),
    ("⼼", "心", 61, 4, "heart"),
    ("⼽", "戈", 62, 4, "halberd"),
    ("⼾", "戶", 63, 4, "door"),
    ("⼿", "手", 64, 4, "hand"),
    ("⽀", "支", 65, 4, "branch"),
    ("⽁", "攴", 66, 4, "rap"),
    ("⽂", "文", 67, 4, "script"),
    ("⽃", "斗", 68, 4, "dipper"),
    ("⽄", "斤", 69, 4, "axe"),
    ("⽅", "方", 70, 4, "square"),
    ("⽆", "无", 71, 4, "not"),
    ("⽇", "日", 72, 4, "sun"),
    ("⽈", "曰", 73, 4, "say"),
    ("⽉", "月", 74, 4, "moon"),
    ("⽊", "木", 75, 4, "tree"),
    ("⽋", "欠", 76, 4, "lack"),
    ("⽌", "止", 77, 4, "stop"),
    ("⽍", "歹", 78, 4, "death"),
    ("⽎", "殳", 79, 4, "weapon"),
    ("⽏", "毋", 80, 4, "do not"),
    ("⽐", "比", 81, 4, "compare"),
    ("⽑", "毛", 82, 4, "fur"),
    ("⽒", "氏", 83, 4, "clan"),
    ("⽓", "气", 84, 4, "steam"),
    ("⽔", "水", 85, 4, "water"),
    ("⽕", "火", 86, 4, "fire"),
    ("⽖", "爪", 87, 4, "claw"),
    ("⽗", "父", 88, 4, "father"),
    ("⽘", "爻", 89, 4, "double x"),
    ("⽙", "爿", 90, 4, "half tree trunk"),
    ("⽚", "片", 91, 4, "slice"),
    ("⽛", "牙", 92, 4, "fang"),
    ("⽜", "牛", 93, 4, "cow"),
    ("⽝", "犬", 94, 4, "dog"),
    ("⽞", "玄", 95, 5, "profound"),
    ("⽟", "玉", 96, 5, "jade"),
    ("⽠", "瓜", 97, 5, "melon"),
    ("⽡", "瓦", 98, 5, "tile"),
    ("⽢", "甘", 99, 5, "sweet"),
    ("⽣", "生", 100, 5, "life"),
    ("⽤", "用", 101, 5, "use"),
    ("⽥", "田", 102, 5, "field"),
    ("⽦", "疋", 103, 5, "bolt of cloth"),
    ("⽧", "疒", 104, 5, "sickness"),
    ("⽨", "癶", 105, 5, "dotted tent"),
    ("⽩", "白", 106, 5, "white"),
    ("⽪", "皮", 107, 5, "skin"),
    ("⽫", "皿", 108, 5, "dish"),
    ("⽬", "目", 109, 5, "eye"),
    ("⽭", "矛", 110, 5, "spear"),
    ("⽮", "矢", 111, 5, "arrow"),
    ("⽯", "石", 112, 5, "stone"),
    ("⽰", "示", 113, 5, "spirit"),
    ("⽱", "禸", 114, 5, "track"),
    ("⽲", "禾", 115, 5, "grain"),
    ("⽳", "穴", 116, 5, "cave"),
    ("⽴", "立", 117, 5, "stand"),
    ("⽵", "竹", 118, 6, "bamboo"),
    ("⽶", "米", 119, 6, "rice"),
    ("⽷", "糸", 120, 6, "silk"),
    ("⽸", "缶", 121, 6, "jar"),
    ("⽹", "网", 122, 6, "net"),
    ("⽺", "羊", 123, 6, "sheep"),
    ("⽻", "羽", 124, 6, "feather"),
    ("⽼", "老", 125, 6, "old"),
    ("⽽", "而", 126, 6, "and"),
    ("⽾", "耒", 127, 6, "plow"),
    ("⽿", "耳", 128, 6, "ear"),
    ("⾀", "聿", 129, 6, "brush"),
    ("⾁", "肉", 130, 6, "meat"),
    ("⾂", "臣", 131, 6, "minister"),
    ("⾃", "自", 132, 6, "self"),
    ("⾄", "至", 133, 6, "arrive"),
    ("⾅", "臼", 134, 6, "mortar"),
    ("⾆", "舌", 135, 6, "tongue"),
    ("⾇", "舛", 136, 6, "oppose"),
    ("⾈", "舟", 137, 6, "boat"),
    ("⾉", "艮", 138, 6, "stopping"),
    ("⾊", "色", 139, 6, "color"),
    ("⾋", "艸", 140, 6, "grass"),
    ("⾌", "虍", 141, 6, "tiger"),
    ("⾍", "虫", 142, 6, "insect"),
    ("⾎", "血", 143, 6, "blood"),
    ("⾏", "行", 144, 6, "walk"),
    ("⾐", "衣", 145, 6, "clothes"),
    ("⾑", "襾", 146, 6, "west"),
    ("⾒", "見", 147, 7, "see"),
    ("⾓", "角", 148, 7, "horn"),
    ("⾔", "言", 149, 7, "speech"),
    ("⾕", "谷", 150, 7, "valley"),
    ("⾖", "豆", 151, 7, "bean"),
    ("⾗", "豕", 152, 7, "pig"),
    ("⾘", "豸", 153, 7, "badger"),
    ("⾙", "貝", 154, 7, "shell"),
    ("⾚", "赤", 155, 7, "red"),
    ("⾛", "走", 156, 7, "run"),
    ("⾜", "足", 157, 7, "foot"),
    ("⾝", "身", 158, 7, "body"),
    ("⾞", "車", 159, 7, "cart"),
    ("⾟", "辛", 160, 7, "bitter"),
    ("⾠", "辰", 161, 7, "morning"),
    ("⾡", "辵", 162, 7, "walk"),
    ("⾢", "邑", 163, 7, "city"),
    ("⾣", "酉", 164, 7, "wine"),
    ("⾤", "釆", 165, 7, "distinguish"),
    ("⾥", "里", 166, 7, "village"),
    ("⾦", "金", 167, 8, "gold"),
    ("⾧", "長", 168, 8, "long"),
    ("⾨", "門", 169, 8, "gate"),
    ("⾩", "阜", 170, 8, "mound"),
    ("⾪", "隶", 171, 8, "slave"),
    ("⾫", "隹", 172, 8, "short-tailed bird"),
    ("⾬", "雨", 173, 8, "rain"),
    ("⾭", "靑", 174, 8, "blue"),
    ("⾮", "非", 175, 8, "wrong"),
    ("⾯", "面", 176, 9, "face"),
    ("⾰", "革", 177, 9, "leather"),
    ("⾱", "韋", 178, 9, "tanned leather"),
    ("⾲", "韭", 179, 9, "leek"),
    ("⾳", "音", 180, 9, "sound"),
    ("⾴", "頁", 181, 9, "leaf"),
    ("⾵", "風", 182, 9, "wind"),
    ("⾶", "飛", 183, 9, "fly"),
    ("⾷", "食", 184, 9, "eat"),
    ("⾸", "首", 185, 9, "head"),
    ("⾹", "香", 186, 9, "fragrant"),
    ("⾺", "馬", 187, 10, "horse"),
    ("⾻", "骨", 188, 10, "bone"),
    ("⾼", "高", 189, 10, "tall"),
    ("⾽", "髟", 190, 10, "hair"),
    ("⾾", "鬥", 191, 10, "fight"),
    ("⾿", "鬯", 192, 10, "sacrificial wine"),
    ("⿀", "鬲", 193, 10, "cauldron"),
    ("⿁", "鬼", 194, 10, "ghost"),
    ("⿂", "魚", 195, 11, "fish"),
    ("⿃", "鳥", 196, 11, "bird"),
    ("⿄", "鹵", 197, 11, "salt"),
    ("⿅", "鹿", 198, 11, "deer"),
    ("⿆", "麥", 199, 11, "wheat"),
    ("⿇", "麻", 200, 11, "hemp"),
    ("⿈", "黃", 201, 12, "yellow"),
    ("⿉", "黍", 202, 12, "millet"),
    ("⿊", "黑", 203, 12, "black"),
    ("⿋", "黹", 204, 12, "embroidery"),
    ("⿌", "黽", 205, 13, "frog"),
    ("⿍", "鼎", 206, 13, "tripod"),
    ("⿎", "鼓", 207, 13, "drum"),
    ("⿏", "鼠", 208, 13, "rat"),
    ("⿐", "鼻", 209, 14, "nose"),
    ("⿑", "齊", 210, 14, "even"),
    ("⿒", "齒", 211, 15, "tooth"),
    ("⿓", "龍", 212, 16, "dragon"),
    ("⿔", "龜", 213, 16, "turtle"),
    ("⿕", "龠", 214, 17, "flute"),
]

# Build lookup sets for radicals
RADICAL_CHARS = set()  # All radical characters (both Kangxi and CJK forms)
RADICAL_TO_NUMBER = {}  # Map any radical form to its number
RADICAL_TO_CJK = {}  # Map Kangxi form to CJK form
CJK_TO_KANGXI = {}  # Map CJK form to Kangxi form

for kangxi, cjk, num, strokes, meaning in KANGXI_RADICALS:
    RADICAL_CHARS.add(kangxi)
    RADICAL_CHARS.add(cjk)
    RADICAL_TO_NUMBER[kangxi] = num
    RADICAL_TO_NUMBER[cjk] = num
    RADICAL_TO_CJK[kangxi] = cjk
    CJK_TO_KANGXI[cjk] = kangxi

# Common radical variants (simplified forms, positional variants, etc.)
# Maps variant to the standard CJK radical form
RADICAL_VARIANTS = {
    # Simplified/variant forms
    "亻": "人",  # person radical (left side)
    "氵": "水",  # water radical (left side)
    "扌": "手",  # hand radical (left side)
    "忄": "心",  # heart radical (left side)
    "犭": "犬",  # dog radical (left side)
    "礻": "示",  # spirit radical (left side)
    "衤": "衣",  # clothes radical (left side)
    "饣": "食",  # food radical (left side)
    "纟": "糸",  # silk radical (left side)
    "钅": "金",  # metal radical (left side)
    "讠": "言",  # speech radical (left side)
    "辶": "辵",  # walk radical (bottom)
    "阝": "阜",  # mound radical (left) - also 邑 on right
    "艹": "艸",  # grass radical (top)
    "宀": "宀",  # roof
    "冫": "冫",  # ice
    "刂": "刀",  # knife radical (right side)
    "卩": "卩",  # seal
    "廴": "廴",  # long stride
    "彳": "彳",  # step
    "灬": "火",  # fire radical (bottom)
    "爫": "爪",  # claw radical (top)
    "疒": "疒",  # sickness
    "罒": "网",  # net radical (top)
    "耂": "老",  # old radical variant
    "月": "肉",  # meat radical (often written as 月)
    "⺼": "肉",  # meat radical variant
    "⺍": "小",  # small radical (top)
    "⺌": "小",  # small radical variant
    "⺀": "八",  # eight variant
    "龵": "手",  # hand variant
    "⺕": "水",  # water variant
    "⺡": "水",  # water variant
    "⺗": "心",  # heart variant
    "⺘": "手",  # hand variant
    "⺮": "竹",  # bamboo variant
    "⺶": "羊",  # sheep variant
    "⺻": "聿",  # brush variant
    "⺾": "艸",  # grass variant
    "⻀": "网",  # net variant
    "⻌": "辵",  # walk variant
    "⻍": "辵",  # walk variant
    "⻎": "辵",  # walk variant
    "⻏": "邑",  # city variant (right side 阝)
    "⻖": "阜",  # mound variant (left side 阝)
    "⻗": "雨",  # rain variant
    "⻘": "靑",  # blue variant
    "⻙": "靑",  # blue variant
    "⻟": "食",  # food variant
    "⻠": "食",  # food variant
    "⻢": "馬",  # horse variant
    "⻣": "骨",  # bone variant
    "⻤": "鬼",  # ghost variant
    "⻥": "魚",  # fish variant
    "⻦": "鳥",  # bird variant
    "⻧": "鹵",  # salt variant
    "⻨": "麥",  # wheat variant
    "⻩": "黃",  # yellow variant
    "⻪": "黃",  # yellow variant
    "⻫": "齊",  # even variant
    "⻬": "齊",  # even variant
    "⻭": "齒",  # tooth variant
    "⻮": "齒",  # tooth variant
    "⻯": "龍",  # dragon variant
    "⻰": "龍",  # dragon variant
    "⻱": "龜",  # turtle variant
    "⻲": "龜",  # turtle variant
}

# Add variants to radical chars set
for variant, standard in RADICAL_VARIANTS.items():
    RADICAL_CHARS.add(variant)
    if standard in RADICAL_TO_NUMBER:
        RADICAL_TO_NUMBER[variant] = RADICAL_TO_NUMBER[standard]

# IDS operators (Ideographic Description Characters)
IDS_OPERATORS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻⿼⿽⿾⿿")

# Common non-radical components that appear frequently in characters
# Format: (character, stroke_count, meaning)
COMMON_COMPONENTS = [
    # Simplified forms of traditional radicals
    ("王", 4, "king"),
    ("鱼", 8, "fish"),
    ("鸟", 5, "bird"),
    ("贝", 4, "shell"),
    ("马", 3, "horse"),
    ("车", 4, "cart"),
    ("门", 3, "gate"),
    ("页", 6, "page"),
    ("见", 4, "see"),
    ("韦", 4, "leather"),
    ("长", 4, "long"),
    ("风", 4, "wind"),
    ("飞", 3, "fly"),
    # Common semantic components
    ("分", 4, "divide"),
    ("合", 6, "combine"),
    ("且", 5, "moreover"),
    ("令", 5, "order"),
    ("占", 5, "occupy"),
    ("各", 6, "each"),
    ("台", 5, "platform"),
    ("句", 5, "sentence"),
    ("者", 8, "person"),
    ("今", 4, "now"),
    ("包", 5, "wrap"),
    ("青", 8, "blue/green"),
    ("圭", 6, "jade tablet"),
    ("夫", 4, "husband"),
    ("召", 5, "summon"),
    ("交", 6, "exchange"),
    ("其", 8, "its"),
    ("果", 8, "fruit"),
    ("同", 6, "same"),
    ("此", 6, "this"),
    ("古", 5, "ancient"),
    ("可", 5, "can"),
    ("吉", 6, "lucky"),
    ("周", 8, "week"),
    ("元", 4, "origin"),
    ("云", 4, "cloud"),
    ("由", 5, "from"),
    ("也", 3, "also"),
    ("巴", 4, "hope"),
    ("及", 3, "reach"),
    ("反", 4, "reverse"),
    ("央", 5, "center"),
    ("不", 4, "not"),
    ("共", 6, "together"),
    ("半", 5, "half"),
    ("内", 4, "inside"),
    ("公", 4, "public"),
    ("甲", 5, "armor"),
    ("申", 5, "extend"),
    ("乃", 2, "then"),
    ("井", 4, "well"),
    ("丁", 2, "fourth"),
]

# Build component lookup
COMPONENT_CHARS = set()
COMPONENT_TO_STROKES = {}
for char, strokes, meaning in COMMON_COMPONENTS:
    COMPONENT_CHARS.add(char)
    COMPONENT_TO_STROKES[char] = strokes

# Visual aliases: radicals that look like other characters when compressed
# Format: semantic_radical -> visual_display_form
# These pairs should be treated as equivalent in gameplay
VISUAL_ALIASES = {
    "肉": "月",   # meat radical looks like moon when compressed
    "心": "忄",   # heart radical - left side form (already a variant)
    "水": "氵",   # water radical - left side form (already a variant)
    "火": "灬",   # fire radical - bottom form (already a variant)
    "手": "扌",   # hand radical - left side form (already a variant)
    "犬": "犭",   # dog radical - left side form (already a variant)
    "示": "礻",   # spirit radical - left side form (already a variant)
    "衣": "衤",   # clothing radical - left side form (already a variant)
    "人": "亻",   # person radical - left side form (already a variant)
    "刀": "刂",   # knife radical - right side form (already a variant)
    "艸": "艹",   # grass radical - top form (already a variant)
    "网": "罒",   # net radical - top form (already a variant)
}

# Reverse mapping for normalization
VISUAL_TO_SEMANTIC = {v: k for k, v in VISUAL_ALIASES.items()}

# For the game, we want to display the visual form but match on semantic
# Add 月 as a component since it's both a radical AND the visual form of 肉
COMPONENT_CHARS.add("月")
COMPONENT_TO_STROKES["月"] = 4


def normalize_component(char: str) -> str:
    """
    Convert a character to its standard form if it's a radical or common component.
    Returns the normalized form, or None if not recognized.
    """
    # Check Kangxi radical forms
    if char in RADICAL_TO_CJK:
        return RADICAL_TO_CJK[char]
    if char in RADICAL_VARIANTS:
        return RADICAL_VARIANTS[char]
    if char in RADICAL_TO_NUMBER:
        return char
    # Check common components
    if char in COMPONENT_CHARS:
        return char
    return None


def extract_components_from_ids(ids_string: str) -> tuple[list[str], bool]:
    """
    Extract all component radicals and common components from an IDS string.
    Returns a tuple of (list of component characters, bool indicating if ALL components were recognized).
    """
    components = []
    all_recognized = True
    
    for char in ids_string:
        # Skip IDS operators
        if char in IDS_OPERATORS:
            continue
        # Skip encircled numbers (used for unencoded components)
        if '\u2460' <= char <= '\u2473':  # ① to ⑳
            continue
        # Skip other special markers
        if char in "[]GTKJVAXO":
            continue
        
        # Check if it's a radical or common component
        normalized = normalize_component(char)
        if normalized:
            components.append(normalized)
        else:
            # Found an unrecognized component
            all_recognized = False
    
    return components, all_recognized


def parse_ids_file(filepath: Path) -> dict:
    """
    Parse the IDS file and extract character-to-radical mappings.
    Returns a dict mapping characters to their component radicals.
    """
    char_to_radicals = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            
            codepoint = parts[0]  # e.g., "U+4E00"
            char = parts[1]       # The actual character
            ids = parts[2]        # The IDS decomposition
            
            # Skip if the character itself is a radical or component
            if char in RADICAL_CHARS or char in COMPONENT_CHARS:
                continue
            
            # Extract components from IDS
            components, all_recognized = extract_components_from_ids(ids)
            
            # Only include characters where ALL components are recognized and has 2+ components
            if all_recognized and len(components) >= 2:
                char_to_radicals[char] = components
    
    return char_to_radicals


def calculate_complexity(components: list[str]) -> int:
    """
    Calculate complexity score for a character based on its components.
    Score = sum of stroke counts of all component radicals/components.
    """
    total_strokes = 0
    for comp in components:
        # Check if it's a Kangxi radical
        if comp in RADICAL_TO_NUMBER:
            rad_num = RADICAL_TO_NUMBER[comp]
            for _, cjk, num, strokes, _ in KANGXI_RADICALS:
                if num == rad_num:
                    total_strokes += strokes
                    break
        # Check if it's a common component
        elif comp in COMPONENT_TO_STROKES:
            total_strokes += COMPONENT_TO_STROKES[comp]
    return total_strokes


def build_radical_to_chars(char_to_radicals: dict) -> dict:
    """
    Build a reverse mapping from radical sets to characters.
    Key is a frozenset of radicals (as a sorted tuple string), value is list of characters.
    """
    radical_combo_to_chars = defaultdict(list)
    
    for char, radicals in char_to_radicals.items():
        # Create a key from sorted radicals
        key = ",".join(sorted(radicals))
        radical_combo_to_chars[key].append(char)
    
    return dict(radical_combo_to_chars)


def get_stroke_count_from_unihan(char: str, unihan_path: Path) -> int:
    """Get total stroke count for a character from Unihan database."""
    # This would require parsing Unihan_IRGSources.txt for kTotalStrokes
    # For now, we'll use the complexity calculation based on radicals
    return None


def is_common_cjk(char: str) -> bool:
    """Check if character is in common CJK ranges that render well."""
    code = ord(char)
    # CJK Unified Ideographs (most common, render well)
    if 0x4E00 <= code <= 0x9FFF:
        return True
    # CJK Unified Ideographs Extension A (less common but usually render)
    if 0x3400 <= code <= 0x4DBF:
        return True
    return False


def main():
    script_dir = Path(__file__).parent
    ids_path = script_dir / "UnihanDB" / "ids.txt"
    output_path = script_dir / "radical_database.json"
    
    print("Parsing IDS database...")
    char_to_radicals = parse_ids_file(ids_path)
    
    # Filter to only common CJK characters that render well
    char_to_radicals = {char: rads for char, rads in char_to_radicals.items() 
                        if is_common_cjk(char)}
    print(f"Found {len(char_to_radicals)} characters with 2+ radicals (filtered to common CJK)")
    
    print("Building character database...")
    characters = {}
    for char, radicals in char_to_radicals.items():
        complexity = calculate_complexity(radicals)
        characters[char] = {
            "radicals": radicals,
            "radical_count": len(radicals),
            "complexity": complexity,
        }
    
    print("Building radical-to-character mapping...")
    radical_to_chars = build_radical_to_chars(char_to_radicals)
    
    print("Building radical metadata...")
    radicals_list = []
    for kangxi, cjk, num, strokes, meaning in KANGXI_RADICALS:
        radicals_list.append({
            "number": num,
            "kangxi": kangxi,
            "cjk": cjk,
            "strokes": strokes,
            "meaning": meaning,
            "type": "radical",
        })
    
    print("Building common component metadata...")
    components_list = []
    for char, strokes, meaning in COMMON_COMPONENTS:
        components_list.append({
            "cjk": char,
            "strokes": strokes,
            "meaning": meaning,
            "type": "component",
        })
    
    # Add 月 as a special component (both radical #74 and visual form of 肉)
    components_list.append({
        "cjk": "月",
        "strokes": 4,
        "meaning": "moon",
        "type": "component",
    })
    
    # Combine radicals and components for game tiles
    all_tiles = radicals_list + components_list
    
    # Build visual alias mapping for the game
    # These show how to display semantic radicals and what alternatives match
    visual_aliases = {}
    for semantic, visual in VISUAL_ALIASES.items():
        visual_aliases[semantic] = {
            "display": visual,
            "matches": [semantic, visual],  # Both forms match this radical
        }
    
    # Build the final database
    database = {
        "metadata": {
            "description": "Chinese Word Hunt radical database",
            "total_radicals": len(KANGXI_RADICALS),
            "total_components": len(COMMON_COMPONENTS) + 1,  # +1 for 月
            "total_tiles": len(all_tiles),
            "total_characters": len(characters),
            "source": "CJKVI-IDS (based on CHISE IDS Database)",
        },
        "radicals": radicals_list,
        "components": components_list,
        "all_tiles": all_tiles,
        "visual_aliases": visual_aliases,
        "characters": characters,
        "radical_combinations": radical_to_chars,
    }
    
    print(f"Writing database to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print("Done!")
    print(f"\nSample characters:")
    sample_chars = list(characters.items())[:10]
    for char, data in sample_chars:
        print(f"  {char}: radicals={data['radicals']}, complexity={data['complexity']}")


if __name__ == "__main__":
    main()
