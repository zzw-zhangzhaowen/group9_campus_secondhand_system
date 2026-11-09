"""English UI contract checks using the unchanged team backend."""
import tempfile
import unittest
from backend_zhang.config import CATEGORIES, STATUS_ON_SALE, STATUS_OFF_SALE
from gui_gao.gateway import Gateway, UserError
from gui_gao.localization import present_item, present_log, error_text


class EnglishPresentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.g = Gateway.isolated(self.temp.name)
        self.g.register('en_student', 'Campus123', 'Student')
        self.g.login('en_student', 'Campus123')

    def test_category_mapping_keeps_the_team_wire_contract(self):
        for english, wire in zip(('Books', 'Electronics', 'Clothing', 'Home & Living'), CATEGORIES):
            with self.subTest(category=english):
                item = self.g.save_item(dict(name='Test item', category=english, price='12',
                                             description='Original description', image_path=''))
                raw = self.g.items.get_item_by_id(item['id'])['data']
                self.assertEqual((raw['category'], raw['status']), (wire, STATUS_ON_SALE))
                self.assertEqual((item['category'], item['status']), (english, 'Available'))
                self.assertEqual([r['id'] for r in self.g.browse(category=english)], [item['id']])
                self.g.change_item('remove', item['id'])
                self.assertEqual(self.g.detail(item['id'])['status'], 'Off sale')
                self.assertEqual(self.g.items.get_item_by_id(item['id'], include_removed=True)['data']['status'], STATUS_OFF_SALE)
                self.g.change_item('restore', item['id'])
                self.assertEqual(self.g.detail(item['id'])['status'], 'Available')

    def test_user_written_content_is_neither_translated_nor_mutated(self):
        original = dict(name='\u6211\u7684\u4e66', description='\u6211\u7684\u7b14\u8bb0',
                        category=CATEGORIES[0], status=STATUS_ON_SALE)
        snapshot = dict(original)
        shown = present_item(original)
        self.assertEqual(original, snapshot)
        self.assertEqual((shown['name'], shown['description']), (original['name'], original['description']))
        self.assertIsNot(shown, original)

    def test_service_errors_are_english(self):
        with self.assertRaisesRegex(UserError, 'Incorrect username or password'):
            self.g.login('en_student', 'Wrong123')
        with self.assertRaisesRegex(UserError, 'already taken'):
            self.g.register('en_student', 'Campus123', 'Student')
        self.assertNotRegex(error_text('\u672a\u77e5\u9519\u8bef'), r'[\u3400-\u9fff]')

    def test_legacy_log_labels_preserve_user_titles(self):
        record = dict(action_type='\u53d1\u5e03\u5546\u54c1', detail='\u5546\u54c1 #3 · \u6211\u7684\u4e66')
        shown = present_log(record)
        self.assertEqual(shown['action_type'], 'List item')
        self.assertEqual(shown['detail'], 'Item #3 · \u6211\u7684\u4e66')
        self.assertEqual(record['action_type'], '\u53d1\u5e03\u5546\u54c1')
        for action, label in (('\u66f4\u65b0\u6635\u79f0', 'Update display name'),
                              ('\u66f4\u65b0\u5bc6\u7801', 'Update password')):
            self.assertEqual(present_log(dict(action_type=action))['action_type'], label)


if __name__ == '__main__':
    unittest.main()
