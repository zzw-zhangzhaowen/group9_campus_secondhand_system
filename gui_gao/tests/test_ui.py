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
from gui_gao.page_design import PageBanner


class TkFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="group9-ui-widgets-")
        self.gateway = Gateway.isolated(self.temp.name)
        self.gateway.register("student_a", "Campus123", "Gao")
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

    def test_retired_page_variables_are_released_on_destroy(self):
        # Hold references as a completed future or traceback might do.
        username = self.app.page.fields["username"].var
        self.app.show("register", force=True)
        self.wait()
        self.assertTrue(username._released)
        self.assertTrue(gc.isenabled())
        self.assertTrue(self.app.status.get() is not None)

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
        for key, value in dict(username="new_user", nickname="NewStudent", password="Campus456", confirm="Campus456").items():
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
        for key,value in dict(name="Test textbook", price="35", description="Good condition, with a few notes.", category="Books").items():
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
        self.app.page.fields["name"].set("Unfinished item")
        with patch("gui_gao.app.messagebox.askyesno", return_value=False):
            self.app.show("home")
        self.assertEqual(self.app.route, "publish")
        self.assertEqual(self.app.page.fields["name"].get(), "Unfinished item")
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
        self.app.page.nickname.set("GaoStudent")
        self.app.page.save_nickname()
        self.wait()
        self.assertEqual(self.gateway.user["nickname"], "GaoStudent")
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
        self.gateway.register("other_user", "Campus123", "OtherStudent")
        self.gateway.login("other_user", "Campus123")
        item = self.gateway.save_item(dict(name="Keyboard", category="Electronics", price="88", description="Bluetooth works", image_path=""))
        self.gateway.login("student_a", "Campus123")
        self.app.show("detail", item_id=item['id'])
        self.wait()
        page = self.app.page
        page.favorite()
        self.wait()
        self.assertTrue(page.favorited)
        page.messages_panel.composer.set("Is it still available?")
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
        page.fields['name'].set('Lamp')
        page.fields['price'].set('25')
        page.fields['description'].set('Existing text')
        page.add_prompt('Accessories: ')
        self.root.update()
        self.assertEqual(page.fields['description'].get(), 'Existing text\nAccessories: ')
        self.assertEqual(page.live_name.cget('text'), 'Lamp')
        self.assertEqual(page.live_price.cget('text'), '¥ 25')
        self.assertEqual(float(page.progress['value']), 4)
        page.fields['description'].set('x' * 198)
        page.add_prompt('Accessories: ')
        self.assertEqual(len(page.fields['description'].get()), 198)
        self.assertTrue(page.fields['description'].error.cget('text'))
        page.fields['description'].set('A reading lamp')
        page.submit()
        self.wait()
        panel = self.app.page.messages_panel
        panel.composer.set('Original question')
        panel.add_prompt('Are all accessories included?')
        self.assertEqual(panel.composer.get(), 'Original question\nAre all accessories included?')
        panel.composer.set('')

    def test_account_counts_motion_and_banner_cleanup(self):
        self.login()
        self.app.show('account')
        self.wait()
        page = self.app.page
        self.assertEqual([w.cget('text') for w in page.stats.values], ['00','00','00'])
        page.nickname.set('NewName')
        self.assertEqual(page.name_preview.cget('text'), 'NewName')
        page.nickname.set(page.original_nickname)
        page.toggle_motion()
        page.banner.animate(-5)
        self.assertIsNone(page.banner.job)
        self.assertEqual(page.banner.offset, 0)
        page.toggle_motion()
        page.banner.animate(-5)
        self.app.show('home')
        self.wait()

    def test_scene_switch_and_self_check_do_not_change_business_data(self):
        self.app.page.toggle_light()
        self.assertTrue(self.app.page.artwork.lit)
        self.app.page.toggle_light()
        self.assertFalse(self.app.page.artwork.lit)
        self.login()
        self.app.show('publish')
        self.wait()
        page = self.app.page
        for v in page.photo_check.values:
            v.set(True)
        page.photo_check.update_count()
        self.assertEqual(page.photo_check.summary.cget('text'), '3 / 3 checked')
        self.assertFalse(page.is_dirty())
        self.assertEqual(self.gateway.mine(), [])

    def test_route_and_clock_motion_pause_reduce_and_cleanup(self):
        self.login()
        self.root.deiconify()
        for kind in ('intentions', 'logs'):
            self.app.show('interactions', kind=kind)
            self.wait()
            banner = next(w for w in self.app.page.body.winfo_children() if isinstance(w, PageBanner))
            art = banner.art
            self.assertIsNotNone(art.job)
            banner.toggle_animation()
            self.assertIsNone(art.job)
            self.assertTrue(art.motion_paused)
            tag = 'pin-hole' if kind == 'intentions' else 'clock-hour'
            snapshots = []
            for elapsed in (0, 2.5, 4.5):
                art._draw_motion(elapsed)
                snapshots.append(art.coords(tag))
            if kind == 'intentions':
                self.assertLess(snapshots[0][0], snapshots[1][0])
                self.assertLess(snapshots[1][0], snapshots[2][0])
                self.assertLess(snapshots[1][1], snapshots[0][1])
            else:
                self.assertEqual(snapshots[0], snapshots[1])  # Hour holds until its tick.
                self.assertNotEqual(snapshots[1], snapshots[2])
                self.assertEqual(snapshots[0][:2], snapshots[2][:2])  # Pivot stays fixed.
            banner.toggle_animation()
            self.assertIsNotNone(art.job)
            self.app.show('home')
            self.wait()
            self.assertIsNone(art.job)
        self.app.reduce_motion = True
        self.app.show('interactions', kind='logs')
        self.wait()
        banner = next(w for w in self.app.page.body.winfo_children() if isinstance(w, PageBanner))
        self.assertIsNone(banner.art.job)
        self.assertTrue(banner.motion_control.instate(['disabled']))

    def test_view_filters_keep_records_and_leave_no_callbacks(self):
        self.login()
        self.app.show('interactions', kind='favorites')
        self.wait()
        page = self.app.page
        page.loaded([{'id': 999, 'name':'Inactive item', 'price':10, 'status':'Off sale',
                      'seller_id':self.gateway.user_id(), 'image_path':''}])
        page.available.set(True)
        page.filter_favorites()
        self.assertEqual(len(page.records), 1)
        page.available.set(False)
        page.filter_favorites()
        self.app.show('interactions', kind='logs')
        self.wait()
        page = self.app.page
        page.loaded([{'action_type':'Save item', 'detail':'Test item', 'timestamp':'Example'}])
        page.log_query.set('no-match')
        page.render()
        self.assertEqual(len(page.records), 1)
        page.log_query.set('Save item')
        page.render()
        self.app.show('account')
        self.wait()
        self.app.page.banner.animate(-7)
        self.app.show('home')
        self.wait()

    def test_image_zoom_limits_reset_and_close(self):
        self.login()
        asset = Path(__file__).resolve().parents[1]/'assets'/'book.png'
        item = self.gateway.save_item(dict(name='Book', category='Books', price='30',
                                          description='Image zoom check', image_path=str(asset)))
        self.app.show('detail', item_id=item['id'])
        self.wait()
        self.app.page.zoom_image()
        self.root.update()
        window = next(w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel))
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        buttons = {w.cget('text'): w for w in descendants(window)
                   if w.winfo_class() in ('TButton', 'Button')}
        canvas = next(w for w in window.winfo_children() if isinstance(w, tk.Canvas))
        initial_width = canvas.photo.width()
        self.assertTrue(buttons['− Zoom out'].instate(['disabled']))
        buttons['＋ Zoom in'].invoke()
        buttons['＋ Zoom in'].invoke()
        self.assertEqual(canvas.photo.width(), initial_width * 3)
        self.assertTrue(buttons['＋ Zoom in'].instate(['disabled']))
        buttons['Reset'].invoke()
        self.assertEqual(canvas.photo.width(), initial_width)
        buttons['Close preview'].invoke()
        self.root.update()
        self.assertFalse(window.winfo_exists())

    def test_native_png_demo_asset_preview(self):
        asset = Path(__file__).resolve().parents[1]/"assets"/"book.png"
        image = ItemImage(self.root, str(asset))
        self.assertIsNotNone(image.photo)
        self.assertEqual(image.reason, "")
        image.destroy()
        self.assertEqual(image_path("gui_gao/assets/book.png"), asset)

    def test_minimum_window_layout(self):
        self.login()
        item = self.gateway.save_item(dict(name="Test textbook", category="Books", price="35",
                                           description="Description", image_path=""))
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
