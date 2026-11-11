import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import unittest
import tempfile
import shutil
import os

from backend_zhang.user_service import (
    register_user, login_user, get_user_by_id, get_public_user_info,
    update_nickname, change_password, user_exists, reset_user_service
)
from backend_zhang.item_service import (
    create_item, get_all_items, get_item_by_id, get_items_by_seller,
    update_item, remove_item, restore_item, delete_item_permanently,
    search_items, item_exists, is_item_active, get_item_status,
    get_public_item_info, is_item_deleted, list_deleted_items, reset_item_service
)
from backend_zhang.user_repository import UserRepository

from feature_du.favorites import FavoriteService
from feature_du.intentions import IntentionService
from feature_du.messages import MessageService


class TestFeatureC(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.user_file = os.path.join(self.tmp, "c_test_users.json")
        self.item_file = os.path.join(self.tmp, "c_test_items.json")

        reset_user_service(data_file=self.user_file)
        buyer_reg = register_user("buyer01", "Buy@123456", "BuyerXiaoMing")
        seller_reg = register_user("seller02", "Sell@123456", "SellerAhHua")
        self.buyer_id = buyer_reg["data"]["id"]
        self.seller_id = seller_reg["data"]["id"]

        ur = UserRepository(data_file=self.user_file)
        reset_item_service(data_file=self.item_file, user_repository=ur)
    
        item_res = create_item(self.seller_id, "Headphones", "electronics", 60, "Works normally")
        if not item_res["success"]:
            raise RuntimeError(f"Failed to create item, response: {item_res}")
        self.item_id = item_res["data"]["id"]

        self.fav_path = os.path.join(self.tmp, "fav.json")
        self.int_path = os.path.join(self.tmp, "int.json")
        self.msg_path = os.path.join(self.tmp, "msg.json")

        self.fav_service = FavoriteService(data_file=self.fav_path)
        self.int_service = IntentionService(data_file=self.int_path)
        self.msg_service = MessageService(data_file=self.msg_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_favorite_toggle_add(self):
        res = self.fav_service.toggle_favorite(user_id=self.buyer_id, item_id=self.item_id)
        self.assertEqual(res["success"], True)
        self.assertEqual(res["message"], "Item favorited successfully")

    def test_favorite_toggle_remove(self):
        self.fav_service.toggle_favorite(user_id=self.buyer_id, item_id=self.item_id)
        res = self.fav_service.toggle_favorite(user_id=self.buyer_id, item_id=self.item_id)
        self.assertEqual(res["success"], True)
        self.assertEqual(res["message"], "Item removed from favorites")

    def test_favorite_get_user_fav(self):
        self.fav_service.toggle_favorite(user_id=self.buyer_id, item_id=self.item_id)
        res = self.fav_service.get_user_favorites(user_id=self.buyer_id)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["data"]), 1)

    def test_intention_create_normal(self):
        res = self.int_service.create_intention(
            user_id=self.buyer_id,
            item_id=self.item_id,
            seller_id=self.seller_id
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["message"], "Purchase intention submitted successfully")

    def test_intention_self_item_fail(self):
        res = self.int_service.create_intention(
            user_id=self.seller_id,
            item_id=self.item_id,
            seller_id=self.seller_id
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["message"], "Cannot submit purchase intention for your own item")

    def test_intention_get_user_intention(self):
        self.int_service.create_intention(self.buyer_id, self.item_id, self.seller_id)
        res = self.int_service.get_user_intentions(self.buyer_id)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["data"]), 1)

    def test_message_add_normal(self):
        res = self.msg_service.add_message(
            item_id=self.item_id,
            user_id=self.buyer_id,
            content="Is this still available?"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["message"], "Message added successfully")

    def test_message_add_empty_fail(self):
        res = self.msg_service.add_message(
            item_id=self.item_id,
            user_id=self.buyer_id,
            content="   "
        )
        self.assertFalse(res["success"])

    def test_message_get_item_msg(self):
        self.msg_service.add_message(self.item_id, self.buyer_id, "When can we meet for handover?")
        res = self.msg_service.get_item_messages(item_id=self.item_id)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["data"]), 1)


class TestUserModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp()
        cls.user_file = os.path.join(cls.tmp_dir, "test_users.json")
        reset_user_service(data_file=cls.user_file)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_register_success(self):
        res = register_user("Tom01", "Abc123456", "TomStudent")
        self.assertEqual(res["success"], True)
        self.assertNotIn("password_hash", res["data"])

    def test_register_dup_username(self):
        register_user("Jack01", "Def654321", "Jack")
        res = register_user("Jack01", "Other98765", "DuplicateNameTest")
        self.assertEqual(res["success"], False)
        self.assertEqual(res["message"], "Username already exists")

    def test_register_bad_password(self):
        res = register_user("Lily01", "123", "Lily")
        self.assertEqual(res["success"], False)

    def test_login_correct(self):
        register_user("Alice01", "Qwe789012", "Alice")
        res = login_user("Alice01", "Qwe789012")
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["data"]["id"])

    def test_login_wrong_password(self):
        register_user("Bob01", "Zxc345678", "Bob")
        res = login_user("Bob01", "wrongpass")
        self.assertFalse(res["success"])
        self.assertEqual(res["message"], "Invalid username or password")

    def test_update_nickname(self):
        reg = register_user("UserA01", "Aaa111111", "OldNickname")
        uid = reg["data"]["id"]
        res = update_nickname(uid, "BrandNewNickname")
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["nickname"], "BrandNewNickname")

    def test_change_password(self):
        reg = register_user("PwUser01", "Ppp123456", "PasswordTester")
        uid = reg["data"]["id"]
        res = change_password(uid, "Ppp123456", "Newp@ss99")
        self.assertTrue(res["success"])
        new_login = login_user("PwUser01", "Newp@ss99")
        self.assertTrue(new_login["success"])

    def test_user_exists_true_false(self):
        reg = register_user("ExistUser", "Eee123456", "Exist")
        uid = reg["data"]["id"]
        r1 = user_exists(uid)
        self.assertEqual(r1["data"], True)
        r2 = user_exists(99999)
        self.assertEqual(r2["data"], False)


class TestItemModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp()
        cls.u_file = os.path.join(cls.tmp_dir, "u.json")
        cls.i_file = os.path.join(cls.tmp_dir, "i.json")
        cls.del_file = os.path.join(cls.tmp_dir, "items_deleted.json")
        cls.meta_file = os.path.join(cls.tmp_dir, "items_meta.json")
        reset_user_service(data_file=cls.u_file)
        reg_res = register_user("Seller01", "Sell123456", "SellerWang")
        cls.seller_id = reg_res["data"]["id"]
        ur = UserRepository(data_file=cls.u_file)
        reset_item_service(data_file=cls.i_file, user_repository=ur,
                            deleted_file=cls.del_file, meta_file=cls.meta_file)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_create_item_ok(self):
        res = create_item(self.seller_id, "Python Textbook", "books", 32.0, "90% new textbook")
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["name"], "Python Textbook")
        self.item1_id = res["data"]["id"]

    def test_create_item_price_negative(self):
        res = create_item(self.seller_id, "Broken Headphone", "electronics", -10, "Broken headphone")
        self.assertFalse(res["success"])

    def test_search_by_keyword(self):
        create_item(self.seller_id, "Mechanical Keyboard", "electronics", 88, "Blue switch keyboard")
        res = search_items(keyword="keyboard")
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["data"]), 1)

    def test_remove_restore_item(self):
        r = create_item(self.seller_id, "Desk Lamp", "household", 29, "Dorm lamp")
        iid = r["data"]["id"]

        down = remove_item(iid, self.seller_id)
        self.assertTrue(down["success"])
        q1 = get_item_by_id(iid)
        self.assertFalse(q1["success"])

        up = restore_item(iid, self.seller_id)
        self.assertTrue(up["success"])
        q2 = get_item_by_id(iid)
        self.assertTrue(q2["success"])

    def test_permanent_delete_item(self):
        r = create_item(self.seller_id, "Notebook", "household", 5, "Paper notebook")
        iid = r["data"]["id"]
        del_res = delete_item_permanently(iid, self.seller_id)
        self.assertTrue(del_res["success"])
        q = get_item_by_id(iid)
        self.assertFalse(q["success"])

    def test_update_item(self):
        r = create_item(self.seller_id, "Water Cup", "household", 18, "Daily cup")
        iid = r["data"]["id"]
        res = update_item(iid, self.seller_id, {"price": 12, "description": "Price reduced"})
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["price"], 12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
