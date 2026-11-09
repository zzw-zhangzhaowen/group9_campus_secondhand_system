"""Integration against actual team feature sources and isolated storage."""
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from gui_gao.gateway import Gateway, UserError
from gui_gao.feature_gateway import service_class
from backend_zhang import json_store


class FeatureIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='group9-features-')
        self.addCleanup(self.temp.cleanup)
        self.g = Gateway.isolated(self.temp.name)
        self.g.register('seller_one', 'Campus123', 'Seller')
        self.g.register('buyer_one', 'Campus123', 'Buyer')
        self.g.login('seller_one', 'Campus123')
        self.item = self.g.save_item(dict(name='Test keyboard', category='Electronics', price='88', description='Bluetooth keyboard', image_path=''))
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
        self.assertEqual(other.features.favorites()[0]['name'], 'Test keyboard')
        other.login('seller_one', 'Campus123')
        self.assertEqual(other.features.favorites(), [])
        self.assertFalse(self.g.features.toggle_favorite(self.item['id'])['favorited'])

    def test_deleted_favorite_keeps_history_and_respects_service_restriction(self):
        self.g.features.toggle_favorite(self.item['id'])
        self.g.login('seller_one', 'Campus123')
        self.g.change_item('delete', self.item['id'])
        self.g.login('buyer_one', 'Campus123')
        record = self.g.features.favorites()[0]
        self.assertEqual((record['name'],record['status']), ('Test keyboard','Deleted'))
        with self.assertRaises(UserError):
            self.g.features.toggle_favorite(self.item['id'])
        self.assertEqual(len(self.g.features.favorites()), 1)

    def test_messages_validated_persisted_and_related_thread(self):
        for content in ['', ' \n ', 'x'*501]:
            with self.assertRaises(UserError): self.g.features.add_message(self.item['id'], content)
        self.g.features.add_message(self.item['id'], ' Are all accessories included? ')
        messages = self.g.features.messages(self.item['id'])
        self.assertEqual(messages[0]['content'], 'Are all accessories included?')
        self.assertEqual(messages[0]['nickname'], 'Buyer')
        self.assertEqual(len(self.g.features.threads()), 1)
        self.g.login('seller_one', 'Campus123')
        self.assertEqual(len(self.g.features.threads()), 1)
        self.g.features.add_message(self.item['id'], 'Yes, all included.')
        self.assertEqual(len(self.g.features.messages(self.item['id'])), 2)

    def test_intentions_buyer_seller_views_duplicate_and_self_guard(self):
        self.g.features.create_intention(self.item['id'])
        self.assertEqual(len(self.g.features.intentions()), 1)
        with self.assertRaises(UserError): self.g.features.create_intention(self.item['id'])
        self.g.login('seller_one', 'Campus123')
        self.assertEqual(self.g.features.intentions()[0]['buyer'], 'Buyer')
        with self.assertRaises(UserError): self.g.features.create_intention(self.item['id'])

    def test_deleted_unbookmarked_discussion_remains_only_for_participants(self):
        self.g.features.add_message(self.item['id'], 'Are accessories included?')
        self.g.login('seller_one', 'Campus123')
        self.g.change_item('delete', self.item['id'])
        self.assertEqual(self.g.features.threads()[0]['item']['status'], 'Deleted')
        self.g.login('buyer_one', 'Campus123')
        self.assertEqual(len(self.g.features.threads()), 1)
        self.g.register('outsider_one', 'Campus123', 'OtherStudent')
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
        self.g.features.add_message(self.item['id'], 'Hello')
        self.g.login('seller_one', 'Campus123')
        self.g.change_item('remove', self.item['id'])
        self.g.login('buyer_one', 'Campus123')
        for operation in [lambda: self.g.features.add_message(self.item['id'], 'hi'), lambda: self.g.features.create_intention(self.item['id'])]:
            with self.assertRaises(UserError): operation()
        self.assertEqual(self.g.features.intentions()[0]['item']['status'], 'Off sale')
        self.assertEqual(len(self.g.features.messages(self.item['id'])),1)
        with self.assertRaises(UserError): self.g.features.toggle_favorite(self.item['id'])
        self.g.login('seller_one', 'Campus123')
        self.g.change_item('restore', self.item['id'])
        self.g.login('buyer_one', 'Campus123')
        self.assertFalse(self.g.features.toggle_favorite(self.item['id'])['favorited'])

    def test_isolated_feature_validation_never_uses_production_services(self):
        from backend_zhang import user_service, item_service
        with patch.object(user_service, 'get_user_service', side_effect=AssertionError('Production users accessed')), \
             patch.object(item_service, 'get_item_service', side_effect=AssertionError('Production items accessed')):
            self.assertTrue(self.g.features.toggle_favorite(self.item['id'])['favorited'])
            self.g.features.add_message(self.item['id'], 'Test comment')
            self.g.features.create_intention(self.item['id'])
            self.assertEqual(len(self.g.features.intentions()), 1)
            self.assertTrue(self.g.features.logs())
            self.assertFalse(self.g.warning)

    def test_feature_contexts_with_matching_ids_remain_separate(self):
        with tempfile.TemporaryDirectory() as other_dir:
            other = Gateway.isolated(other_dir)
            other.register('other_user', 'Campus123', 'OtherStudent')
            other.login('other_user', 'Campus123')
            own = other.save_item(dict(name='Other item', category='Books', price='12',
                                       description='Separate directory', image_path=''))
            self.assertEqual(own['id'], self.item['id'])
            self.g.features.toggle_favorite(self.item['id'])
            self.g.features.add_message(self.item['id'], 'First context')
            other.features.add_message(own['id'], 'Second context')
            self.assertEqual(other.features.favorites(), [])
            self.assertEqual([m['content'] for m in other.features.messages(own['id'])], ['Second context'])
            self.assertEqual([m['content'] for m in self.g.features.messages(self.item['id'])], ['First context'])

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
        self.assertIn('Changes saved', self.g.warning)
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
