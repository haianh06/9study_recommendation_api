"""
Personality & Vocation Mapper
=============================================
Maps MBTI and Holland (RIASEC) codes to Major Groups and Interest Keywords
to solve the Cold-Start problem when users don't know what to study.
"""

from typing import List, Dict, Tuple
from datetime import datetime

# Full list of major groups from the database
MAJOR_GROUPS = [
    'Kế toán - Kiểm toán', 'Tài chính - Ngân hàng', 'Kinh tế - Quản trị kinh doanh', 
    'Khoa học máy tính - Kỹ thuật phần mềm', 'Kỹ thuật máy tính - Mạng & Vi mạch', 
    'Marketing - Quan hệ công chúng', 'Sư phạm', 'Y - Dược', 'Nông - Lâm - Thú y', 
    'Quân sự - Công an', 'Công nghệ thông tin - Truyền thông', 'Xây dựng - Kiến trúc - Đô thị', 
    'Ngôn ngữ - Ngoại ngữ', 'Kinh doanh quốc tế', 'Du lịch - Khách sạn - Nhà hàng', 
    'Kỹ thuật ô tô - Cơ khí', 'Điện - Điện tử - Tự động hóa', 'Hàng hải - Logistics', 
    'Hàng không', 'Vật liệu - Hóa chất - Luyện kim', 'Công nghệ thực phẩm', 'Kỹ thuật In - Xuất bản', 
    'Công nghệ sinh học', 'Luật - Pháp lý', 'Địa lý - Môi trường - Trắc địa', 
    'Nghệ thuật - Thiết kế - Âm nhạc', 'Môi trường - Tài nguyên', 'Tâm lý học - Công tác xã hội', 
    'Thể dục - Thể thao', 'Dệt may - Thời trang', 'Nông nghiệp - Bảo vệ thực vật', 
    'Toán - Thống kê ứng dụng', 'Quản lý nhà nước - Nhân lực', 'Văn học - Khoa học xã hội', 
    'Khoa học tự nhiên - Vật lý - Hóa học'
]

HOLLAND_MAP = {
    "R": {
        "name": "Realistic (Người thực tế)",
        "major_groups": [
            "Kỹ thuật ô tô - Cơ khí", "Điện - Điện tử - Tự động hóa", 
            "Xây dựng - Kiến trúc - Đô thị", "Nông - Lâm - Thú y",
            "Kỹ thuật máy tính - Mạng & Vi mạch", "Vật liệu - Hóa chất - Luyện kim"
        ],
        "keywords": ["kỹ thuật", "cơ khí", "máy móc", "xây dựng", "thực hành", "nông nghiệp"]
    },
    "I": {
        "name": "Investigative (Người nghiên cứu)",
        "major_groups": [
            "Khoa học máy tính - Kỹ thuật phần mềm", "Y - Dược",
            "Khoa học tự nhiên - Vật lý - Hóa học", "Công nghệ sinh học",
            "Toán - Thống kê ứng dụng", "Công nghệ thông tin - Truyền thông"
        ],
        "keywords": ["nghiên cứu", "khoa học", "phân tích", "dữ liệu", "y khoa", "máy tính"]
    },
    "A": {
        "name": "Artistic (Người nghệ thuật)",
        "major_groups": [
            "Nghệ thuật - Thiết kế - Âm nhạc", "Ngôn ngữ - Ngoại ngữ",
            "Văn học - Khoa học xã hội", "Dệt may - Thời trang",
            "Xây dựng - Kiến trúc - Đô thị"
        ],
        "keywords": ["nghệ thuật", "thiết kế", "sáng tạo", "ngôn ngữ", "viết lách", "thẩm mỹ"]
    },
    "S": {
        "name": "Social (Người xã hội)",
        "major_groups": [
            "Sư phạm", "Tâm lý học - Công tác xã hội", 
            "Y - Dược", "Du lịch - Khách sạn - Nhà hàng",
            "Quản lý nhà nước - Nhân lực"
        ],
        "keywords": ["giáo dục", "giúp đỡ", "tâm lý", "chăm sóc sức khỏe", "xã hội", "nhân sự"]
    },
    "E": {
        "name": "Enterprising (Người dám nghĩ dám làm)",
        "major_groups": [
            "Kinh tế - Quản trị kinh doanh", "Marketing - Quan hệ công chúng",
            "Luật - Pháp lý", "Kinh doanh quốc tế", "Tài chính - Ngân hàng"
        ],
        "keywords": ["kinh doanh", "lãnh đạo", "luật", "thuyết phục", "marketing", "quản trị"]
    },
    "C": {
        "name": "Conventional (Người quản lý dữ liệu)",
        "major_groups": [
            "Kế toán - Kiểm toán", "Tài chính - Ngân hàng", 
            "Quản lý nhà nước - Nhân lực", "Toán - Thống kê ứng dụng"
        ],
        "keywords": ["kế toán", "tài chính", "văn phòng", "số liệu", "tổ chức", "chi tiết"]
    }
}

MBTI_MAP = {
    # Analysts (INTJ, INTP, ENTJ, ENTP)
    "INTJ": {"holland": ["I", "R", "C"], "bonus_groups": ["Khoa học máy tính - Kỹ thuật phần mềm"]},
    "INTP": {"holland": ["I", "A", "R"], "bonus_groups": ["Toán - Thống kê ứng dụng"]},
    "ENTJ": {"holland": ["E", "I", "C"], "bonus_groups": ["Kinh tế - Quản trị kinh doanh"]},
    "ENTP": {"holland": ["E", "I", "A"], "bonus_groups": ["Marketing - Quan hệ công chúng"]},
    
    # Diplomats (INFJ, INFP, ENFJ, ENFP)
    "INFJ": {"holland": ["S", "I", "A"], "bonus_groups": ["Tâm lý học - Công tác xã hội"]},
    "INFP": {"holland": ["A", "S", "I"], "bonus_groups": ["Văn học - Khoa học xã hội"]},
    "ENFJ": {"holland": ["S", "E", "A"], "bonus_groups": ["Sư phạm"]},
    "ENFP": {"holland": ["A", "S", "E"], "bonus_groups": ["Ngôn ngữ - Ngoại ngữ", "Du lịch - Khách sạn - Nhà hàng"]},

    # Sentinels (ISTJ, ISFJ, ESTJ, ESFJ)
    "ISTJ": {"holland": ["C", "R", "I"], "bonus_groups": ["Kế toán - Kiểm toán"]},
    "ISFJ": {"holland": ["S", "C", "R"], "bonus_groups": ["Y - Dược", "Quản lý nhà nước - Nhân lực"]},
    "ESTJ": {"holland": ["E", "C", "R"], "bonus_groups": ["Quản lý nhà nước - Nhân lực"]},
    "ESFJ": {"holland": ["S", "E", "C"], "bonus_groups": ["Du lịch - Khách sạn - Nhà hàng"]},

    # Explorers (ISTP, ISFP, ESTP, ESFP)
    "ISTP": {"holland": ["R", "I", "C"], "bonus_groups": ["Kỹ thuật ô tô - Cơ khí"]},
    "ISFP": {"holland": ["A", "R", "S"], "bonus_groups": ["Nghệ thuật - Thiết kế - Âm nhạc"]},
    "ESTP": {"holland": ["E", "R", "S"], "bonus_groups": ["Kinh doanh quốc tế"]},
    "ESFP": {"holland": ["S", "E", "A"], "bonus_groups": ["Du lịch - Khách sạn - Nhà hàng", "Thể dục - Thể thao"]},
}

NUMEROLOGY_MAP = {
    1: ["Kinh tế - Quản trị kinh doanh", "Kinh doanh quốc tế", "Quân sự - Công an", "Công nghệ thông tin - Truyền thông"],
    2: ["Tâm lý học - Công tác xã hội", "Sư phạm", "Ngôn ngữ - Ngoại ngữ", "Y - Dược"],
    3: ["Nghệ thuật - Thiết kế - Âm nhạc", "Marketing - Quan hệ công chúng", "Du lịch - Khách sạn - Nhà hàng", "Văn học - Khoa học xã hội"],
    4: ["Kế toán - Kiểm toán", "Tài chính - Ngân hàng", "Xây dựng - Kiến trúc - Đô thị", "Luật - Pháp lý"],
    5: ["Du lịch - Khách sạn - Nhà hàng", "Marketing - Quan hệ công chúng", "Ngôn ngữ - Ngoại ngữ", "Kinh doanh quốc tế"],
    6: ["Y - Dược", "Sư phạm", "Tâm lý học - Công tác xã hội", "Công nghệ thực phẩm"],
    7: ["Khoa học máy tính - Kỹ thuật phần mềm", "Khoa học tự nhiên - Vật lý - Hóa học", "Địa lý - Môi trường - Trắc địa", "Toán - Thống kê ứng dụng"],
    8: ["Tài chính - Ngân hàng", "Kinh tế - Quản trị kinh doanh", "Kế toán - Kiểm toán", "Luật - Pháp lý"],
    9: ["Sư phạm", "Y - Dược", "Tâm lý học - Công tác xã hội", "Nghệ thuật - Thiết kế - Âm nhạc"],
    11: ["Tâm lý học - Công tác xã hội", "Văn học - Khoa học xã hội", "Nghệ thuật - Thiết kế - Âm nhạc", "Sư phạm"],
    22: ["Xây dựng - Kiến trúc - Đô thị", "Khoa học máy tính - Kỹ thuật phần mềm", "Kinh tế - Quản trị kinh doanh", "Công nghệ sinh học"],
    33: ["Sư phạm", "Y - Dược", "Tâm lý học - Công tác xã hội", "Nghệ thuật - Thiết kế - Âm nhạc"]
}

ZODIAC_MAP = {
    "Aries": ["Quân sự - Công an", "Kinh tế - Quản trị kinh doanh", "Thể dục - Thể thao", "Kỹ thuật ô tô - Cơ khí"],
    "Taurus": ["Kế toán - Kiểm toán", "Tài chính - Ngân hàng", "Nông nghiệp - Bảo vệ thực vật", "Nghệ thuật - Thiết kế - Âm nhạc"],
    "Gemini": ["Ngôn ngữ - Ngoại ngữ", "Marketing - Quan hệ công chúng", "Công nghệ thông tin - Truyền thông", "Du lịch - Khách sạn - Nhà hàng"],
    "Cancer": ["Y - Dược", "Tâm lý học - Công tác xã hội", "Sư phạm", "Quản lý nhà nước - Nhân lực"],
    "Leo": ["Kinh tế - Quản trị kinh doanh", "Nghệ thuật - Thiết kế - Âm nhạc", "Du lịch - Khách sạn - Nhà hàng", "Luật - Pháp lý"],
    "Virgo": ["Khoa học máy tính - Kỹ thuật phần mềm", "Kế toán - Kiểm toán", "Y - Dược", "Toán - Thống kê ứng dụng"],
    "Libra": ["Luật - Pháp lý", "Nghệ thuật - Thiết kế - Âm nhạc", "Marketing - Quan hệ công chúng", "Văn học - Khoa học xã hội"],
    "Scorpio": ["Tâm lý học - Công tác xã hội", "Y - Dược", "Khoa học tự nhiên - Vật lý - Hóa học", "Kinh doanh quốc tế"],
    "Sagittarius": ["Du lịch - Khách sạn - Nhà hàng", "Ngôn ngữ - Ngoại ngữ", "Sư phạm", "Kinh doanh quốc tế"],
    "Capricorn": ["Tài chính - Ngân hàng", "Xây dựng - Kiến trúc - Đô thị", "Quản lý nhà nước - Nhân lực", "Kế toán - Kiểm toán"],
    "Aquarius": ["Công nghệ thông tin - Truyền thông", "Khoa học máy tính - Kỹ thuật phần mềm", "Điện - Điện tử - Tự động hóa", "Khoa học tự nhiên - Vật lý - Hóa học"],
    "Pisces": ["Nghệ thuật - Thiết kế - Âm nhạc", "Tâm lý học - Công tác xã hội", "Y - Dược", "Văn học - Khoa học xã hội"]
}

def calculate_numerology(dob_str: str) -> int:
    """Calculate Life Path Number from DOB (YYYY-MM-DD)."""
    try:
        digits = [int(d) for d in dob_str if d.isdigit()]
        if not digits: return 0
        total = sum(digits)
        while total > 9 and total not in (11, 22, 33):
            total = sum(int(d) for d in str(total))
        return total
    except Exception:
        return 0

def get_zodiac_sign(dob_str: str) -> str:
    """Get Zodiac Sign from DOB (YYYY-MM-DD)."""
    try:
        dt = datetime.strptime(dob_str, "%Y-%m-%d")
        month, day = dt.month, dt.day
        if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "Aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20): return "Taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20): return "Gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22): return "Cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22): return "Leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22): return "Virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22): return "Libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21): return "Scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21): return "Sagittarius"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19): return "Capricorn"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18): return "Aquarius"
        elif (month == 2 and day >= 19) or (month == 3 and day <= 20): return "Pisces"
    except Exception:
        pass
    return ""

def get_recommendations_from_numerology(number: int) -> Tuple[List[str], List[str]]:
    """Get major groups for a Numerology number."""
    groups = NUMEROLOGY_MAP.get(number, [])
    return groups, []

def get_recommendations_from_holland(codes: str) -> Tuple[List[str], List[str]]:
    """Get major groups and keywords for a Holland code combination (e.g., 'RIA')."""
    codes = codes.upper()[:3]
    groups = []
    keywords = []
    
    for code in codes:
        if code in HOLLAND_MAP:
            groups.extend(HOLLAND_MAP[code]["major_groups"])
            keywords.extend(HOLLAND_MAP[code]["keywords"])
            
    # Remove duplicates but preserve some order
    groups = list(dict.fromkeys(groups))
    keywords = list(dict.fromkeys(keywords))
    
    return groups, keywords

def get_recommendations_from_mbti(mbti: str) -> Tuple[List[str], List[str]]:
    """Get major groups and keywords for an MBTI type."""
    mbti = mbti.upper()
    if mbti not in MBTI_MAP:
        return [], []
        
    mapping = MBTI_MAP[mbti]
    holland_codes = "".join([c for c in mapping["holland"] if c in HOLLAND_MAP])
    
    groups, keywords = get_recommendations_from_holland(holland_codes)
    
    # Add bonus groups at the beginning
    for bg in reversed(mapping.get("bonus_groups", [])):
        if bg in groups:
            groups.remove(bg)
        groups.insert(0, bg)
        
    return groups, keywords

def test():
    print("MBTI INTJ Recommendations:")
    g, k = get_recommendations_from_mbti("INTJ")
    print("Groups:", g[:5])
    print("Keywords:", k[:5])
    print("\\nHolland SEC Recommendations:")
    g, k = get_recommendations_from_holland("SEC")
    print("Groups:", g[:5])
    print("Keywords:", k[:5])

if __name__ == "__main__":
    test()
