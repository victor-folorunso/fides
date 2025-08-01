import 'package:flutter/material.dart';
import 'package:my_app/airdrop_page.dart';
import 'package:my_app/swap_page.dart';
import 'package:my_app/vault_page.dart';

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  int pageIndex = 0;
  var appBarTitle = "airdrop";

  final pages = [
    Center(child: AirdropPage()),
    Center(child: VaultPage()),
    Center(child: SwapPage()),
  ];

  final page_name = [
    "airdrop",
    "vault",
    "swap",
  ];

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        appBar: AppBar(
          leading: Icon(Icons.verified_user),
          title: Text(appBarTitle),
          backgroundColor: Color(0xFF00FF15),
          titleTextStyle: TextStyle(fontWeight: FontWeight.bold, fontSize: 25),
          centerTitle: true,
          actions: [
            IconButton(
              onPressed: () {
                print("logout clicked");
              },
              icon: Icon(Icons.logout),
            ),
          ],
        ),
        body: pages[pageIndex],
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: pageIndex,
          backgroundColor: Color(0xFF00FF15),
          onTap: (index) {
            setState(() {
              pageIndex = index;
              appBarTitle = page_name[index];
            });
          },
          items: [
            BottomNavigationBarItem(
              icon: Icon(Icons.card_giftcard),
              label: "airdrop",
            ),
            BottomNavigationBarItem(icon: Icon(Icons.lock), label: "vault"),
            BottomNavigationBarItem(
              icon: Icon(Icons.currency_exchange),
              label: "swap",
            ),
          ],
          selectedFontSize: 20,
          unselectedFontSize: 15,
        ),
      ),
    );
  }
}
