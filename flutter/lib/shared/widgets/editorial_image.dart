import 'package:flutter/material.dart';

import '../../core/constants/categories.dart';
import 'editorial_placeholder.dart';

/// URL 이 있으면 네트워크 이미지, 없거나 실패하면 EditorialPlaceholder.
class EditorialImage extends StatelessWidget {
  final String? url;
  final double width;
  final double height;
  final Category cat;
  final String? label;
  final double radius;

  const EditorialImage({
    super.key,
    required this.url,
    this.width = double.infinity,
    this.height = 160,
    required this.cat,
    this.label,
    this.radius = 0,
  });

  @override
  Widget build(BuildContext context) {
    final u = url;
    if (u == null || u.isEmpty) {
      return EditorialPlaceholder(
        width: width, height: height, cat: cat, label: label, radius: radius,
      );
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: Image.network(
        u,
        width: width,
        height: height,
        fit: BoxFit.cover,
        errorBuilder: (_, _, _) => EditorialPlaceholder(
          width: width, height: height, cat: cat, label: label, radius: radius,
        ),
        loadingBuilder: (ctx, child, progress) {
          if (progress == null) return child;
          return EditorialPlaceholder(
            width: width, height: height, cat: cat, label: label, radius: radius,
          );
        },
      ),
    );
  }
}
