"""Frontend bridge to DU YI's services, without modifying team modules.

The private loader adapts only json_store imports inside the four feature modules.
No sys.modules mutation or global monkey patch; business methods remain their code.
All storage still delegates to ZHANG's locked, atomic JsonArrayStore.
"""
from __future__ import annotations

import builtins
from functools import lru_cache
from pathlib import Path
from types import ModuleType

from backend_zhang import json_store
from backend_zhang.exceptions import DataFileError
from .gateway import UserError, unwrap


class StoreBridge(json_store.JsonArrayStore):
    @property
    def lock(self):
        return json_store.get_file_lock(self.path)

    def read(self):
        return self.load()

    def write(self, records):
        return self.save(records)


@lru_cache(maxsize=4)
def service_class(name, class_name):
    """Load trusted checked-in team source with a module-local storage facade."""
    facade = ModuleType('backend_zhang.json_store')
    facade.__dict__.update(vars(json_store))
    facade.JsonStore = facade.JsonArrayStore = StoreBridge
    real_import = builtins.__import__

    def scoped_import(module, globals=None, locals=None, fromlist=(), level=0):
        if module == 'backend_zhang.json_store' and level == 0:
            return facade
        return real_import(module, globals, locals, fromlist, level)

    source = Path(__file__).resolve().parent.parent / 'feature_du' / f'{name}.py'
    module = ModuleType(f'gui_gao._feature_{name}')
    module.__file__ = str(source)
    module.__package__ = 'feature_du'
    module.__dict__['__builtins__'] = dict(vars(builtins), __import__=scoped_import)
    exec(compile(source.read_text(encoding='utf-8'), str(source), 'exec'), module.__dict__)
    return getattr(module, class_name)


class Features:
    def __init__(self, gateway, directory):
        self.gateway, self.directory = gateway, Path(directory)
        self.services = {}

    def service(self, name):
        if name not in self.services:
            classes = {'favorites': 'FavoriteService', 'messages': 'MessageService',
                       'intentions': 'IntentionService', 'logs': 'LogService'}
            filename = 'system_logs.json' if name == 'logs' else f'{name}.json'
            try:
                self.services[name] = service_class(name, classes[name])(str(self.directory / filename))
            except (ImportError, AttributeError, OSError, SyntaxError) as exc:
                raise UserError('互动模块暂时不可用，请检查 feature_du 是否完整。') from exc
        return self.services[name]

    def call(self, name, method, *args):
        try:
            return unwrap(getattr(self.service(name), method)(*args))
        except DataFileError as exc:
            raise UserError(str(exc)) from exc

    def person(self, uid):
        result = self.gateway.users.get_public_user_info(uid)
        return (result.get('data') or {}).get('nickname', '账号不可用') if result.get('success') else '账号不可用'

    def item(self, item_id):
        # Distinguish a deleted item from a storage read error; never swallow errors.
        if unwrap(self.gateway.items.item_exists(item_id, include_removed=True)):
            return unwrap(self.gateway.items.get_item_by_id(item_id, include_removed=True))
        deleted = unwrap(self.gateway.items.is_item_deleted(item_id))
        return {'id': item_id, 'name': deleted.get('name') or '商品已不可用',
                'status': '已删除', 'seller_id': deleted.get('seller_id'),
                'category': '', 'price': None, 'image_path': ''}

    def active(self, item_id):
        item = self.item(item_id)
        if item['status'] != '在售':
            raise UserError('商品已下架或删除，无法继续此操作。')
        return item

    def favorite_ids(self):
        return self.call('favorites', 'get_user_favorites', self.gateway.user_id())

    def favorites(self):
        return [self.item(i) for i in reversed(self.favorite_ids())]

    def toggle_favorite(self, item_id):
        uid = self.gateway.user_id()
        # Removal remains possible even after the item disappears.
        with self.service('favorites').store.lock:
            if item_id not in self.favorite_ids():
                self.active(item_id)
            value = self.call('favorites', 'toggle_favorite', uid, item_id)
        self.gateway.audit('取消收藏' if not value['favorited'] else '收藏商品', f'商品 #{item_id}')
        return value

    def messages(self, item_id):
        self.gateway.user_id()
        records = self.call('messages', 'get_item_messages', item_id)
        return [dict(r, nickname=self.person(r['user_id'])) for r in records]

    def add_message(self, item_id, content):
        uid = self.gateway.user_id()
        if not content.strip():
            raise UserError('请先填写留言内容。')
        if len(content.strip()) > 500:
            raise UserError('留言最多 500 个字符。')
        self.active(item_id)
        value = self.call('messages', 'add_message', item_id, uid, content.strip())
        self.gateway.audit('发布留言', f'商品 #{item_id}')
        return value

    def intentions(self):
        uid = self.gateway.user_id()
        records = self.call('intentions', 'get_user_intentions', uid)
        return [dict(r, item=self.item(r['item_id']), buyer=self.person(r['user_id']),
                     seller=self.person(r['seller_id'])) for r in reversed(records)]

    def create_intention(self, item_id):
        uid = self.gateway.user_id()
        item = self.active(item_id)
        if item['seller_id'] == uid:
            raise UserError('不能向自己发布的商品提交购买意向。')
        with self.service('intentions').store.lock:
            records = self.call('intentions', 'get_user_intentions', uid)
            if any(r['user_id'] == uid and r['item_id'] == item_id for r in records):
                raise UserError('你已提交过购买意向，可在「购买意向」查看。')
            value = self.call('intentions', 'create_intention', uid, item_id, item['seller_id'])
        self.gateway.audit('提交购买意向', f'商品 #{item_id}')
        return value

    def threads(self):
        """Find related discussions, including removed/deleted unbookmarked goods.

        The team service exposes per-item messages only. Obtain candidate IDs
        through its existing store (no direct file I/O), then use public methods
        to load each conversation. This bridge can disappear when the service
        adds a user-thread endpoint.
        """
        uid = self.gateway.user_id()
        try:
            message_records = self.service('messages').store.read()
        except DataFileError as exc:
            raise UserError(str(exc)) from exc
        item_ids = dict.fromkeys(r['item_id'] for r in message_records)
        threads = []
        for item_id in item_ids:
            item = self.item(item_id)
            records = self.messages(item['id'])
            if records and (item['seller_id'] == uid or any(r['user_id'] == uid for r in records)):
                threads.append({'item': item, 'messages': records})
        return sorted(threads, key=lambda r: r['messages'][-1]['created_at'], reverse=True)

    def logs(self):
        uid = self.gateway.user_id()
        return [r for r in reversed(self.call('logs', 'get_logs')) if r.get('user_id') == uid]

    def log(self, action, detail):
        return self.call('logs', 'log_action', self.gateway.user_id(), action, detail)
