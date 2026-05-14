# VolunteerMap — Flutter mobile app

Field companion for surveys, maps, OCR upload, and volunteer matching. It talks to the same FastAPI backend as the Streamlit dashboard.

## API base URL

By default the app points at `http://127.0.0.1:8000` (see `lib/config/api_config.dart`). For a deployed backend or a physical device, pass your Cloud Run / Vercel URL at build time:

```bash
flutter run --dart-define=API_BASE_URL=https://your-api.example.com
flutter build apk --dart-define=API_BASE_URL=https://your-api.example.com
```

## Commands

```bash
flutter pub get
flutter analyze
flutter test
```

See the repository root [README.md](../README.md) for full stack setup.
