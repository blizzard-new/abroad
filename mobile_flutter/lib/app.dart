import 'package:flutter/material.dart';

import 'core/exchange_theme.dart';
import 'screens/root_shell.dart';
import 'state/exchange_store.dart';

class ExchangeGuideApp extends StatefulWidget {
  const ExchangeGuideApp({super.key});

  @override
  State<ExchangeGuideApp> createState() => _ExchangeGuideAppState();
}

class _ExchangeGuideAppState extends State<ExchangeGuideApp> {
  late final ExchangeStore store;

  @override
  void initState() {
    super.initState();
    store = ExchangeStore()..initialize();
  }

  @override
  void dispose() {
    store.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ExchangeStoreScope(
      store: store,
      child: MaterialApp(
        title: '交換指南',
        debugShowCheckedModeBanner: false,
        theme: buildExchangeTheme(),
        home: const RootShell(),
      ),
    );
  }
}
