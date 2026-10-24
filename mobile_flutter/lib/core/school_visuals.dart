import 'package:flutter/material.dart';

import '../data/models.dart';
import 'exchange_theme.dart';

class SchoolPhoto extends StatelessWidget {
  const SchoolPhoto({required this.school, super.key, this.fit = BoxFit.cover});

  final PartnerUniversity school;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    if (school.imageStatus == 'verified' && school.imageUrl.isNotEmpty) {
      return Image.network(
        school.imageUrl,
        fit: fit,
        alignment: schoolPhotoAlignment(school),
        filterQuality: FilterQuality.medium,
        gaplessPlayback: true,
        semanticLabel: '${school.schoolName}官方校園圖片',
        loadingBuilder: (context, child, progress) => progress == null
            ? child
            : const _NeutralSchoolPlaceholder(showProgress: true),
        errorBuilder: (_, _, _) =>
            _BundledSchoolPhoto(school: school, fit: fit),
      );
    }
    return const _NeutralSchoolPlaceholder();
  }
}

class _BundledSchoolPhoto extends StatelessWidget {
  const _BundledSchoolPhoto({required this.school, required this.fit});

  final PartnerUniversity school;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    final uri = Uri.tryParse(school.imageUrl);
    final filename = uri == null || uri.pathSegments.isEmpty
        ? ''
        : uri.pathSegments.last;
    if (filename.isEmpty) return const _NeutralSchoolPlaceholder();
    return Image.asset(
      'assets/schools/$filename',
      fit: fit,
      alignment: schoolPhotoAlignment(school),
      filterQuality: FilterQuality.medium,
      semanticLabel: '${school.schoolName}官方校園圖片',
      errorBuilder: (_, _, _) => const _NeutralSchoolPlaceholder(),
    );
  }
}

class _NeutralSchoolPlaceholder extends StatelessWidget {
  const _NeutralSchoolPlaceholder({this.showProgress = false});

  final bool showProgress;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      image: true,
      label: showProgress ? '正在載入學校圖片' : '學校圖片暫時無法顯示',
      child: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF24324D), Color(0xFF161F38)],
          ),
        ),
        child: Center(
          child: showProgress
              ? const SizedBox.square(
                  dimension: 28,
                  child: CircularProgressIndicator(strokeWidth: 2.4),
                )
              : const Icon(
                  Icons.account_balance_outlined,
                  size: 54,
                  color: ExchangeColors.secondaryInk,
                ),
        ),
      ),
    );
  }
}

Alignment schoolPhotoAlignment(PartnerUniversity school) {
  final bucket =
      school.schoolName.codeUnits.fold<int>(
        0,
        (value, codeUnit) => value + codeUnit,
      ) %
      3;
  return switch (bucket) {
    0 => const Alignment(-.28, 0),
    1 => Alignment.center,
    _ => const Alignment(.28, 0),
  };
}
