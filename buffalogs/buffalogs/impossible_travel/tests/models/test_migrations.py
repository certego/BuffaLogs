from django.test import TransactionTestCase
from django_test_migrations.migrator import Migrator


class BaseMigrationTestCase(TransactionTestCase):
    """
    Resusable base class for migration tests.
    """

    database = "default"
    app_name = "impossible_travel"
    migrate_from = None
    migrate_to = None

    def setUp(self):
        super().setUp()
        self.migrator = Migrator(database=self.database)
        self.old_state = self.migrator.apply_initial_migration((self.app_name, self.migrate_from))

    def apply_tested_migration(self):
        # Applies the migration being tested
        return self.migrator.apply_tested_migration((self.app_name, self.migrate_to))

    def tearDown(self):
        self.migrator.reset()
        super().tearDown()


class TestDeviceFingerprintMigration0022(BaseMigrationTestCase):
    migrate_from = "0021_tasksettings_execution_mode_and_more"
    migrate_to = "0022_remove_tasksettings_unique_task_execution_mode_and_more"

    def test_migration_desktop_logic(self):
        User = self.old_state.apps.get_model(self.app_name, "User")
        Login = self.old_state.apps.get_model(self.app_name, "Login")

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.0.0"
        test_user = User.objects.create(username="drona_1")
        Login.objects.create(user_id=test_user.id, user_agent=ua)

        new_state = self.apply_tested_migration()
        LoginNew = new_state.apps.get_model(self.app_name, "Login")
        record = LoginNew.objects.first()
        self.assertEqual(record.device_fingerprint, "windows-10-desktop-chrome")

    def test_migration_mobile_heuristic(self):
        User = self.old_state.apps.get_model(self.app_name, "User")
        Login = self.old_state.apps.get_model(self.app_name, "Login")

        test_user = User.objects.create(username="mobile_user")
        iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
        Login.objects.create(user_id=test_user.id, user_agent=iphone_ua)

        new_state = self.apply_tested_migration()
        LoginNew = new_state.apps.get_model(self.app_name, "Login")
        record = LoginNew.objects.get(user_id=test_user.id)

        self.assertEqual(record.device_fingerprint, "ios-14-mobile-mobilesafari")

    def test_migration_does_not_stop_on_empty_ua(self):
        User = self.old_state.apps.get_model(self.app_name, "User")
        Login = self.old_state.apps.get_model(self.app_name, "Login")

        user = User.objects.create(username="drona_2")
        Login.objects.create(user_id=user.id, user_agent="")

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.0.0"
        Login.objects.create(user_id=user.id, user_agent=ua)

        new_state = self.apply_tested_migration()
        LoginNew = new_state.apps.get_model(self.app_name, "Login")

        second_record = LoginNew.objects.get(user_agent=ua)
        self.assertEqual(second_record.device_fingerprint, "windows-10-desktop-chrome")
