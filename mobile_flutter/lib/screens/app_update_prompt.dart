import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/app_updates.dart';
import '../core/exchange_theme.dart';
import '../core/exchange_widgets.dart';

class AppUpdateScope extends InheritedNotifier<AppUpdateController> {
  const AppUpdateScope({
    required AppUpdateController controller,
    required super.child,
    super.key,
  }) : super(notifier: controller);
  static AppUpdateController? maybeOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AppUpdateScope>()?.notifier;
}

Future<void> showAppUpdatePrompt(
  BuildContext context,
  AppUpdateController controller,
  AppRelease release, {
  Future<bool> Function(Uri)? openUrl,
}) async {
  if (controller.promptOpen) return;
  controller.promptOpen = true;
  var downloading = false;
  String? error;
  try {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          icon: const Icon(
            Icons.system_update_rounded,
            color: ExchangeColors.teal,
          ),
          title: Text('UniWay ${release.version} 已推出'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '目前版本 ${controller.version}\n新版約 ${(release.bytes / 1000000).toStringAsFixed(1)} MB',
                ),
                const SizedBox(height: 14),
                const Text('點一下下載新版 APK，下載完成後開啟檔案，依 Android 提示安裝更新。'),
                TextButton(
                  onPressed: () async {
                    try {
                      if (!await (openUrl?.call(release.pageUrl) ??
                          launchUrl(
                            release.pageUrl,
                            mode: LaunchMode.externalApplication,
                          ))) {
                        throw StateError('Cannot open browser');
                      }
                    } catch (_) {
                      if (context.mounted) {
                        setState(() => error = '無法開啟版本頁面，請再試一次。');
                      }
                    }
                  },
                  child: const Text('查看更新內容'),
                ),
                if (error != null)
                  Text(
                    error!,
                    style: const TextStyle(color: ExchangeColors.danger),
                  ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: downloading ? null : () => Navigator.pop(context),
              child: const Text('稍後提醒'),
            ),
            FilledButton(
              onPressed: downloading
                  ? null
                  : () async {
                      setState(() {
                        downloading = true;
                        error = null;
                      });
                      try {
                        final opened =
                            await (openUrl?.call(release.downloadUrl) ??
                                launchUrl(
                                  release.downloadUrl,
                                  mode: LaunchMode.externalApplication,
                                ));
                        if (!opened) throw StateError('Cannot open browser');
                        if (context.mounted) Navigator.pop(context);
                      } catch (_) {
                        if (context.mounted) {
                          setState(() {
                            downloading = false;
                            error = '無法開啟下載，請再試一次。';
                          });
                        }
                      }
                    },
              child: Text(downloading ? '開啟下載中…' : '下載更新'),
            ),
          ],
        ),
      ),
    );
    await controller.remindTomorrow(release);
  } finally {
    controller.promptOpen = false;
  }
}

class AppUpdateTile extends StatelessWidget {
  const AppUpdateTile({super.key});
  @override
  Widget build(BuildContext context) {
    final controller = AppUpdateScope.maybeOf(context);
    if (controller == null) return const SizedBox.shrink();
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('App 版本', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 6),
          Text(
            controller.version.isEmpty
                ? '啟動後自動檢查更新'
                : '目前版本 ${controller.version}',
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            icon: const Icon(Icons.system_update_alt_rounded),
            label: Text(controller.checking ? '檢查中…' : '檢查更新'),
            onPressed: controller.checking
                ? null
                : () async {
                    final release = await controller.check(manual: true);
                    if (!context.mounted) return;
                    if (release != null) {
                      await showAppUpdatePrompt(context, controller, release);
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(controller.error ?? '目前已是最新版本。'),
                        ),
                      );
                    }
                  },
          ),
        ],
      ),
    );
  }
}
