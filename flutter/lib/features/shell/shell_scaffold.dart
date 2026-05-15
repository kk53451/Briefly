import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../shared/widgets/shell_tab_bar.dart';

/// 4탭 하단 내비 shell — go_router StatefulShellRoute 와 연결.
class ShellScaffold extends StatelessWidget {
  final Widget child;
  final int currentIndex;
  final ValueChanged<int> onTab;

  const ShellScaffold({
    super.key,
    required this.child,
    required this.currentIndex,
    required this.onTab,
  });

  @override
  Widget build(BuildContext context) {
    final active = ShellTab.values[currentIndex];
    return Scaffold(
      body: child,
      bottomNavigationBar: SafeArea(
        top: false,
        child: ShellTabBar(
          active: active,
          onChanged: (t) {
            final idx = ShellTab.values.indexOf(t);
            onTab(idx);
            context.go(t.route);
          },
        ),
      ),
    );
  }
}
