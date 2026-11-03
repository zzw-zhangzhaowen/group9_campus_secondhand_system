"""Favorites, public item discussions, purchase intentions and personal activity."""
from tkinter import ttk
from . import theme as t
from .widgets import ScrollPage, Field, ItemImage, page_title, empty_state

TABS = {'favorites': '我的收藏', 'messages': '商品留言', 'intentions': '购买意向', 'logs': '操作记录'}


class MessagePanel(ttk.Frame):
    def __init__(self, parent, app, item):
        super().__init__(parent, padding=20, relief='solid', borderwidth=1)
        self.app, self.item = app, item
        header = ttk.Frame(self)
        header.pack(fill='x')
        t.label(header, '商品留言', size=19, bold=True).pack(side='left')
        t.button(header, '刷新留言', self.start, 'nav').pack(side='right')
        t.label(self, '这里是公开留言区，买卖双方可以讨论商品状况和交收安排。',
                color=t.MUTED, size=11, wraplength=740, justify='left').pack(anchor='w', pady=(8, 16))
        self.list = ttk.Frame(self)
        self.list.pack(fill='x')
        self.feedback = t.label(self, '', color=t.RED, wraplength=740, justify='left')
        self.feedback.pack(anchor='w', pady=10)
        self.composer = None
        if item['status'] == '在售':
            self.composer = Field(self, '写一条留言', multiline=True, hint='最多 500 字。此留言会展示给查看商品的同学。')
            self.composer.input.configure(height=3)
            self.composer.pack(fill='x')
            t.button(self, '发布留言  →', self.send, 'primary').pack(anchor='e')
        else:
            t.label(self, '商品已不可交易，历史留言仍可查看。', color=t.MUTED).pack(anchor='w')

    def is_dirty(self):
        return bool(self.composer and self.composer.get().strip())

    def start(self):
        self.app.run_task(lambda: self.app.gateway.features.messages(self.item['id']), self.loaded,
                          lambda message: self.feedback.configure(text=message))

    def loaded(self, records):
        self.feedback.configure(text='')
        for child in self.list.winfo_children():
            child.destroy()
        if not records:
            t.label(self.list, '还没有留言。成为第一个提问的人吧。', color=t.MUTED).pack(anchor='w', pady=12)
        for record in records:
            row = ttk.Frame(self.list, padding=(0, 10))
            row.pack(fill='x')
            who = record['nickname'] + (' · 卖家' if record['user_id'] == self.item['seller_id'] else '')
            t.label(row, who, bold=True, color=t.BLUE).pack(anchor='w')
            t.label(row, record['content'], wraplength=750, justify='left').pack(anchor='w', pady=6)
            t.label(row, record['created_at'], size=10, color=t.MUTED).pack(anchor='w')
            ttk.Separator(row).pack(fill='x', pady=(10, 0))

    def send(self):
        if self.app.busy or not self.composer:
            return
        text = self.composer.get().strip()
        if not text or len(text) > 500:
            self.composer.show_error('请填写 1–500 字的留言。')
            self.composer.input.focus_set()
            return
        self.composer.show_error('')
        def saved(_):
            self.composer.set('')
            self.start()
        self.app.run_task(lambda: self.app.gateway.features.add_message(self.item['id'], text), saved,
                          lambda message: self.feedback.configure(text=message))


class InteractionPage(ScrollPage):
    def __init__(self, parent, app, kind='favorites', item_id=None):
        super().__init__(parent)
        self.app, self.kind, self.item_id = app, kind, item_id
        self.direction = 'sent'
        self.records = []
        self.panel = None
        page_title(self.body, '喜欢的好物，在这里续上故事。', '收藏心动、聊聊细节，或看看你发出和收到的购买意向。')
        tabs = ttk.Frame(self.body)
        tabs.pack(fill='x', pady=(0, 22))
        for value, title in TABS.items():
            t.button(tabs, title, lambda k=value: app.show('interactions', kind=k),
                     'selected' if kind == value else 'nav').pack(side='left', padx=(0, 12))
        t.button(tabs, '刷新', self.start, 'nav').pack(side='right')
        self.area = ttk.Frame(self.body)
        self.area.pack(fill='both', expand=True)

    def is_dirty(self):
        return bool(self.panel and self.panel.is_dirty())

    def start(self):
        if self.is_dirty():
            # A refresh updates messages only and preserves the current draft.
            self.panel.start()
            return
        features = self.app.gateway.features
        if self.kind == 'messages' and self.item_id is not None:
            self.app.run_task(lambda: features.item(self.item_id), self.thread, self.failed)
            return
        method = {'favorites': features.favorites, 'messages': features.threads,
                  'intentions': features.intentions, 'logs': features.logs}[self.kind]
        self.app.run_task(method, self.loaded, self.failed)

    def clear(self):
        self.panel = None
        for child in self.area.winfo_children():
            child.destroy()

    def failed(self, message):
        self.clear()
        empty_state(self.area, '暂时无法加载' + TABS[self.kind], message, self.start)

    def loaded(self, records):
        self.records = records
        self.render()

    def thread(self, item):
        self.clear()
        t.button(self.area, '‹ 返回留言列表', lambda: self.app.show('interactions', kind='messages'), 'nav').pack(anchor='w')
        t.label(self.area, item['name'], size=22, bold=True).pack(anchor='w', pady=12)
        self.panel = MessagePanel(self.area, self.app, item)
        self.panel.pack(fill='x', pady=8)
        self.panel.start()

    def render(self):
        self.clear()
        if self.kind == 'intentions':
            top = ttk.Frame(self.area)
            top.pack(fill='x', pady=(0, 18))
            uid = self.app.gateway.user_id()
            for value, title, key in [('sent', '我发出的', 'user_id'), ('received', '我收到的', 'seller_id')]:
                count = sum(r[key] == uid for r in self.records)
                t.button(top, f'{title}  {count}', lambda d=value: self.change_direction(d),
                         'selected' if self.direction == value else 'nav').pack(side='left', padx=(0, 8))
            t.label(self.area, '购买意向仅表示兴趣，不会扣款、预订或将商品标为已售。',
                    size=11, color=t.MUTED).pack(anchor='w', pady=(0, 16))
            key = 'user_id' if self.direction == 'sent' else 'seller_id'
            records = [r for r in self.records if r[key] == uid]
        else:
            records = self.records
        if not records:
            messages = {'favorites': ('把喜欢的好物留在这里', '浏览商品时点「收藏」，下次就能快速找到。'),
                        'messages': ('还没有与你相关的留言', '你发布的商品留言，以及你参与过的商品讨论，会展示在这里。'),
                        'intentions': ('还没有购买意向', '看到心仪商品，可以在详情页向卖家表达兴趣。'),
                        'logs': ('还没有操作记录', '这里仅显示你自己的操作，不记录密码和留言正文。')}
            title, detail = messages[self.kind]
            empty_state(self.area, title, detail, lambda: self.app.show('home'), '去逛校园  →')
            return
        if self.kind == 'logs':
            t.label(self.area, '仅你自己的操作 · 最新记录在前', color=t.MUTED).pack(anchor='w', pady=(0, 14))
            for record in records:
                row = ttk.Frame(self.area, padding=(18, 14), relief='solid', borderwidth=1)
                row.pack(fill='x', pady=(0, 10))
                t.label(row, record['action_type'], bold=True).pack(side='left')
                t.label(row, record.get('detail', ''), color=t.MUTED, wraplength=450).pack(side='left', padx=20)
                t.label(row, record.get('timestamp', ''), size=10, color=t.MUTED).pack(side='right')
            return
        t.label(self.area, f'共 {len(records)} 条', color=t.MUTED).pack(anchor='w', pady=(0, 12))
        for record in records:
            item = record if self.kind == 'favorites' else record['item']
            row = ttk.Frame(self.area, padding=16, relief='solid', borderwidth=1)
            row.pack(fill='x', pady=(0, 14))
            ItemImage(row, item.get('image_path', ''), width=100, height=88).pack(side='left', padx=(0, 18))
            info = ttk.Frame(row)
            info.pack(side='left', fill='x', expand=True)
            t.label(info, item['name'], bold=True, size=15, wraplength=400).pack(anchor='w')
            price = f"¥ {item['price']:.2f}  ·  " if item.get('price') is not None else ''
            t.label(info, price+item['status'], color=t.BLUE if item['status'] == '在售' else t.MUTED).pack(anchor='w', pady=6)
            actions = ttk.Frame(row)
            actions.pack(side='right')
            if self.kind == 'favorites':
                if item['status'] == '在售' or item['seller_id'] == self.app.gateway.user_id() and item['status'] != '已删除':
                    t.button(actions, '查看商品  →', lambda i=item['id']: self.app.show('detail', item_id=i), 'primary').pack(fill='x')
                t.button(actions, '取消收藏', lambda i=item['id']: self.unfavorite(i), 'nav').pack(fill='x', pady=(6, 0))
            elif self.kind == 'messages':
                last = record['messages'][-1]
                t.label(info, last['nickname']+'：'+last['content'][:55], wraplength=480, color=t.MUTED, justify='left').pack(anchor='w')
                t.label(info, f"{len(record['messages'])} 条留言 · {last['created_at']}", size=10, color=t.MUTED).pack(anchor='w', pady=(5, 0))
                t.button(actions, '查看留言  →', lambda i=item['id']: self.app.show('interactions', kind='messages', item_id=i), 'primary').pack()
            else:
                who = '卖家：'+record['seller'] if self.direction == 'sent' else '买家：'+record['buyer']
                status = '已提交 · 待沟通' if record['status'] == 'pending' else record['status']
                t.label(info, who+'   /   '+status, color=t.MUTED).pack(anchor='w')
                t.label(info, record['created_at'], size=10, color=t.MUTED).pack(anchor='w', pady=(5, 0))
                t.button(actions, '查看商品留言', lambda i=item['id']: self.app.show('interactions', kind='messages', item_id=i)).pack()

    def change_direction(self, direction):
        if not self.app.busy:
            self.direction = direction
            self.render()

    def unfavorite(self, item_id):
        self.app.run_task(lambda: self.app.gateway.features.toggle_favorite(item_id), lambda _: self.start())
