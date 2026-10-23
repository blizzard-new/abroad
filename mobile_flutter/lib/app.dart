import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';

import 'core/exchange_theme.dart';
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
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _links?.cancel();
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
    }
  }

  @override
  Widget build(BuildContext context) {
    return ExchangeStoreScope(
      store: store,
      child: MaterialApp(
        navigatorKey: navigatorKey,
        title: 'UniWay',
        debugShowCheckedModeBanner: false,
        theme: buildExchangeTheme(),
        home: const RootShell(),
      ),
    );
  }
}
