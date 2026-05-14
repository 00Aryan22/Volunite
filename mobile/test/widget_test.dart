import 'package:flutter_test/flutter_test.dart';
import 'package:volunteermap/main.dart';

void main() {
  testWidgets('VolunteerMap splash shows branding', (WidgetTester tester) async {
    await tester.pumpWidget(const VolunteerMapApp());
    expect(find.text('VolunteerMap'), findsOneWidget);
    expect(find.textContaining('Connecting communities'), findsOneWidget);
  });
}
