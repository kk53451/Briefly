import 'package:flutter/material.dart';

/// 프로토타입 icons.jsx 의 아이콘 이름을 Material Icons 로 매핑.
/// 정확한 editorial-style outline 이 필요해지면 여기만 교체하면 됨.
enum AppIconName {
  home, newspaper, radio, person,
  play, pause, trackPrev, trackNext, skipBack, skipFwd,
  chevronRight, chevronLeft, chevronDown,
  search, bookmark, share,
  sun, check, volume, repeatIcon, sparkle, bell, info,
  arrowLeft, close, dots, sort, list,
  // Category glyphs
  building, trending, people, palette, globe, pin, trophy, chip,
}

IconData appIconData(AppIconName n) {
  switch (n) {
    case AppIconName.home:          return Icons.home_outlined;
    case AppIconName.newspaper:     return Icons.article_outlined;
    case AppIconName.radio:         return Icons.podcasts_outlined;
    case AppIconName.person:        return Icons.person_outline_rounded;
    case AppIconName.play:          return Icons.play_arrow_rounded;
    case AppIconName.pause:         return Icons.pause_rounded;
    case AppIconName.trackPrev:     return Icons.skip_previous_rounded;
    case AppIconName.trackNext:     return Icons.skip_next_rounded;
    case AppIconName.skipBack:      return Icons.replay_10_rounded;
    case AppIconName.skipFwd:       return Icons.forward_10_rounded;
    case AppIconName.chevronRight:  return Icons.chevron_right_rounded;
    case AppIconName.chevronLeft:   return Icons.chevron_left_rounded;
    case AppIconName.chevronDown:   return Icons.keyboard_arrow_down_rounded;
    case AppIconName.search:        return Icons.search_rounded;
    case AppIconName.bookmark:      return Icons.bookmark_border_rounded;
    case AppIconName.share:         return Icons.ios_share_rounded;
    case AppIconName.sun:           return Icons.wb_sunny_outlined;
    case AppIconName.check:         return Icons.check_rounded;
    case AppIconName.volume:        return Icons.volume_up_outlined;
    case AppIconName.repeatIcon:    return Icons.repeat_rounded;
    case AppIconName.sparkle:       return Icons.auto_awesome_outlined;
    case AppIconName.bell:          return Icons.notifications_none_rounded;
    case AppIconName.info:          return Icons.info_outline_rounded;
    case AppIconName.arrowLeft:     return Icons.arrow_back_rounded;
    case AppIconName.close:         return Icons.close_rounded;
    case AppIconName.dots:          return Icons.more_horiz_rounded;
    case AppIconName.sort:          return Icons.sort_rounded;
    case AppIconName.list:          return Icons.format_list_bulleted_rounded;
    case AppIconName.building:      return Icons.business_outlined;
    case AppIconName.trending:      return Icons.trending_up_rounded;
    case AppIconName.people:        return Icons.people_outline_rounded;
    case AppIconName.palette:       return Icons.palette_outlined;
    case AppIconName.globe:         return Icons.public_rounded;
    case AppIconName.pin:           return Icons.location_on_outlined;
    case AppIconName.trophy:        return Icons.emoji_events_outlined;
    case AppIconName.chip:          return Icons.memory_rounded;
  }
}

class AppIcon extends StatelessWidget {
  final AppIconName name;
  final double size;
  final Color? color;
  final double? weight;

  const AppIcon(this.name, {super.key, this.size = 20, this.color, this.weight});

  @override
  Widget build(BuildContext context) {
    return Icon(
      appIconData(name),
      size: size,
      color: color,
      weight: weight,
    );
  }
}
