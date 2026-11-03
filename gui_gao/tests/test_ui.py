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
from gui_gao.widgets import ItemImage, MarketHero, image_path


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

    def test_login_reveal_cleanup_and_minimum_layout(self):
        self.root.geometry('1000x700')
        self.root.deiconify()
        self.root.update_idletasks()
        page = self.app.page
        self.assertLessEqual(page.body.winfo_reqwidth(), page.canvas.winfo_width()+2)
        page.fields['username'].set('student_a')
        page.fields['password'].set('Wrong123')
        page.toggle_password()
        self.assertEqual(page.fields['password'].input.cget('show'), '')
        page.submit()
        self.wait()
        self.assertEqual(page.fields['password'].get(), '')
        self.assertFalse(page.password_visible)
        self.assertTrue(page.fields['password'].input.cget('show'))
        page.artwork.animate(-5)
        self.app.show('register')
        self.wait()
        page = self.app.page
        page.toggle_password()
        self.assertEqual(page.fields['confirm'].input.cget('show'), '')
        self.root.update_idletasks()
        self.assertLessEqual(page.body.winfo_reqwidth(), page.canvas.winfo_width()+2)

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

    def test_interactions_submit_and_navigation(self):
        self.login()
        self.gateway.register("other_user", "Campus123", "其他同学")
        self.gateway.login("other_user", "Campus123")
        item = self.gateway.save_item(dict(name="键盘", category="电子产品", price="88", description="蓝牙正常", image_path=""))
        self.gateway.login("student_a", "Campus123")
        self.app.show("detail", item_id=item['id'])
        self.wait()
        page = self.app.page
        page.favorite()
        self.wait()
        self.assertTrue(page.favorited)
        page.messages_panel.composer.set("请问还在吗？")
        with patch("gui_gao.app.messagebox.askyesno", return_value=False):
            self.app.show("home")
        self.assertEqual(self.app.route, "detail")
        page.messages_panel.send()
        self.wait()
        self.assertFalse(page.is_dirty())
        with patch("gui_gao.item_page.messagebox.askyesno", return_value=True):
            page.intention()
        self.wait()
        self.assertTrue(page.intended)
        self.root.geometry("1000x700")
        self.root.deiconify()
        for kind in ["favorites", "messages", "intentions", "logs"]:
            self.app.show("interactions", kind=kind)
            self.wait()
            self.assertTrue(self.app.page.records, kind)
            self.assertLessEqual(self.app.page.body.winfo_reqwidth(), self.app.page.canvas.winfo_width()+2, kind)
        self.app.show("interactions", kind="messages", item_id=item['id'])
        self.wait()
        self.assertIsNotNone(self.app.page.panel)

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

    def test_live_preview_and_prompts_preserve_existing_text(self):
        self.login()
        self.app.show('publish')
        self.wait()
        page = self.app.page
        page.fields['name'].set('台灯')
        page.fields['price'].set('25')
        page.fields['description'].set('原有内容')
        page.add_prompt('附带配件：')
        self.root.update()
        self.assertEqual(page.fields['description'].get(), '原有内容\n附带配件：')
        self.assertEqual(page.live_name.cget('text'), '台灯')
        self.assertEqual(page.live_price.cget('text'), '¥ 25')
        self.assertEqual(float(page.progress['value']), 4)
        page.fields['description'].set('字' * 198)
        page.add_prompt('附带配件：')
        self.assertEqual(len(page.fields['description'].get()), 198)
        self.assertTrue(page.fields['description'].error.cget('text'))
        page.fields['description'].set('一盏台灯')
        page.submit()
        self.wait()
        panel = self.app.page.messages_panel
        panel.composer.set('原问题')
        panel.add_prompt('配件是否齐全？')
        self.assertEqual(panel.composer.get(), '原问题\n配件是否齐全？')
        panel.composer.set('')

    def test_account_counts_motion_and_banner_cleanup(self):
        self.login()
        self.app.show('account')
        self.wait()
        page = self.app.page
        self.assertEqual([w.cget('text') for w in page.stats.values], ['00','00','00'])
        page.nickname.set('新昵称')
        self.assertEqual(page.name_preview.cget('text'), '新昵称')
        page.nickname.set(page.original_nickname)
        page.toggle_motion()
        page.banner.animate(-5)
        self.assertIsNone(page.banner.job)
        self.assertEqual(page.banner.offset, 0)
        page.toggle_motion()
        page.banner.animate(-5)
        self.app.show('home')
        self.wait()

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
                if route == 'home':
                    hero = next(w for w in self.app.page.body.winfo_children() if isinstance(w, MarketHero))
                    copy = hero.winfo_children()[0]
                    action = copy.winfo_children()[-1]
                    self.assertGreaterEqual(action.winfo_height(), action.winfo_reqheight())
                    self.assertLessEqual(action.winfo_y()+action.winfo_height(), copy.winfo_height())


if __name__ == "__main__":
    unittest.main(verbosity=2)
