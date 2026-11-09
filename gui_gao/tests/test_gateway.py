import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from gui_gao.gateway import Gateway, UserError, unwrap
from gui_gao.validation import item_errors, password_error, registration_errors


def fields(**changes):
    return dict(name="Python textbook", category="Books", price="35.00",
                description="Good condition, with a few notes.", image_path="", **changes)


class RealBackendIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="group9-ui-test-")
        self.addCleanup(self.temp.cleanup)
        self.gateway = Gateway.isolated(self.temp.name)
        self.gateway.register("student_a", "Campus123", "Gao")
        self.gateway.register("student_b", "Campus456", "Lin")
        self.gateway.login("student_a", "Campus123")

    def test_login_and_session_exclude_secrets(self):
        user = self.gateway.user
        self.assertEqual(user["nickname"], "Gao")
        self.assertFalse(any("password" in key for key in user))

    def test_failed_login_clears_previous_session(self):
        with self.assertRaises(UserError):
            self.gateway.login("student_a", "Wrong123")
        self.assertIsNone(self.gateway.user)
        with self.assertRaises(UserError):
            self.gateway.mine()

    def test_duplicate_registration(self):
        with self.assertRaises(UserError):
            self.gateway.register("STUDENT_A", "Campus123", "DuplicateUser")

    def test_create_persist_reload_edit(self):
        item = self.gateway.save_item(fields())
        replacement = Gateway.isolated(self.temp.name)
        replacement.login("student_a", "Campus123")
        self.assertEqual(replacement.detail(item["id"])["name"], "Python textbook")
        changed = fields()
        changed.update(name="Updated textbook", price="42.50")
        replacement.save_item(changed, item["id"])
        self.assertEqual(self.gateway.detail(item["id"])["price"], 42.5)

    def test_all_owner_mutations_are_rejected_for_other_user(self):
        item = self.gateway.save_item(fields())
        self.gateway.login("student_b", "Campus456")
        for action in ["remove", "restore", "delete"]:
            with self.subTest(action=action), self.assertRaises(UserError):
                self.gateway.change_item(action, item["id"])
        with self.assertRaises(UserError):
            self.gateway.save_item(fields(), item["id"])
        self.assertEqual(self.gateway.mine(), [])

    def test_remove_restore_delete_and_stale_detail(self):
        item = self.gateway.save_item(fields())
        self.gateway.change_item("remove", item["id"])
        self.assertEqual(self.gateway.browse(), [])
        self.assertEqual(self.gateway.mine()[0]["status"], "Off sale")
        self.gateway.change_item("restore", item["id"])
        self.assertEqual(len(self.gateway.browse()), 1)
        self.gateway.change_item("delete", item["id"])
        self.assertEqual(self.gateway.mine(), [])
        with self.assertRaises(UserError):
            self.gateway.detail(item["id"])
        with self.assertRaises(UserError):
            self.gateway.save_item(fields(), item["id"])

    def test_removed_item_is_visible_only_to_owner_in_ui(self):
        item = self.gateway.save_item(fields())
        self.gateway.change_item("remove", item["id"])
        self.assertEqual(self.gateway.detail(item["id"])["status"], "Off sale")
        self.gateway.login("student_b", "Campus456")
        with self.assertRaises(UserError):
            self.gateway.detail(item["id"])

    def test_search_category_and_price_order(self):
        self.gateway.save_item(fields())
        second = fields()
        second.update(name="Keyboard", category="Electronics", price="88", description="Bluetooth keyboard for Python users")
        self.gateway.save_item(second)
        self.assertEqual(len(self.gateway.browse("pYtHoN")), 2)
        self.assertEqual(len(self.gateway.browse("python", "Electronics")), 1)
        self.assertEqual([i["price"] for i in self.gateway.browse(sort="Price: high to low")], [88, 35])
        self.assertEqual([i["price"] for i in self.gateway.browse(sort="Price: low to high")], [35, 88])
        self.assertEqual(self.gateway.browse("does-not-exist"), [])

    def test_session_identity_overrides_injected_fields(self):
        value = fields()
        value.update(seller_id=2, id=999, status="Off sale")
        item = self.gateway.save_item(value)
        self.assertEqual(item["seller_id"], self.gateway.user_id())
        self.assertNotEqual(item["id"], 999)
        self.assertEqual(item["status"], "Available")

    def test_nickname_updates_public_seller_label(self):
        item = self.gateway.save_item(fields())
        self.gateway.nickname("GaoStudent")
        self.assertEqual(self.gateway.user["nickname"], "GaoStudent")
        self.assertEqual(self.gateway.seller_names([item])[item["seller_id"]], "GaoStudent")

    def test_password_change_requires_current_password(self):
        with self.assertRaises(UserError):
            self.gateway.password("Wrong123", "Newpass123")
        self.gateway.password("Campus123", "Newpass123")
        with self.assertRaises(UserError):
            self.gateway.login("student_a", "Campus123")
        self.gateway.login("student_a", "Newpass123")

    def test_invalid_backend_input_preserves_existing_item(self):
        item = self.gateway.save_item(fields())
        value = fields()
        value["price"] = "-2"
        with self.assertRaises(UserError):
            self.gateway.save_item(value, item["id"])
        self.assertEqual(self.gateway.detail(item["id"])["price"], 35)

    def test_corrupt_data_reports_failure_without_overwriting(self):
        self.gateway.save_item(fields())
        path = Path(self.temp.name) / "items.json"
        bad = "{not valid json"
        path.write_text(bad, encoding="utf-8")
        with self.assertRaises(UserError):
            self.gateway.browse()
        with self.assertRaises(UserError):
            self.gateway.save_item(fields())
        self.assertEqual(path.read_text(encoding="utf-8"), bad)

    def test_logged_out_actions_are_blocked(self):
        self.gateway.logout()
        for operation in [self.gateway.browse, self.gateway.mine,
                          lambda: self.gateway.save_item(fields()),
                          lambda: self.gateway.change_item("delete", 1)]:
            with self.subTest(operation=operation), self.assertRaises(UserError):
                operation()


class ValidationTests(unittest.TestCase):
    def test_field_limits_and_price_edge_cases(self):
        self.assertEqual(item_errors(fields()), {})
        for value in ["", "0", "-1", "NaN", "Infinity", "100000001", "0.001", "abc", "1e999999"]:
            record = fields()
            record["price"] = value
            with self.subTest(value=value):
                self.assertIn("price", item_errors(record))
        record = fields()
        record.update(name="x"*21, description="x"*201, category="Other")
        self.assertEqual(set(item_errors(record)), {"name", "description", "category"})

    def test_registration_and_password_feedback(self):
        value = dict(username="student_1", nickname="GaoStudent", password="Campus123", confirm="Campus123")
        self.assertEqual(registration_errors(value), {})
        self.assertTrue(password_error("Campus 123"))
        self.assertTrue(password_error("Campus\t123"))
        value.update(username="1bad", confirm="different")
        self.assertEqual(set(registration_errors(value)), {"username", "confirm"})

    def test_contract_invalid_and_failed_responses(self):
        for result in [None, {}, {"success": "true"}, {"success": False, "message": "Error"}]:
            with self.subTest(result=result), self.assertRaises(UserError):
                unwrap(result)

    def test_default_module_adapter_uses_team_function_names(self):
        users, items = Mock(), Mock()
        users.login_user.return_value = {"success": True, "data": {"id": 7, "nickname": "Student"}}
        temp = tempfile.TemporaryDirectory(prefix="group9-mock-")
        self.addCleanup(temp.cleanup)
        gateway = Gateway(users, items, feature_directory=temp.name)
        gateway.login("name", "value")
        users.login_user.assert_called_once_with("name", "value")
        self.assertEqual(gateway.user_id(), 7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
