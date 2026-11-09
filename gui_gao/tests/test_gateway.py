import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from gui_gao.gateway import Gateway, UserError, unwrap
from gui_gao.validation import item_errors, password_error, registration_errors


def fields(**changes):
    return dict(name="Python教材", category="书籍", price="35.00",
                description="九成新，少量笔记。", image_path="", **changes)


class RealBackendIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="group9-ui-test-")
        self.addCleanup(self.temp.cleanup)
        self.gateway = Gateway.isolated(self.temp.name)
        self.gateway.register("student_a", "Campus123", "小高")
        self.gateway.register("student_b", "Campus456", "小林")
        self.gateway.login("student_a", "Campus123")

    def test_login_and_session_exclude_secrets(self):
        user = self.gateway.user
        self.assertEqual(user["nickname"], "小高")
        self.assertFalse(any("password" in key for key in user))

    def test_failed_login_clears_previous_session(self):
        with self.assertRaises(UserError):
            self.gateway.login("student_a", "Wrong123")
        self.assertIsNone(self.gateway.user)
        with self.assertRaises(UserError):
            self.gateway.mine()

    def test_duplicate_registration(self):
        with self.assertRaises(UserError):
            self.gateway.register("STUDENT_A", "Campus123", "重复用户")

    def test_create_persist_reload_edit(self):
        item = self.gateway.save_item(fields())
        replacement = Gateway.isolated(self.temp.name)
        replacement.login("student_a", "Campus123")
        self.assertEqual(replacement.detail(item["id"])["name"], "Python教材")
        changed = fields()
        changed.update(name="更新后的教材", price="42.50")
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
        self.assertEqual(self.gateway.mine()[0]["status"], "已下架")
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
        self.assertEqual(self.gateway.detail(item["id"])["status"], "已下架")
        self.gateway.login("student_b", "Campus456")
        with self.assertRaises(UserError):
            self.gateway.detail(item["id"])

    def test_search_category_and_price_order(self):
        self.gateway.save_item(fields())
        second = fields()
        second.update(name="键盘", category="电子产品", price="88", description="Python 程序员的蓝牙键盘")
        self.gateway.save_item(second)
        self.assertEqual(len(self.gateway.browse("pYtHoN")), 2)
        self.assertEqual(len(self.gateway.browse("python", "电子产品")), 1)
        self.assertEqual([i["price"] for i in self.gateway.browse(sort="价格从高到低")], [88, 35])
        self.assertEqual([i["price"] for i in self.gateway.browse(sort="价格从低到高")], [35, 88])
        self.assertEqual(self.gateway.browse("does-not-exist"), [])

    def test_session_identity_overrides_injected_fields(self):
        value = fields()
        value.update(seller_id=2, id=999, status="已下架")
        item = self.gateway.save_item(value)
        self.assertEqual(item["seller_id"], self.gateway.user_id())
        self.assertNotEqual(item["id"], 999)
        self.assertEqual(item["status"], "在售")

    def test_nickname_updates_public_seller_label(self):
        item = self.gateway.save_item(fields())
        self.gateway.nickname("高同学")
        self.assertEqual(self.gateway.user["nickname"], "高同学")
        self.assertEqual(self.gateway.seller_names([item])[item["seller_id"]], "高同学")

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
        record.update(name="书"*21, description="字"*201, category="其他")
        self.assertEqual(set(item_errors(record)), {"name", "description", "category"})

    def test_registration_and_password_feedback(self):
        value = dict(username="student_1", nickname="高同学", password="Campus123", confirm="Campus123")
        self.assertEqual(registration_errors(value), {})
        self.assertTrue(password_error("Campus 123"))
        self.assertTrue(password_error("Campus\t123"))
        value.update(username="1bad", confirm="different")
        self.assertEqual(set(registration_errors(value)), {"username", "confirm"})

    def test_contract_invalid_and_failed_responses(self):
        for result in [None, {}, {"success": "true"}, {"success": False, "message": "错误"}]:
            with self.subTest(result=result), self.assertRaises(UserError):
                unwrap(result)

    def test_default_module_adapter_uses_team_function_names(self):
        users, items = Mock(), Mock()
        users.login_user.return_value = {"success": True, "data": {"id": 7, "nickname": "同学"}}
        temp = tempfile.TemporaryDirectory(prefix="group9-mock-")
        self.addCleanup(temp.cleanup)
        gateway = Gateway(users, items, feature_directory=temp.name)
        gateway.login("name", "value")
        users.login_user.assert_called_once_with("name", "value")
        self.assertEqual(gateway.user_id(), 7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
