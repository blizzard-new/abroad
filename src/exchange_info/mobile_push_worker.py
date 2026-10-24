"""Host scheduler entrypoint: processes published rules, never crawls sources."""
import json
import os

from .api import app
from .mobile_push import FcmSender, MobilePushService, SupabasePushStore


def main():
    project = os.environ.get('EXCHANGE_FIREBASE_PROJECT_ID')
    if not project:
        raise SystemExit('EXCHANGE_FIREBASE_PROJECT_ID is not configured.')
    if app.state.account_repository.backend_name != 'supabase':
        raise SystemExit('Scheduled dispatch requires the production Supabase repository.')
    service = MobilePushService(app.state.account_repository, app.state.notification_service,
                               SupabasePushStore(), FcmSender(project))
    print(json.dumps(service.dispatch()))


if __name__ == '__main__':
    main()
