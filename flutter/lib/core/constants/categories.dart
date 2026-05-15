import 'package:flutter/material.dart';

import '../theme/app_icons.dart';

class Category {
  final String id;        // api_name (e.g. 'economy')
  final String ko;        // 한글 표시명
  final Color color;      // 카테고리 전용 색 (muted editorial)
  final AppIconName icon;

  const Category({
    required this.id,
    required this.ko,
    required this.color,
    required this.icon,
  });
}

// id 는 backend CATEGORY_MAP 의 api_name 과 일치해야 함 (Supabase news_cards.category 컬럼).
// 지역·스포츠는 backend 가 수집하지 않으므로 제외.
const kCategories = <Category>[
  Category(id: 'politics',      ko: '정치',    color: Color(0xFFB54A3A), icon: AppIconName.building),
  Category(id: 'economy',       ko: '경제',    color: Color(0xFF4A7C59), icon: AppIconName.trending),
  Category(id: 'society',       ko: '사회',    color: Color(0xFF6B4E8A), icon: AppIconName.people),
  Category(id: 'culture',       ko: '문화',    color: Color(0xFFB85A75), icon: AppIconName.palette),
  Category(id: 'international', ko: '국제',    color: Color(0xFF3D6B8C), icon: AppIconName.globe),
  Category(id: 'tech',          ko: 'IT/과학', color: Color(0xFF5A5FB0), icon: AppIconName.chip),
];

final Map<String, Category> kCategoryById = {
  for (final c in kCategories) c.id: c,
};
