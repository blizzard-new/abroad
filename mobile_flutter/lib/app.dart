import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

import 'core/app_updates.dart';
import 'core/exchange_theme.dart';
import 'screens/app_update_prompt.dart';
import 'screens/root_shell.dart';
import 'screens/deadlines_screen.dart';
import 'screens/notification_screen.dart';
import 'state/exchange_store.dart';

class ExchangeGuideApp extends StatefulWidget {
  const ExchangeGuideApp({super.key});

  @override
  State<ExchangeGuideApp> createState() => _ExchangeGuideAppState();
}

class _ExchangeGuideAppState extends State<ExchangeGuideApp>
    with WidgetsBindingObserver {
  late final ExchangeStore store;
  StreamSubscription<Uri>? _links;
  final navigatorKey = GlobalKey<NavigatorState>();
  late Future<void> _initialized;
  final updates = AppUpdateController();
  Timer? _updateTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    store = ExchangeStore();
    final initialized = _initialized = store.initialize();
    store.mobileNotifications.target.addListener(_openNotification);
    final appLinks = AppLinks();
    _links = appLinks.uriLinkStream.listen((uri) async {
      await initialized;
      if (uri.scheme == 'tw.uniway.app' && uri.host == 'journey') {
        store.selectMainTab(0);
        navigatorKey.currentState?.popUntil((route) => route.isFirst);
        return;
      }
      await store.completeMobileLogin(uri);
    });
    _updateTimer = Timer(const Duration(seconds: 3), _checkUpdate);
  }

  Future<void> _checkUpdate() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) return;
    final release = await updates.check();
    if (!mounted || release == null || !await updates.shouldPrompt(release)) {
      return;
    }
    if (!mounted ||
        WidgetsBinding.instance.lifecycleState != AppLifecycleState.resumed) {
      return;
    }
    final context = navigatorKey.currentState?.overlay?.context;
    if (context != null && context.mounted) {
      await showAppUpdatePrompt(context, updates, release);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _links?.cancel();
    _updateTimer?.cancel();
    updates.dispose();
    store.mobileNotifications.target.removeListener(_openNotification);
    store.dispose();
    super.dispose();
  }

  Future<void> _openNotification() async {
    final target = store.mobileNotifications.target.value;
    if (target == null) return;
    await _initialized;
    if (!mounted || store.account?.id != target.accountId) return;
    await store.selectUniversity(target.homeSchool);
    if (!mounted || store.account?.id != target.accountId) return;
    final event = store.personalCalendarEvents
        .where((event) => event.id == target.eventId)
        .firstOrNull;
    store.mobileNotifications.target.value = null;
    navigatorKey.currentState?.push(
      MaterialPageRoute(
        builder: (_) => target.notificationId.isNotEmpty
            ? NotificationScreen(initialNotificationId: target.notificationId)
            : DeadlinesScreen(initialDate: event?.date),
      ),
    );
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(store.synchronizeWorkspace());
      unawaited(_checkUpdate());
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppUpdateScope(
      controller: updates,
      child: ExchangeStoreScope(
        store: store,
        child: MaterialApp(
          navigatorKey: navigatorKey,
          title: 'UniWay',
          debugShowCheckedModeBanner: false,
          theme: buildExchangeTheme(),
          home: const RootShell(),
        ),
      ),
    );
  }
}
