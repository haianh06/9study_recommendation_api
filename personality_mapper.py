"""
Personality & Vocation Mapper
=============================================
Maps MBTI and Holland (RIASEC) codes to Major Groups and Interest Keywords
to solve the Cold-Start problem when users don't know what to study.

Also contains the full onboarding quiz bank:
- Holland RIASEC: 36 câu chia 3 màn (tính cách, năng lực, sở thích)
- Learning Style:  16 câu màn 4 (phong cách học tập)
"""

from typing import List, Dict, Tuple, Any
from datetime import datetime


# ──────────────────────────────────────────
# Quiz Question Bank
# ──────────────────────────────────────────

# Thang điểm Likert 1-5
QUIZ_SCALE = {
    "min": 1,
    "max": 5,
    "labels": [
        "Rất không giống em",
        "Không giống lắm",
        "Bình thường",
        "Khá giống em",
        "Rất giống em"
    ]
}

# Mapping câu Holland → nhóm RIASEC
# Mỗi màn 12 câu: cặp (1,2)→R, (3,4)→I, (5,6)→A, (7,8)→S, (9,10)→E, (11,12)→C
HOLLAND_QUESTION_GROUP_MAP = {
    1: "R", 2: "R",
    3: "I", 4: "I",
    5: "A", 6: "A",
    7: "S", 8: "S",
    9: "E", 10: "E",
    11: "C", 12: "C"
}

# 36 câu Holland chia 3 màn
HOLLAND_QUESTIONS: List[Dict[str, Any]] = [
    # ── MÀN 1: Tôi là người… ──
    {"id": "H_S1_Q1",  "screen": 1, "q_num": 1,  "text": "Kín đáo và khiêm tốn",                                 "holland_group": "R"},
    {"id": "H_S1_Q2",  "screen": 1, "q_num": 2,  "text": "Có năng khiếu về kỹ thuật, máy móc",                    "holland_group": "R"},
    {"id": "H_S1_Q3",  "screen": 1, "q_num": 3,  "text": "Có đầu óc phân tích và logic",                          "holland_group": "I"},
    {"id": "H_S1_Q4",  "screen": 1, "q_num": 4,  "text": "Tò mò và ham học hỏi",                                  "holland_group": "I"},
    {"id": "H_S1_Q5",  "screen": 1, "q_num": 5,  "text": "Sáng tạo và giàu trí tưởng tượng",                      "holland_group": "A"},
    {"id": "H_S1_Q6",  "screen": 1, "q_num": 6,  "text": "Thích đổi mới và cách tân",                             "holland_group": "A"},
    {"id": "H_S1_Q7",  "screen": 1, "q_num": 7,  "text": "Thân thiện, cởi mở",                                    "holland_group": "S"},
    {"id": "H_S1_Q8",  "screen": 1, "q_num": 8,  "text": "Thích giúp đỡ người khác",                              "holland_group": "S"},
    {"id": "H_S1_Q9",  "screen": 1, "q_num": 9,  "text": "Tự tin vào bản thân",                                   "holland_group": "E"},
    {"id": "H_S1_Q10", "screen": 1, "q_num": 10, "text": "Có tham vọng và hoài bão lớn",                          "holland_group": "E"},
    {"id": "H_S1_Q11", "screen": 1, "q_num": 11, "text": "Ngăn nắp và có tổ chức",                                "holland_group": "C"},
    {"id": "H_S1_Q12", "screen": 1, "q_num": 12, "text": "Làm việc bài bản, có hệ thống",                         "holland_group": "C"},

    # ── MÀN 2: Tôi có thể… ──
    {"id": "H_S2_Q1",  "screen": 2, "q_num": 1,  "text": "Tự tìm tòi và sửa chữa các thiết bị điện tử cơ bản trong nhà",              "holland_group": "R"},
    {"id": "H_S2_Q2",  "screen": 2, "q_num": 2,  "text": "Lắp ráp dễ dàng các đồ vật mua trên Shopee (giá sách, giá để giày...)",    "holland_group": "R"},
    {"id": "H_S2_Q3",  "screen": 2, "q_num": 3,  "text": "Tư duy và khái quát các vấn đề trừu tượng",                                "holland_group": "I"},
    {"id": "H_S2_Q4",  "screen": 2, "q_num": 4,  "text": "Phân tích và xử lý dữ liệu số",                                             "holland_group": "I"},
    {"id": "H_S2_Q5",  "screen": 2, "q_num": 5,  "text": "Chơi được ít nhất một loại nhạc cụ",                                         "holland_group": "A"},
    {"id": "H_S2_Q6",  "screen": 2, "q_num": 6,  "text": "Sáng tác truyện, làm thơ hoặc vẽ tranh",                                     "holland_group": "A"},
    {"id": "H_S2_Q7",  "screen": 2, "q_num": 7,  "text": "Diễn đạt ý kiến cá nhân/truyền đạt kiến thức một cách rõ ràng, dễ hiểu",   "holland_group": "S"},
    {"id": "H_S2_Q8",  "screen": 2, "q_num": 8,  "text": "Hòa giải mâu thuẫn giữa mọi người",                                          "holland_group": "S"},
    {"id": "H_S2_Q9",  "screen": 2, "q_num": 9,  "text": "Thuyết phục người khác làm theo ý của mình",                                 "holland_group": "E"},
    {"id": "H_S2_Q10", "screen": 2, "q_num": 10, "text": "Phát biểu hoặc thuyết trình tự tin trước đám đông",                          "holland_group": "E"},
    {"id": "H_S2_Q11", "screen": 2, "q_num": 11, "text": "Làm việc tốt trong một hệ thống đã có sẵn quy trình rõ ràng",               "holland_group": "C"},
    {"id": "H_S2_Q12", "screen": 2, "q_num": 12, "text": "Ghi chép và lưu trữ số liệu, hồ sơ một cách chính xác",                     "holland_group": "C"},

    # ── MÀN 3: Tôi thích… ──
    {"id": "H_S3_Q1",  "screen": 3, "q_num": 1,  "text": "Làm việc thủ công, tự tay chế tạo đồ vật",                                   "holland_group": "R"},
    {"id": "H_S3_Q2",  "screen": 3, "q_num": 2,  "text": "Tham gia các hoạt động vận động thể chất tích cực",                          "holland_group": "R"},
    {"id": "H_S3_Q3",  "screen": 3, "q_num": 3,  "text": "Làm các thí nghiệm hoặc phân tích trong phòng thực hành",                     "holland_group": "I"},
    {"id": "H_S3_Q4",  "screen": 3, "q_num": 4,  "text": "Chơi các trò chơi trí tuệ, giải đố, hack não",                               "holland_group": "I"},
    {"id": "H_S3_Q5",  "screen": 3, "q_num": 5,  "text": "Vẽ tranh, điêu khắc hoặc làm đồ gốm nghệ thuật",                             "holland_group": "A"},
    {"id": "H_S3_Q6",  "screen": 3, "q_num": 6,  "text": "Decor, trang trí nhà cửa hoặc không gian sống",                              "holland_group": "A"},
    {"id": "H_S3_Q7",  "screen": 3, "q_num": 7,  "text": "Tham gia các hoạt động tình nguyện, thiện nguyện",                           "holland_group": "S"},
    {"id": "H_S3_Q8",  "screen": 3, "q_num": 8,  "text": "Đứng ra tổ chức các sự kiện, buổi tiệc tùng",                                "holland_group": "S"},
    {"id": "H_S3_Q9",  "screen": 3, "q_num": 9,  "text": "Đưa ra các quyết định có tầm ảnh hưởng đến tập thể",                         "holland_group": "E"},
    {"id": "H_S3_Q10", "screen": 3, "q_num": 10, "text": "Chinh phục các cột mốc, danh hiệu hoặc giải thưởng danh giá",                "holland_group": "E"},
    {"id": "H_S3_Q11", "screen": 3, "q_num": 11, "text": "Làm việc trực tiếp với các con số hoặc bảng biểu tính toán",                 "holland_group": "C"},
    {"id": "H_S3_Q12", "screen": 3, "q_num": 12, "text": "Giữ cho môi trường xung quanh luôn gọn gàng, ngăn nắp và sạch sẽ",           "holland_group": "C"},
]

# 16 câu Learning Style (màn 4)
LEARNING_STYLE_QUESTIONS: List[Dict[str, Any]] = [
    # Active / Collaborative
    {"id": "LS_Q1",  "q_num": 1,  "text": "Em hiểu bài nhanh hơn khi được trao đổi với bạn hoặc giáo viên.",           "style_group": "active"},
    {"id": "LS_Q2",  "q_num": 2,  "text": "Khi giải thích lại cho người khác, em nhớ kiến thức lâu hơn.",              "style_group": "active"},
    {"id": "LS_Q3",  "q_num": 3,  "text": "Em thích học trong lớp có nhiều hoạt động hỏi đáp.",                        "style_group": "active"},
    {"id": "LS_Q4",  "q_num": 4,  "text": "Em dễ mất tập trung nếu chỉ ngồi nghe giảng một chiều.",                    "style_group": "active"},
    # Visual
    {"id": "LS_Q5",  "q_num": 5,  "text": "Em dễ nhớ kiến thức hơn khi được nhìn sơ đồ, bảng biểu hoặc hình minh họa.","style_group": "visual"},
    {"id": "LS_Q6",  "q_num": 6,  "text": "Em thích giáo viên tóm tắt bài bằng mindmap.",                              "style_group": "visual"},
    {"id": "LS_Q7",  "q_num": 7,  "text": "Khi học bài, em thường dùng màu sắc, ký hiệu hoặc gạch đầu dòng.",          "style_group": "visual"},
    {"id": "LS_Q8",  "q_num": 8,  "text": "Em hiểu bài nhanh hơn khi kiến thức được trình bày trực quan.",             "style_group": "visual"},
    # Practical / Contextual
    {"id": "LS_Q9",  "q_num": 9,  "text": "Em chỉ thật sự hiểu bài khi có ví dụ cụ thể.",                              "style_group": "practical"},
    {"id": "LS_Q10", "q_num": 10, "text": "Em thích học qua các tình huống gần với đời sống hoặc đề thi thật.",         "style_group": "practical"},
    {"id": "LS_Q11", "q_num": 11, "text": "Nếu chỉ học lý thuyết, em thấy kiến thức hơi khó nhớ.",                     "style_group": "practical"},
    {"id": "LS_Q12", "q_num": 12, "text": "Em thường hỏi: 'Cái này dùng để làm gì?' hoặc 'Thi sẽ hỏi kiểu nào?'",     "style_group": "practical"},
    # Kinesthetic / Action-based
    {"id": "LS_Q13", "q_num": 13, "text": "Em học tốt nhất khi được làm bài ngay sau khi học lý thuyết.",              "style_group": "kinesthetic"},
    {"id": "LS_Q14", "q_num": 14, "text": "Em thích vừa học vừa luyện, sai đâu sửa đó.",                               "style_group": "kinesthetic"},
    {"id": "LS_Q15", "q_num": 15, "text": "Em thấy việc làm mini project/nhiệm vụ học tập giúp em nhớ lâu hơn.",       "style_group": "kinesthetic"},
    {"id": "LS_Q16", "q_num": 16, "text": "Em không thích học quá nhiều lý thuyết trước khi được thực hành.",           "style_group": "kinesthetic"},
]

# Mô tả chi tiết cho từng nhóm Holland (chuẩn UX Writer, tone hướng học sinh)
HOLLAND_DESCRIPTIONS = {
    "R": {
        "code": "R",
        "short_name": "Thực tế",
        "full_name": "Thực Tế (Realistic)",
        "tagline": "Người xây dựng & tạo ra thế giới",
        "description": "Em là người của hành động – thích làm hơn là nói. Em cảm thấy thoải mái nhất khi được làm việc bằng tay, sử dụng công cụ, máy móc hoặc tham gia các hoạt động đòi hỏi sức lực và kỹ năng thực tế. Em không thích ngồi yên một chỗ và luôn muốn thấy kết quả cụ thể, hữu hình từ công việc mình tự tay làm ra.",
        "strengths": [
            "Kỹ năng thực hành vượt trội, khéo tay và có tay nghề",
            "Tư duy cơ học, kỹ thuật tốt – giỏi cảm nhận không gian",
            "Kiên nhẫn và bền bỉ trong công việc dài hơi",
            "Giải quyết vấn đề thực tế, không lý thuyết suông"
        ],
        "traits": ["Thực hành", "Kỹ thuật", "Cụ thể", "Độc lập", "Bền bỉ"],
        "suitable_majors": [
            "Kỹ thuật ô tô - Cơ khí",
            "Điện - Điện tử - Tự động hóa",
            "Xây dựng - Kiến trúc - Đô thị",
            "Nông - Lâm - Thú y",
            "Kỹ thuật máy tính - Mạng & Vi mạch",
            "Vật liệu - Hóa chất - Luyện kim"
        ],
        "suggested_careers": [
            "Kỹ sư cơ khí / Kỹ sư xây dựng",
            "Kỹ thuật viên điện tử / Lập trình nhúng",
            "Kiến trúc sư / Kỹ sư hạ tầng",
            "Kỹ sư nông nghiệp / Lâm nghiệp",
            "Chuyên gia vận hành hệ thống"
        ],
        "work_environment": "Em phù hợp với môi trường thực tế, có thể di chuyển, tự tay tạo ra sản phẩm hơn là ngồi văn phòng cả ngày."
    },
    "I": {
        "code": "I",
        "short_name": "Nghiên cứu",
        "full_name": "Nghiên Cứu (Investigative)",
        "tagline": "Người giải mã những bí ẩn của thế giới",
        "description": "Em là người của tư duy – luôn đặt câu hỏi \"Tại sao?\" và không ngừng tìm kiếm câu trả lời. Em có xu hướng yêu thích việc tìm hiểu, phân tích và khám phá bản chất sự vật. Em thường phù hợp với những môi trường cần tư duy logic, quan sát sâu, đặt câu hỏi và giải quyết vấn đề bằng lý luận.",
        "strengths": [
            "Tư duy phân tích và logic xuất sắc",
            "Khả năng tiếp thu kiến thức nhanh, học sâu",
            "Kiên nhẫn và tỉ mỉ trong nghiên cứu",
            "Tư duy độc lập, không ngại đặt câu hỏi"
        ],
        "traits": ["Phân tích", "Tư duy logic", "Tò mò", "Độc lập", "Học thuật"],
        "suitable_majors": [
            "Khoa học máy tính - Kỹ thuật phần mềm",
            "Khoa học dữ liệu - Trí tuệ nhân tạo",
            "Y - Dược",
            "Khoa học tự nhiên - Vật lý - Hóa học",
            "Công nghệ sinh học",
            "Toán - Thống kê ứng dụng"
        ],
        "suggested_careers": [
            "Kỹ sư phần mềm / Khoa học dữ liệu",
            "Bác sĩ / Dược sĩ / Nghiên cứu y khoa",
            "Nhà nghiên cứu / Giảng viên đại học",
            "Chuyên gia phân tích tài chính",
            "Kỹ sư AI / Machine Learning"
        ],
        "work_environment": "Em làm việc tốt nhất khi được tự do khám phá ý tưởng, nghiên cứu chuyên sâu và có không gian để suy nghĩ độc lập."
    },
    "A": {
        "code": "A",
        "short_name": "Nghệ thuật",
        "full_name": "Nghệ Thuật (Artistic)",
        "tagline": "Người biến ý tưởng thành tác phẩm",
        "description": "Em là người của sáng tạo – có trí tưởng tượng phong phú và luôn muốn thể hiện bản thân qua ngôn ngữ, hình ảnh, âm thanh hay chuyển động. Em không thích sự gò bó, quy tắc cứng nhắc và làm việc tốt nhất khi được tự do thể hiện cá tính riêng.",
        "strengths": [
            "Óc sáng tạo và tư duy đổi mới",
            "Nhạy cảm với thẩm mỹ và cái đẹp",
            "Khả năng biểu đạt và kể chuyện hấp dẫn",
            "Tư duy \"out of the box\", không bị giới hạn"
        ],
        "traits": ["Sáng tạo", "Biểu đạt", "Độc đáo", "Nhạy cảm", "Tự do"],
        "suitable_majors": [
            "Nghệ thuật - Thiết kế - Âm nhạc",
            "Ngôn ngữ - Ngoại ngữ",
            "Văn học - Khoa học xã hội",
            "Dệt may - Thời trang",
            "Xây dựng - Kiến trúc - Đô thị",
            "Marketing - Quan hệ công chúng"
        ],
        "suggested_careers": [
            "Nhà thiết kế đồ họa / UI/UX Designer",
            "Kiến trúc sư / Nhà thiết kế nội thất",
            "Nhà văn / Biên kịch / Nhà báo",
            "Nhạc sĩ / Nghệ sĩ biểu diễn",
            "Chuyên gia sáng tạo nội dung / Content Creator"
        ],
        "work_environment": "Em phát huy tốt nhất trong môi trường sáng tạo, ít quy tắc cứng nhắc, được khuyến khích thể hiện ý tưởng và cá tính riêng."
    },
    "S": {
        "code": "S",
        "short_name": "Xã hội",
        "full_name": "Xã Hội (Social)",
        "tagline": "Người kết nối và truyền cảm hứng",
        "description": "Em là người của con người – luôn quan tâm, lắng nghe và sẵn sàng giúp đỡ người xung quanh. Em có khả năng thấu hiểu cảm xúc của người khác và làm cho mọi người cảm thấy được coi trọng. Em làm việc tốt nhất khi có cơ hội giao lưu, hỗ trợ và tạo sự thay đổi tích cực cho cộng đồng.",
        "strengths": [
            "Kỹ năng giao tiếp và lắng nghe xuất sắc",
            "Đồng cảm sâu sắc, hiểu tâm lý người khác",
            "Khả năng dạy dỗ, hướng dẫn và truyền đạt",
            "Xây dựng mối quan hệ bền chặt, tạo sự tin tưởng"
        ],
        "traits": ["Đồng cảm", "Giao tiếp", "Hợp tác", "Chăm sóc", "Kiên nhẫn"],
        "suitable_majors": [
            "Sư phạm",
            "Tâm lý học - Công tác xã hội",
            "Y - Dược",
            "Du lịch - Khách sạn - Nhà hàng",
            "Quản lý nhà nước - Nhân lực",
            "Ngôn ngữ - Ngoại ngữ"
        ],
        "suggested_careers": [
            "Giáo viên / Giảng viên",
            "Chuyên viên tư vấn tâm lý / Tham vấn học đường",
            "Nhân viên công tác xã hội",
            "Chuyên gia nhân sự (HR) / L&D",
            "Hướng dẫn viên du lịch / Event Planner"
        ],
        "work_environment": "Em phát huy tốt trong môi trường tập thể, nơi em có thể tương tác, hỗ trợ và tạo ra tác động tích cực đến mọi người."
    },
    "E": {
        "code": "E",
        "short_name": "Doanh nghiệp",
        "full_name": "Doanh Nghiệp (Enterprising)",
        "tagline": "Người lãnh đạo & tạo ra ảnh hưởng",
        "description": "Em là người của hành động và tham vọng – luôn hướng đến kết quả, thích lãnh đạo và có sức hút tự nhiên với người xung quanh. Em giỏi thuyết phục, đàm phán và truyền cảm hứng cho người khác đi theo tầm nhìn của mình. Em không ngại rủi ro nếu cơ hội xứng đáng.",
        "strengths": [
            "Khả năng lãnh đạo và ảnh hưởng tự nhiên",
            "Kỹ năng thuyết phục và đàm phán sắc bén",
            "Tư duy chiến lược, nhìn xa trông rộng",
            "Dám nghĩ dám làm, không ngại thất bại"
        ],
        "traits": ["Lãnh đạo", "Thuyết phục", "Tham vọng", "Quyết đoán", "Năng động"],
        "suitable_majors": [
            "Kinh tế - Quản trị kinh doanh",
            "Marketing - Quan hệ công chúng",
            "Luật - Pháp lý",
            "Kinh doanh quốc tế",
            "Tài chính - Ngân hàng",
            "Hàng không"
        ],
        "suggested_careers": [
            "Doanh nhân / Startup Founder",
            "Giám đốc kinh doanh / Sales Director",
            "Luật sư / Chuyên gia pháp lý",
            "Chuyên gia Marketing / Brand Manager",
            "Nhà quản lý dự án / Product Manager"
        ],
        "work_environment": "Em làm việc tốt nhất khi được giao quyền quyết định, có cơ hội lãnh đạo nhóm và theo đuổi những mục tiêu có ảnh hưởng lớn."
    },
    "C": {
        "code": "C",
        "short_name": "Quy trình",
        "full_name": "Quy Trình (Conventional)",
        "tagline": "Người đảm bảo mọi thứ hoạt động hoàn hảo",
        "description": "Em là người của sự chính xác – có tư duy hệ thống, thích làm việc có kế hoạch và đảm bảo mọi thứ vận hành trơn tru. Em giỏi xử lý số liệu, quản lý thông tin và xây dựng quy trình. Em mang lại sự ổn định và đáng tin cậy cho bất kỳ tổ chức nào em tham gia.",
        "strengths": [
            "Tư duy hệ thống và có tổ chức xuất sắc",
            "Chính xác, tỉ mỉ trong từng chi tiết",
            "Khả năng quản lý dữ liệu và quy trình tốt",
            "Đáng tin cậy, hoàn thành công việc đúng hạn"
        ],
        "traits": ["Cẩn thận", "Có tổ chức", "Chính xác", "Đáng tin cậy", "Kiên định"],
        "suitable_majors": [
            "Kế toán - Kiểm toán",
            "Tài chính - Ngân hàng",
            "Quản lý nhà nước - Nhân lực",
            "Toán - Thống kê ứng dụng",
            "Công nghệ thông tin - Truyền thông",
            "Hàng hải - Logistics"
        ],
        "suggested_careers": [
            "Kế toán viên / Kiểm toán viên",
            "Chuyên viên phân tích tài chính",
            "Quản lý hành chính / Văn phòng",
            "Chuyên gia Logistics / Supply Chain",
            "Lập trình viên backend / Kỹ sư hệ thống"
        ],
        "work_environment": "Em phát huy tốt trong môi trường có cấu trúc rõ ràng, quy trình minh bạch và tiêu chuẩn cụ thể để tuân theo."
    }
}

# Mô tả và tips cho từng Learning Style
LEARNING_STYLE_MAP = {
    "active": {
        "name": "Người Học Chủ Động (Active/Collaborative)",
        "description": "Em học tốt nhất thông qua trao đổi, thảo luận và tương tác với người khác. Em tiếp thu nhanh khi được giải thích lại cho ai đó.",
        "study_tips": [
            "Tham gia nhóm học tập để trao đổi và thảo luận",
            "Dạy lại kiến thức cho bạn bè để nhớ lâu hơn",
            "Đặt câu hỏi trong lớp và tham gia hỏi đáp",
            "Học qua podcast, video có tương tác",
            "Dùng flashcard và quiz để ôn tập"
        ]
    },
    "visual": {
        "name": "Người Học Thị Giác (Visual)",
        "description": "Em tiếp thu tốt qua hình ảnh, sơ đồ và biểu đồ. Não em xử lý thông tin trực quan hiệu quả hơn văn bản thuần túy.",
        "study_tips": [
            "Vẽ mindmap và sơ đồ tư duy cho mỗi chủ đề",
            "Dùng màu sắc để highlight và phân loại ghi chú",
            "Xem video bài giảng có hình ảnh minh họa",
            "Tạo infographic tóm tắt kiến thức",
            "Học với bảng trắng, viết và vẽ khi ôn bài"
        ]
    },
    "practical": {
        "name": "Người Học Thực Dụng (Practical/Contextual)",
        "description": "Em học hiệu quả nhất khi kiến thức gắn liền với ví dụ thực tế và ứng dụng cụ thể. Em cần biết 'để làm gì' trước khi học.",
        "study_tips": [
            "Luôn tìm ví dụ thực tế trước khi học lý thuyết",
            "Học qua case study và tình huống thực tiễn",
            "Liên hệ kiến thức với đời sống hàng ngày",
            "Tập giải đề thi thật để hiểu yêu cầu",
            "Xem ứng dụng của kiến thức trong các ngành nghề"
        ]
    },
    "kinesthetic": {
        "name": "Người Học Thực Hành (Kinesthetic)",
        "description": "Em học tốt nhất khi được trực tiếp làm, thực hành và thử nghiệm. Em nhớ lâu qua hành động hơn là đọc hay nghe.",
        "study_tips": [
            "Làm bài tập ngay sau khi học lý thuyết",
            "Thực hiện mini project để áp dụng kiến thức",
            "Học qua thí nghiệm, thực hành trực tiếp",
            "Chia nhỏ mục tiêu và tự kiểm tra thường xuyên",
            "Ghi chú tay khi học (viết giúp não ghi nhớ tốt hơn)"
        ]
    }
}


# ──────────────────────────────────────────
# Scoring Functions
# ──────────────────────────────────────────

def score_holland_answers(answers: Dict[str, int]) -> Dict[str, Any]:
    """
    Tính điểm Holland từ answers dict.

    Args:
        answers: dict {question_id: score (1-5)}
                 e.g. {"H_S1_Q1": 4, "H_S1_Q2": 3, ...}

    Returns:
        {
          "scores": {"R": int, "I": int, "A": int, "S": int, "E": int, "C": int},
          "holland_code": str (e.g. "RIA"),
          "percentages": {"R": float, ...},
          "max_score": int   # điểm tối đa có thể đạt (= số câu × 5)
        }
    """
    scores: Dict[str, int] = {g: 0 for g in "RIASEC"}
    question_map = {q["id"]: q["holland_group"] for q in HOLLAND_QUESTIONS}

    for qid, val in answers.items():
        if qid in question_map:
            group = question_map[qid]
            scores[group] += max(1, min(5, int(val)))

    # Max score mỗi nhóm = 6 câu × 5 = 30
    max_per_group = 30
    total = sum(scores.values()) or 1
    percentages = {g: round(scores[g] / max_per_group * 100, 1) for g in "RIASEC"}

    # Holland code = 3 nhóm cao nhất
    sorted_groups = sorted(scores.keys(), key=lambda g: scores[g], reverse=True)
    holland_code = "".join(sorted_groups[:3])

    # Chart data theo thứ tự cố định R-I-A-S-E-C (cho line chart trên UI)
    chart_data = [
        {
            "code": g,
            "short_name": HOLLAND_DESCRIPTIONS.get(g, {}).get("short_name", g),
            "score": percentages[g]
        }
        for g in "RIASEC"
    ]

    # Top 3 nhóm cao nhất (cho footer UI)
    top_3_groups = [
        {
            "rank": i + 1,
            "code": g,
            "short_name": HOLLAND_DESCRIPTIONS.get(g, {}).get("short_name", g),
            "score": percentages[g]
        }
        for i, g in enumerate(sorted_groups[:3])
    ]

    return {
        "scores": scores,
        "holland_code": holland_code,
        "percentages": percentages,
        "max_score": max_per_group,
        "chart_data": chart_data,
        "top_3_groups": top_3_groups,
    }


def score_learning_style(answers: Dict[str, int]) -> Dict[str, Any]:
    """
    Tính điểm Learning Style từ answers dict.

    Args:
        answers: dict {question_id: score (1-5)}
                 e.g. {"LS_Q1": 5, "LS_Q2": 4, ...}

    Returns:
        {
          "scores": {"active": int, "visual": int, "practical": int, "kinesthetic": int},
          "dominant_style": str,
          "percentages": {style: float, ...},
          "max_score": int
        }
    """
    style_groups = ["active", "visual", "practical", "kinesthetic"]
    scores: Dict[str, int] = {s: 0 for s in style_groups}
    question_map = {q["id"]: q["style_group"] for q in LEARNING_STYLE_QUESTIONS}

    for qid, val in answers.items():
        if qid in question_map:
            style = question_map[qid]
            scores[style] += max(1, min(5, int(val)))

    # Max score mỗi style = 4 câu × 5 = 20
    max_per_style = 20
    percentages = {s: round(scores[s] / max_per_style * 100, 1) for s in style_groups}
    dominant_style = max(scores, key=lambda s: scores[s])

    return {
        "scores": scores,
        "dominant_style": dominant_style,
        "percentages": percentages,
        "max_score": max_per_style
    }


def get_personality_insights(
    holland_code: str,
    dominant_style: str
) -> Dict[str, Any]:
    """
    Tạo insights phân tích tính cách và phong cách học tập.
    """
    # Holland insights từ 3 ký tự đầu
    primary = holland_code[0] if holland_code else ""
    holland_info = HOLLAND_DESCRIPTIONS.get(primary, {})
    style_info = LEARNING_STYLE_MAP.get(dominant_style, {})

    return {
        "holland_primary": primary,
        "holland_name": holland_info.get("full_name", ""),
        "holland_description": holland_info.get("description", ""),
        "holland_traits": holland_info.get("traits", []),
        "suggested_careers": holland_info.get("suggested_careers", []),
        "learning_style_name": style_info.get("name", ""),
        "learning_style_description": style_info.get("description", ""),
        "study_tips": style_info.get("study_tips", [])
    }


def get_highlight_group(holland_code: str) -> Dict[str, Any]:
    """
    Trả về dữ liệu đầy đủ của nhóm Holland nổi trội nhất (#1)
    để hiển thị phần "Nhóm nổi bật nhất" trên UI.
    """
    primary = holland_code[0] if holland_code else ""
    info = HOLLAND_DESCRIPTIONS.get(primary, {})
    return {
        "code": primary,
        "short_name": info.get("short_name", ""),
        "full_name": info.get("full_name", ""),
        "tagline": info.get("tagline", ""),
        "description": info.get("description", ""),
        "strengths": info.get("strengths", []),
        "suitable_majors": info.get("suitable_majors", []),
        "work_environment": info.get("work_environment", ""),
    }


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

# Dữ liệu Thần số học (Life Path Number)
NUMEROLOGY_DESCRIPTIONS = {
    2: {
        "number": 2,
        "keywords": ["Trực giác", "Hòa bình", "Đồng cảm"],
        "strengths": ["Khả năng thấu hiểu và lắng nghe xuất sắc", "Giỏi ngoại giao và hòa giải", "Làm việc nhóm cực kỳ tốt", "Đáng tin cậy và trung thành"],
        "weaknesses": ["Dễ bị tổn thương, nhạy cảm quá mức", "Hay do dự, thiếu quyết đoán", "Thường hạ thấp bản thân", "Sợ làm phiền người khác"],
        "development": ["Học cách nói 'Không' khi cần thiết", "Tin tưởng vào trực giác của bản thân", "Phát triển sự tự tin và độc lập", "Tránh việc phụ thuộc quá nhiều vào người khác"],
        "core_orientation": ["Hỗ trợ, kết nối cộng đồng", "Nghệ thuật, thiết kế", "Tâm lý học, tư vấn", "Giáo dục, đào tạo"]
    },
    3: {
        "number": 3,
        "keywords": ["Sáng tạo", "Giao tiếp", "Lạc quan"],
        "strengths": ["Tư duy sáng tạo, nhiều ý tưởng", "Giao tiếp duyên dáng, hài hước", "Năng lượng tích cực, truyền cảm hứng", "Thích nghi nhanh với môi trường mới"],
        "weaknesses": ["Thiếu tập trung, hay bỏ dở giữa chừng", "Dễ bốc đồng trong chi tiêu và cảm xúc", "Đôi khi quá để ý đến vẻ bề ngoài", "Thiếu kiên nhẫn"],
        "development": ["Rèn luyện tính kỷ luật và tổ chức", "Học cách quản lý tài chính và cảm xúc", "Biết lắng nghe người khác nhiều hơn", "Kiên trì theo đuổi mục tiêu đến cùng"],
        "core_orientation": ["Nghệ thuật biểu diễn, sáng tạo nội dung", "Truyền thông, báo chí", "Marketing, bán hàng", "Giảng dạy, diễn giả"]
    },
    4: {
        "number": 4,
        "keywords": ["Thực tế", "Kỷ luật", "Ổn định"],
        "strengths": ["Làm việc có kế hoạch, cực kỳ kỷ luật", "Đáng tin cậy, thực tế, vững chắc", "Chịu được áp lực cao, bền bỉ", "Tổ chức và quản lý xuất sắc"],
        "weaknesses": ["Đôi khi quá bảo thủ, cứng nhắc", "Hay lo lắng thái quá về vật chất", "Khó thể hiện cảm xúc cá nhân", "Làm việc quá sức (Workaholic)"],
        "development": ["Học cách linh hoạt và cởi mở hơn", "Cân bằng giữa công việc và cuộc sống", "Cho phép bản thân được thư giãn, sáng tạo", "Lắng nghe những ý tưởng mới mẻ"],
        "core_orientation": ["Kỹ thuật, công nghệ, xây dựng", "Kế toán, tài chính, kiểm toán", "Quản lý dự án, vận hành", "Luật pháp, hành chính"]
    },
    5: {
        "number": 5,
        "keywords": ["Tự do", "Khám phá", "Linh hoạt"],
        "strengths": ["Cực kỳ linh hoạt, thích nghi nhanh", "Năng động, dũng cảm, thích mạo hiểm", "Tư duy nhạy bén, đa tài", "Khả năng bán hàng, thuyết phục tốt"],
        "weaknesses": ["Nhanh chán, thiếu sự kiên nhẫn", "Hay thay đổi định hướng đột ngột", "Dễ rơi vào các thói quen xấu nếu buồn chán", "Thiếu tính kỷ luật"],
        "development": ["Cam kết lâu dài với mục tiêu cốt lõi", "Sử dụng sự tự do một cách có trách nhiệm", "Học cách kiên nhẫn với các quy trình", "Lựa chọn bạn bè và môi trường cẩn thận"],
        "core_orientation": ["Du lịch, khách sạn, sự kiện", "Bán hàng, kinh doanh tự do", "Phóng viên, nhà điều tra", "Giải trí, truyền thông"]
    },
    6: {
        "number": 6,
        "keywords": ["Gia đình", "Chăm sóc", "Trách nhiệm"],
        "strengths": ["Giàu tình yêu thương, tận tâm", "Có tinh thần trách nhiệm cực kỳ cao", "Thẩm mỹ tốt, yêu cái đẹp", "Khả năng chữa lành cho người khác"],
        "weaknesses": ["Hay ôm đồm, lo chuyện bao đồng", "Dễ bị lợi dụng lòng tốt", "Đôi khi thích kiểm soát người thân", "Quên mất việc chăm sóc bản thân"],
        "development": ["Biết thiết lập ranh giới cá nhân", "Cho người khác tự tự lập", "Yêu thương bản thân nhiều hơn", "Học cách buông bỏ sự hoàn hảo"],
        "core_orientation": ["Y tế, chăm sóc sức khỏe", "Giáo dục mầm non, tâm lý", "Thiết kế nội thất, thời trang", "Công tác xã hội, nhân sự"]
    },
    7: {
        "number": 7,
        "keywords": ["Triết lý", "Nghiên cứu", "Tâm linh"],
        "strengths": ["Tư duy phân tích sâu sắc, độc lập", "Khả năng đúc kết chân lý từ trải nghiệm", "Học hỏi nhanh, quan sát nhạy bén", "Tin vào khoa học hoặc tâm linh sâu sắc"],
        "weaknesses": ["Thích thu mình lại, khó mở lòng", "Đôi khi quá đa nghi, lạnh lùng", "Dễ bị cô lập khỏi đám đông", "Suy nghĩ quá nhiều (Overthinking)"],
        "development": ["Học cách kết nối và chia sẻ cảm xúc", "Tin tưởng vào người khác nhiều hơn", "Cân bằng giữa lý trí và trực giác", "Biết tận hưởng cuộc sống hiện tại"],
        "core_orientation": ["Nghiên cứu khoa học, dữ liệu", "Giảng viên đại học, triết học", "Lập trình, chuyên gia IT", "Chuyên gia tâm lý, tôn giáo"]
    },
    8: {
        "number": 8,
        "keywords": ["Quyền lực", "Vật chất", "Tham vọng"],
        "strengths": ["Tố chất lãnh đạo, điều hành xuất sắc", "Nhạy bén với kinh doanh, tài chính", "Độc lập, tự tin và đầy tham vọng", "Có khả năng quản lý quy mô lớn"],
        "weaknesses": ["Đề cao quá mức vật chất và địa vị", "Đôi khi lạnh lùng, độc đoán", "Tham công tiếc việc", "Dễ mất cân bằng nếu kinh doanh thất bại"],
        "development": ["Sử dụng quyền lực vì lợi ích chung", "Cân bằng giữa tiền bạc và tinh thần", "Lắng nghe và tôn trọng cấp dưới", "Học cách biết ơn những điều nhỏ bé"],
        "core_orientation": ["Kinh doanh, khởi nghiệp", "Quản lý, điều hành doanh nghiệp", "Tài chính, chứng khoán, đầu tư", "Luật sư, bất động sản"]
    },
    9: {
        "number": 9,
        "keywords": ["Nhân đạo", "Lý tưởng", "Cống hiến"],
        "strengths": ["Tấm lòng bao dung, vị tha", "Tầm nhìn xa trông rộng", "Tinh thần cống hiến vì cộng đồng mạnh mẽ", "Khả năng truyền cảm hứng lớn"],
        "weaknesses": ["Quá lý tưởng hóa, thiếu thực tế", "Dễ bị lừa gạt, lợi dụng", "Khó kiểm soát cảm xúc", "Ôm đồm nhiều việc bao đồng"],
        "development": ["Kết nối lý tưởng với thực tế xã hội", "Học cách từ chối để bảo vệ năng lượng", "Quản lý tài chính cá nhân chặt chẽ", "Tập trung vào hiện tại thay vì quá khứ"],
        "core_orientation": ["Hoạt động xã hội, phi chính phủ", "Giáo dục, y tế cộng đồng", "Lĩnh vực tôn giáo, tâm lý", "Nghệ thuật hướng tới nhân sinh"]
    },
    10: {
        "number": 10, # (tức là 1)
        "keywords": ["Độc lập", "Tiên phong", "Tự chủ"],
        "strengths": ["Khả năng lãnh đạo, mở đường", "Tự tin, quyết đoán, bản lĩnh", "Tràn đầy năng lượng, sức sáng tạo", "Dám nghĩ dám làm, không ngại khó"],
        "weaknesses": ["Cái tôi lớn, bướng bỉnh", "Khó làm việc nhóm dưới quyền người khác", "Đôi khi thiếu sự thấu cảm", "Thiếu kiên nhẫn với tiểu tiết"],
        "development": ["Học cách nhún nhường và lắng nghe", "Phát triển kỹ năng hợp tác (teamwork)", "Rèn luyện sự kiên nhẫn", "Cân nhắc kỹ trước khi đưa ra quyết định"],
        "core_orientation": ["Lãnh đạo, quản lý cấp cao", "Khởi nghiệp (Startup founder)", "Chuyên gia độc lập, tư vấn", "Lĩnh vực sáng tạo, tiên phong"]
    },
    11: {
        "number": 11,
        "keywords": ["Trực giác", "Tầm nhìn", "Truyền cảm hứng"],
        "strengths": ["Trực giác mạnh mẽ phi thường", "Sứ mệnh truyền cảm hứng cho người khác", "Thấu hiểu sự đồng cảm sâu sắc", "Nhạy bén với các thông điệp tâm linh/nghệ thuật"],
        "weaknesses": ["Dễ nhạy cảm, suy nghĩ nhiều", "Kỳ vọng cao dễ dẫn đến thất vọng", "Khó tập trung khi thiếu mục tiêu lý tưởng", "Dễ kiệt sức nếu ôm đồm"],
        "development": ["Rèn luyện kỷ luật và sự tập trung", "Tin tưởng tuyệt đối vào trực giác", "Phát triển kỹ năng giao tiếp truyền cảm hứng", "Theo đuổi mục tiêu dài hạn, thực tế hóa lý tưởng"],
        "core_orientation": ["Tâm lý học, giáo dục, khai vấn (coaching)", "Truyền thông, diễn giả", "Nghệ thuật, văn học, thiết kế", "Nghiên cứu tôn giáo, tâm linh"]
    },
    22: {
        "number": 22,
        "keywords": ["Kiến tạo", "Tầm vóc", "Thực tiễn"],
        "strengths": ["Bậc thầy kiến tạo (Master Builder)", "Khả năng biến giấc mơ lớn thành hiện thực", "Tầm nhìn bao quát kết hợp năng lực thực thi", "Năng lượng làm việc vô hạn"],
        "weaknesses": ["Dễ bị áp lực vì lý tưởng quá lớn", "Có thể trở nên độc đoán, khắc nghiệt", "Nếu thiếu định hướng, có thể rất lười biếng", "Gặp khó khăn trong việc diễn đạt cảm xúc"],
        "development": ["Chia nhỏ mục tiêu lớn thành bước nhỏ", "Giữ sự linh hoạt trong kế hoạch", "Kết nối cảm xúc với những người xung quanh", "Tin tưởng giao quyền cho người khác"],
        "core_orientation": ["Lãnh đạo quốc gia, tập đoàn lớn", "Kiến trúc sư, quy hoạch đô thị", "Tổ chức phi chính phủ quy mô lớn", "Khoa học công nghệ đột phá"]
    }
}

def get_numerology_insights(dob_str: str) -> dict:
    """Calculate and return Numerology insights based on DOB."""
    number = calculate_numerology(dob_str)
    # Convert 1 -> 10 per standard Vietnamese Numerology convention if applicable, or treat 1 as 10.
    if number == 1:
        number = 10
    
    # Defaults for unmatched numbers
    insight = NUMEROLOGY_DESCRIPTIONS.get(number, {
        "number": number,
        "keywords": ["Chưa cập nhật"],
        "strengths": ["Chưa cập nhật"],
        "weaknesses": ["Chưa cập nhật"],
        "development": ["Chưa cập nhật"],
        "core_orientation": ["Chưa cập nhật"]
    })
    return insight


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
