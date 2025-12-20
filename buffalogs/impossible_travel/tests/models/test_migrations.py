from django.test import TransactionTestCase
from django_test_migrations.migrator import Migrator


class TestDeviceFingerprintMigration(TransactionTestCase):
    database = "default"

    def setUp(self):
        self.migrator = Migrator(database=self.database)

    def test_migration_0022_logic(self):
        """
        Verify that a desktop user agent results in the correct fingerprint.
        """
        old_state = self.migrator.apply_initial_migration(("impossible_travel", "0021_tasksettings_execution_mode_and_more"))

        User = old_state.apps.get_model("impossible_travel", "User")
        Login = old_state.apps.get_model("impossible_travel", "Login")

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.0.0"
        test_user = User.objects.create(
            username="@drona",
        
        Login.objects.create(user_id=test_user.id, user_agent=ua)

        new_state = self.migrator.apply_tested_migration(("impossible_travel", "0022_remove_tasksettings_unique_task_execution_mode_and_more"))

        LoginNew = new_state.apps.get_model("impossible_travel", "Login")
        record = LoginNew.objects.first()

        self.assertEqual(record.device_fingerprint, "windows-10-desktop-chrome")

    def test_migration_mobile_heuristic(self):
        """
        Verifies that an iPhone User Agent is correctly
        identified as 'mobile' by the migration logic.
        """
        old_state = self.migrator.apply_initial_migration(("impossible_travel", "0021_tasksettings_execution_mode_and_more"))
        User = old_state.apps.get_model("impossible_travel", "User")
        Login = old_state.apps.get_model("impossible_travel", "Login")

        test_user = User.objects.create(username="mobile_user")

        iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
        Login.objects.create(user_id=test_user.id, user_agent=iphone_ua)

        new_state = self.migrator.apply_tested_migration(("impossible_travel", "0022_remove_tasksettings_unique_task_execution_mode_and_more"))

        LoginNew = new_state.apps.get_model("impossible_travel", "Login")
        record = LoginNew.objects.get(user_id=test_user.id)

        self.assertEqual(record.device_fingerprint, "ios-14-mobile-mobilesafari")

    def test_migration_does_not_stop_on_empty_ua(self):
        """
        Verify that one empty User Agent doesn't stop the
        migration for other records.
        """
        old_state = self.migrator.apply_initial_migration(("impossible_travel", "0021_tasksettings_execution_mode_and_more"))
        User = old_state.apps.get_model("impossible_travel", "User")
        Login = old_state.apps.get_model("impossible_travel", "Login")

        user = User.objects.create(username="@drona")

        Login.objects.create(user_id=user.id, user_agent="")

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.0.0"
        Login.objects.create(user_id=user.id, user_agent=ua)

        new_state = self.migrator.apply_tested_migration(("impossible_travel", "0022_remove_tasksettings_unique_task_execution_mode_and_more"))

        LoginNew = new_state.apps.get_model("impossible_travel", "Login")

        second_record = LoginNew.objects.get(user_agent=ua)
        self.assertEqual(second_record.device_fingerprint, "windows-10-desktop-chrome")

    def tearDown(self):
        self.migrator.reset()
