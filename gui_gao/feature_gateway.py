"""Frontend bridge to DU YI's services, without modifying team modules.

The private loader binds service imports to the current gateway's data context.
No sys.modules mutation or global monkey patch; business methods remain their code.
All storage still delegates to ZHANG's locked, atomic JsonArrayStore.
"""
from __future__ import annotations

import builtins
from pathlib import Path
from types import ModuleType

from backend_zhang import json_store
from backend_zhang.exceptions import DataFileError
from .gateway import UserError, unwrap
from .localization import present_item, present_log


class StoreBridge(json_store.JsonArrayStore):
    @property
    def lock(self):
        return json_store.get_file_lock(self.path)

    def read(self):
        return self.load()

    def write(self, records):
        return self.save(records)


def service_class(name, class_name, *, users=None, items=None):
    """Load team source with local storage and service bindings, never globals.

    The feature services now validate users and items through module imports.
    Bind those imports to this gateway so a demo never reads production data.
    """
    import backend_zhang
    facade = ModuleType('backend_zhang.json_store')
    facade.__dict__.update(vars(json_store))
    facade.JsonStore = facade.JsonArrayStore = StoreBridge
    backend = ModuleType('backend_zhang')
    backend.__dict__.update(vars(backend_zhang))
    if users is not None:
        backend.user_service = users
    if items is not None:
        backend.item_service = items
    real_import = builtins.__import__

    def scoped_import(module, globals=None, locals=None, fromlist=(), level=0):
        if module == 'backend_zhang.json_store' and level == 0:
            return facade
        if module == 'backend_zhang' and level == 0 and fromlist:
            return backend
        if module == 'backend_zhang.user_service' and level == 0 and users is not None:
            return users if fromlist else backend
        if module == 'backend_zhang.item_service' and level == 0 and items is not None:
            return items if fromlist else backend
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
                cls = service_class(name, classes[name], users=self.gateway.users, items=self.gateway.items)
                self.services[name] = cls(str(self.directory / filename))
            except (ImportError, AttributeError, OSError, SyntaxError) as exc:
                raise UserError('Community features are unavailable. Check that feature_du is installed.') from exc
        return self.services[name]

    def call(self, name, method, *args):
        try:
            return unwrap(getattr(self.service(name), method)(*args))
        except DataFileError as exc:
            raise UserError(str(exc)) from exc

    def person(self, uid):
        result = self.gateway.users.get_public_user_info(uid)
        return (result.get('data') or {}).get('nickname', 'Account unavailable') if result.get('success') else 'Account unavailable'

    def item(self, item_id):
        # Distinguish a deleted item from a storage read error; never swallow errors.
        if unwrap(self.gateway.items.item_exists(item_id, include_removed=True)):
            return present_item(unwrap(self.gateway.items.get_item_by_id(item_id, include_removed=True)))
        deleted = unwrap(self.gateway.items.is_item_deleted(item_id))
        return {'id': item_id, 'name': deleted.get('name') or 'Item unavailable',
                'status': 'Deleted', 'seller_id': deleted.get('seller_id'),
                'category': '', 'price': None, 'image_path': ''}

    def active(self, item_id):
        item = self.item(item_id)
        if item['status'] != 'Available':
            raise UserError('This item is off sale or deleted. This action is unavailable.')
        return item

    def favorite_ids(self):
        # The public query now omits deleted items. Keep their saved history
        # through the service's store, just as threads use its message store.
        uid = self.gateway.user_id()
        try:
            records = self.service('favorites').store.load()
        except DataFileError as exc:
            raise UserError(str(exc)) from exc
        return [r['item_id'] for r in records if r.get('user_id') == uid]

    def favorites(self):
        return [self.item(i) for i in reversed(self.favorite_ids())]

    def toggle_favorite(self, item_id):
        uid = self.gateway.user_id()
        # The current team service blocks all toggles for unavailable items.
        with self.service('favorites').store.lock:
            self.active(item_id)
            result = self.call('favorites', 'toggle_favorite', uid, item_id)
            # Current service returns a record on save and None on removal.
            value = {'favorited': result is not None, 'item_id': item_id}
        self.gateway.audit('Unsave' if not value['favorited'] else 'Save item', f'Item #{item_id}')
        return value

    def messages(self, item_id):
        self.gateway.user_id()
        records = self.call('messages', 'get_item_messages', item_id)
        return [dict(r, nickname=self.person(r['user_id'])) for r in records]

    def add_message(self, item_id, content):
        uid = self.gateway.user_id()
        if not content.strip():
            raise UserError('Enter a comment first.')
        if len(content.strip()) > 500:
            raise UserError('Comments are limited to 500 characters.')
        self.active(item_id)
        value = self.call('messages', 'add_message', item_id, uid, content.strip())
        self.gateway.audit('Post comment', f'Item #{item_id}')
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
            raise UserError('You cannot send an enquiry about your own item.')
        with self.service('intentions').store.lock:
            records = self.call('intentions', 'get_user_intentions', uid)
            if any(r['user_id'] == uid and r['item_id'] == item_id for r in records):
                raise UserError('You have already sent an enquiry. View it in Enquiries.')
            value = self.call('intentions', 'create_intention', uid, item_id, item['seller_id'])
        self.gateway.audit('Send enquiry', f'Item #{item_id}')
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
        return [present_log(r) for r in reversed(self.call('logs', 'get_logs')) if r.get('user_id') == uid]

    def log(self, action, detail):
        return self.call('logs', 'log_action', self.gateway.user_id(), action, detail)
