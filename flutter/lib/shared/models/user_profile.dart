/// `public.profiles` row 1:1 매핑.
/// handle_new_user 트리거가 auth.users INSERT 시 자동 채움.
class UserProfile {
  final String id;           // auth.users.id (uuid)
  final String? nickname;
  final String? profileImage;
  final List<String> interests;
  final bool onboardingCompleted;
  final DateTime createdAt;

  const UserProfile({
    required this.id,
    required this.nickname,
    required this.profileImage,
    required this.interests,
    required this.onboardingCompleted,
    required this.createdAt,
  });

  factory UserProfile.fromRow(Map<String, dynamic> row) {
    final rawInterests = row['interests'];
    return UserProfile(
      id: row['id'] as String,
      nickname: row['nickname'] as String?,
      profileImage: row['profile_image'] as String?,
      interests: rawInterests is List
          ? rawInterests.whereType<String>().toList()
          : const <String>[],
      onboardingCompleted: (row['onboarding_completed'] as bool?) ?? false,
      createdAt: DateTime.parse(row['created_at'] as String).toLocal(),
    );
  }

  UserProfile copyWith({
    String? nickname,
    String? profileImage,
    List<String>? interests,
    bool? onboardingCompleted,
  }) {
    return UserProfile(
      id: id,
      nickname: nickname ?? this.nickname,
      profileImage: profileImage ?? this.profileImage,
      interests: interests ?? this.interests,
      onboardingCompleted: onboardingCompleted ?? this.onboardingCompleted,
      createdAt: createdAt,
    );
  }

  /// 닉네임이 없으면 uuid 마지막 4글자로 "독자 #XXXX" 생성.
  String get displayName {
    final n = nickname?.trim();
    if (n != null && n.isNotEmpty) return n;
    final tail = id.length >= 4 ? id.substring(id.length - 4).toUpperCase() : id;
    return '독자 #$tail';
  }

  /// 아바타가 없을 때 이니셜용 한 글자 (runes 기준 — surrogate pair 대비).
  String get initialChar {
    final n = nickname?.trim();
    if (n == null || n.isEmpty) return '독';
    return String.fromCharCode(n.runes.first);
  }
}
