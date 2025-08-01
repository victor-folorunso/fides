import 'package:flutter/material.dart';

class AirdropPage extends StatelessWidget {
  const AirdropPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        ElevatedButton(onPressed: () {
          print("claim button clicked");
        }, child: Text("claim FIDES"))
      ],
    );
  }
}