/// Backend base URL.
///
/// Local: default `http://127.0.0.1:8000`
/// Production / device to Cloud Run or Vercel:
///   `flutter run --dart-define=API_BASE_URL=https://your-api.example.com`
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  static const String surveysAll = '/surveys/all';
  static const String submitSurvey = '/surveys/submit';
  static const String clusters = '/surveys/clusters';
  static const String urgentNeeds = '/surveys/urgent';
  static const String ocrUpload = '/surveys/ocr';
  static const String volunteers = '/volunteers/available';
  static const String registerVolunteer = '/volunteers/register';
  static const String matchVolunteers = '/volunteers/match';
  static const String stats = '/dashboard/stats';
  static const String health = '/health';
}
