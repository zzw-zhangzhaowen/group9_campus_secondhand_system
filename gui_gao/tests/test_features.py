"""Integration against actual team feature sources and isolated storage."""
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from gui_gao.gateway import Gateway, UserError
from gui_gao.feature_gateway import service_class
from backend_zhang import json_store


class FeatureIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='group9-features-')
        self.addCleanup(self.temp.cleanup)
        self.g = Gateway.isolated(self.temp.name)
        self.g.register('seller_one', 'Campus123', '小卖家')
        self.g.register('buyer_one', 'Campus123', '小买家')
        self.g.login('seller_one', 'Campus123')
        self.item = self.g.save_item(dict(name='测试键盘', category='电子产品', price='88', description='蓝牙键盘', image_path=''))
        self.g.login('buyer_one', 'Campus123')

    def test_private_loader_preserves_global_storage_module(self):
        for module, cls in [('favorites','FavoriteService'), ('messages','MessageService'), ('logs','LogService'), ('intentions','IntentionService')]:
            self.assertEqual(service_class(module,cls).__name__, cls)
        self.assertFalse(hasattr(json_store, 'JsonStore'))
        self.assertFalse(hasattr(json_store.JsonArrayStore, 'read'))

    def test_favorite_persists_across_restart_and_is_private(self):
        self.g.features.toggle_favorite(self.item['id'])
        other = Gateway.isolated(self.temp.name)
        other.login('buyer_one', 'Campus123')
        self.assertEqual(other.features.favorites()[0]['name'], '测试键盘')
        other.login('seller_one', 'Campus123')
        self.assertEqual(other.features.favorites(), [])
        self.assertFalse(self.g.features.toggle_favorite(self.item['id'])['favorited'])

    def test_deleted_favorite_keeps_identity_and_can_be_removed(self):
        self.g.features.toggle_favorite(self.item['id'])
        self.g.login('seller_one', 'Campus123')
        self.g.change_item('delete', self.item['id'])
        self.g.login('buyer_one', 'Campus123')
        record = self.g.features.favorites()[0]
        self.assertEqual((record['name'],record['status']), ('测试键盘','已删除'))
        self.g.features.toggle_favorite(self.item['id'])
        self.assertEqual(self.g.features.favorites(), [])

    def test_messages_validated_persisted_and_related_thread(self):
        for content in ['', ' \n ', '字'*501]:
            with self.assertRaises(UserError): self.g.features.add_message(self.item['id'], content)
        self.g.features.add_message(self.item['id'], ' 请问配件齐全吗？ ')
        messages = self.g.features.messages(self.item['id'])
        self.assertEqual(messages[0]['content'], '请问配件齐全吗？')
        self.assertEqual(messages[0]['nickname'], '小买家')
        self.assertEqual(len(self.g.features.threads()), 1)
        self.g.login('seller_one', 'Campus123')
        self.assertEqual(len(self.g.features.threads()), 1)
        self.g.features.add_message(self.item['id'], '齐全。')
        self.assertEqual(len(self.g.features.messages(self.item['id'])), 2)

    def test_intentions_buyer_seller_views_duplicate_and_self_guard(self):
        self.g.features.create_intention(self.item['id'])
        self.assertEqual(len(self.g.features.intentions()), 1)
        with self.assertRaises(UserError): self.g.features.create_intention(self.item['id'])
        self.g.login('seller_one', 'Campus123')
        self.assertEqual(self.g.features.intentions()[0]['buyer'], '小买家')
        with self.assertRaises(UserError): self.g.features.create_intention(self.item['id'])

    def test_deleted_unbookmarked_discussion_remains_only_for_participants(self):
        self.g.features.add_message(self.item['id'], '配件齐全吗？')
        self.g.login('seller_one', 'Campus123')
        self.g.change_item('delete', self.item['id'])
        self.assertEqual(self.g.features.threads()[0]['item']['status'], '已删除')
        self.g.login('buyer_one', 'Campus123')
        self.assertEqual(len(self.g.features.threads()), 1)
        self.g.register('outsider_one', 'Campus123', '其他同学')
        self.g.login('outsider_one', 'Campus123')
        self.assertEqual(self.g.features.threads(), [])

    def test_concurrent_double_submit_creates_one_intention(self):
        def submit():
            try: return self.g.features.create_intention(self.item['id'])
            except UserError: return None
        # Resolve the lazy service before exercising concurrent calls.
        self.g.features.service('intentions')
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: submit(), range(2)))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(len(self.g.features.intentions()), 1)

    def test_inactive_goods_block_new_activity_but_keep_history(self):
        self.g.features.toggle_favorite(self.item['id'])
        self.g.features.create_intention(self.item['id'])
        self.g.features.add_message(self.item['id'], '你好')
        self.g.login('seller_one', 'Campus123')
        self.g.change_item('remove', self.item['id'])
        self.g.login('buyer_one', 'Campus123')
        for operation in [lambda: self.g.features.add_message(self.item['id'], 'hi'), lambda: self.g.features.create_intention(self.item['id'])]:
            with self.assertRaises(UserError): operation()
        self.assertEqual(self.g.features.intentions()[0]['item']['status'], '已下架')
        self.assertEqual(len(self.g.features.messages(self.item['id'])),1)
        self.g.features.toggle_favorite(self.item['id'])
        with self.assertRaises(UserError): self.g.features.toggle_favorite(self.item['id'])

    def test_logs_filter_identity_and_exclude_secrets(self):
        self.g.features.add_message(self.item['id'], 'private message content')
        self.g.password('Campus123', 'Changed123')
        records = self.g.features.logs()
        self.assertTrue(all(r['user_id'] == self.g.user_id() for r in records))
        for forbidden in ['Campus123','Changed123','private message content']:
            self.assertNotIn(forbidden, str(records))

    def test_corrupt_feature_storage_preserved_and_visible_failure(self):
        path = Path(self.temp.name)/'favorites.json'
        path.write_text('{broken', encoding='utf-8')
        with self.assertRaises(UserError): self.g.features.favorites()
        with self.assertRaises(UserError): self.g.features.toggle_favorite(self.item['id'])
        self.assertEqual(path.read_text(), '{broken')

    def test_failed_log_does_not_retry_completed_business_action(self):
        path = Path(self.temp.name)/'system_logs.json'
        path.write_text('{broken', encoding='utf-8')
        value = self.g.features.create_intention(self.item['id'])
        self.assertTrue(value['intention_id'])
        self.assertIn('操作已保存', self.g.warning)
        self.assertEqual(len(self.g.features.intentions()), 1)
        self.assertEqual(path.read_text(), '{broken')

    def test_logged_out_feature_actions_rejected(self):
        self.g.logout()
        for operation in [self.g.features.favorites, self.g.features.intentions, self.g.features.threads, self.g.features.logs,
                          lambda: self.g.features.messages(self.item['id']), lambda: self.g.features.add_message(self.item['id'],'hi'),
                          lambda: self.g.features.create_intention(self.item['id']), lambda: self.g.features.toggle_favorite(self.item['id'])]:
            with self.assertRaises(UserError): operation()


if __name__ == '__main__':
    unittest.main()
