"""Real Tk widget/async tests. Requires a graphical desktop with Tkinter.

These are supplementary frontend tests, not a replacement for tests_zhao.
Windows stay withdrawn; all backend state is in TemporaryDirectory.
"""
import gc
import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from gui_gao.app import CampusApp
from gui_gao.gateway import Gateway
from gui_gao.widgets import ItemImage, image_path


class TkFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="group9-ui-widgets-")
        self.gateway = Gateway.isolated(self.temp.name)
        self.gateway.register("student_a", "Campus123", "小高")
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.temp.cleanup()
            self.skipTest(f"A Tk desktop is required: {exc}")
        self.root.withdraw()
        self.app = CampusApp(self.root, self.gateway)
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.wait()

    def tearDown(self):
        self.wait()
        self.app.page = None
        self.app.close()
        # Each test owns a Tcl interpreter. Collect its Python reference cycles
        # here on the main thread before another test starts a service worker.
        del self.app, self.root
        gc.collect()
        self.temp.cleanup()
        self.assertEqual(self.errors, [], f"Tk callback failures: {self.errors}")

    def wait(self):
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            self.root.update()
            if not self.app.busy:
                self.root.update()
                if not self.app.busy:
                    return
            time.sleep(.01)
        self.fail("UI operation did not complete in five seconds")

    def login(self):
        self.app.page.fields["username"].set("student_a")
        self.app.page.fields["password"].set("Campus123")
        self.app.page.submit()
        self.wait()
        self.assertEqual(self.app.route, "home")

    def test_login_error_then_success(self):
        page = self.app.page
        page.fields["username"].set("student_a")
        page.fields["password"].set("Wrong123")
        page.submit()
        self.wait()
        self.assertTrue(page.error.cget("text"))
        self.assertEqual(page.fields["password"].get(), "")
        self.assertIsNone(self.gateway.user)
        self.login()

    def test_registration_page_and_success(self):
        self.app.show("register")
        self.wait()
        page = self.app.page
        for key, value in dict(username="new_user", nickname="新同学", password="Campus456", confirm="Campus456").items():
            page.fields[key].set(value)
        page.submit()
        self.wait()
        self.assertEqual(self.app.route, "login")
        self.assertEqual(self.app.page.fields["username"].get(), "new_user")
        self.assertIsNone(self.gateway.user)

    def test_publish_validation_then_save_and_edit(self):
        self.login()
        self.app.show("publish")
        self.wait()
        page = self.app.page
        page.submit()
        self.assertTrue(page.fields["name"].error.cget("text"))
        for key,value in dict(name="测试教材", price="35", description="九成新，少量笔记。", category="书籍").items():
            page.fields[key].set(value)
        page.submit()
        # Duplicate click is ignored while in flight.
        page.submit()
        self.wait()
        self.assertEqual(self.app.route, "detail")
        self.assertEqual(len(self.gateway.mine()), 1)
        item_id = self.gateway.mine()[0]["id"]
        self.app.show("publish", item_id=item_id)
        self.wait()
        self.app.page.fields["price"].set("40")
        self.app.page.submit()
        self.wait()
        self.assertEqual(self.gateway.detail(item_id)["price"], 40)

    def test_unsaved_form_cancel_preserves_input(self):
        self.login()
        self.app.show("publish")
        self.wait()
        self.app.page.fields["name"].set("未完成的商品")
        with patch("gui_gao.app.messagebox.askyesno", return_value=False):
            self.app.show("home")
        self.assertEqual(self.app.route, "publish")
        self.assertEqual(self.app.page.fields["name"].get(), "未完成的商品")
        with patch("gui_gao.app.messagebox.askyesno", return_value=True):
            self.app.show("home")
        self.wait()
        self.assertEqual(self.app.route, "home")

    def test_all_authenticated_routes_and_logout(self):
        self.login()
        for route in ["mine", "account", "publish", "home"]:
            self.app.show(route)
            self.wait()
            self.assertEqual(self.app.route, route)
        self.app.logout()
        self.wait()
        self.assertEqual(self.app.route, "login")
        self.assertIsNone(self.gateway.user)

    def test_account_nickname_and_password(self):
        self.login()
        self.app.show("account")
        self.wait()
        self.app.page.nickname.set("高同学")
        self.app.page.save_nickname()
        self.wait()
        self.assertEqual(self.gateway.user["nickname"], "高同学")
        for key,value in dict(old="Campus123", new="Nextpass123", confirm="Nextpass123").items():
            self.app.page.fields[key].set(value)
        self.app.page.save_password()
        self.wait()
        self.assertFalse(self.app.page.is_dirty())
        self.gateway.login("student_a", "Nextpass123")

    def test_worker_exception_unfreezes_form_and_hides_sensitive_error(self):
        def bad():
            raise OSError("sensitive-token-do-not-show")
        self.app.run_task(bad, lambda _: None)
        self.wait()
        self.assertFalse(self.app.busy)
        self.assertNotIn("sensitive-token", self.app.status.get())
        self.assertFalse(self.app.page.fields["username"].input.instate(["disabled"]))

    def test_page_variables_are_released_before_worker_collection(self):
        finalized_on = []
        original = tk.Variable.__del__

        def tracked(variable):
            finalized_on.append(threading.get_ident())
            original(variable)

        with patch.object(tk.Variable, "__del__", tracked):
            for _ in range(3):
                self.app.show("register")
                self.wait()
                self.app.show("login")
                self.wait()
                self.app.run_task(gc.collect, lambda _: None)
                self.wait()
        self.assertTrue(finalized_on)
        self.assertEqual(set(finalized_on), {threading.get_ident()})

    def test_missing_and_corrupt_image_fallback(self):
        for value in ["", str(Path(self.temp.name)/"missing.png")]:
            image = ItemImage(self.root, value)
            self.assertIsNone(image.photo)
            self.assertTrue(image.reason)
            image.destroy()
        file = Path(self.temp.name)/"corrupt.png"
        file.write_text("invalid image")
        image = ItemImage(self.root, str(file))
        self.assertIsNone(image.photo)
        image.destroy()

    def test_native_png_demo_asset_preview(self):
        asset = Path(__file__).resolve().parents[1]/"assets"/"book.png"
        image = ItemImage(self.root, str(asset))
        self.assertIsNotNone(image.photo)
        self.assertEqual(image.reason, "")
        image.destroy()
        self.assertEqual(image_path("gui_gao/assets/book.png"), asset)

    def test_minimum_window_layout(self):
        self.login()
        item = self.gateway.save_item(dict(name="测试教材", category="书籍", price="35",
                                           description="商品描述", image_path=""))
        self.root.geometry("1000x700")
        self.root.deiconify()
        for route in ["home", "mine", "account", "publish", "detail"]:
            kwargs = {"item_id": item["id"]} if route == "detail" else {}
            self.app.show(route, **kwargs)
            self.wait()
            self.root.update_idletasks()
            with self.subTest(route=route):
                self.assertLessEqual(self.app.page.body.winfo_reqwidth(),
                                     self.app.page.canvas.winfo_width()+2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
