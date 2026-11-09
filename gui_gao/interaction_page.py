"""Favorites, public item discussions, purchase intentions and personal activity."""
import tkinter as tk
from tkinter import ttk
from . import theme as t
from .page_design import PageBanner, note_card, LocalChecklist
from .widgets import ScrollPage, Field, ItemImage, page_title, empty_state

TABS = {'favorites': 'Saved items', 'messages': 'Comments', 'intentions': 'Enquiries', 'logs': 'Activity log'}


class MessagePanel(ttk.Frame):
    def __init__(self, parent, app, item):
        super().__init__(parent, padding=20, relief='solid', borderwidth=1)
        self.app, self.item = app, item
        header = ttk.Frame(self)
        header.pack(fill='x')
        t.label(header, 'Comments', size=19, bold=True).pack(side='left')
        t.button(header, 'Refresh comments', self.start, 'nav').pack(side='right')
        t.label(self, 'Comments are public. Ask about the item and arrange a handover here.',
                color=t.MUTED, size=11, wraplength=740, justify='left').pack(anchor='w', pady=(8, 16))
        self.list = ttk.Frame(self)
        self.list.pack(fill='x')
        self.feedback = t.label(self, '', color=t.RED, wraplength=740, justify='left')
        self.feedback.pack(anchor='w', pady=10)
        self.composer = None
        if item['status'] == 'Available':
            self.composer = Field(self, 'Write a comment', multiline=True, hint='Up to 500 characters. Anyone viewing this item can read your comment.')
            self.composer.input.configure(height=3)
            self.composer.pack(fill='x')
            chips = ttk.Frame(self)
            chips.pack(fill='x', pady=(0, 12))
            for text in ['Are all accessories included?', 'Is there any wear or damage?', 'Where could we meet?']:
                t.button(chips, text+' +', lambda v=text: self.add_prompt(v), 'nav').pack(side='left', padx=(0, 6))
            self.counter = t.label(self, '0 / 500', color=t.MUTED, size=10)
            self.counter.pack(anchor='e', pady=(0, 10))
            self.composer.observe(self.update_count)
            t.button(self, 'Post comment  →', self.send, 'primary').pack(anchor='e')
        else:
            t.label(self, 'This item is no longer available. Previous comments are still visible.', color=t.MUTED).pack(anchor='w')

    def update_count(self):
        length = len(self.composer.get())
        self.counter.configure(text=f'{length} / 500', fg=t.RED if length > 500 else t.MUTED)

    def add_prompt(self, text):
        if not self.composer or self.app.busy:
            return
        current = self.composer.get()
        updated = current + ('\n' if current else '') + text
        if len(updated) > 500:
            self.composer.show_error('Comments are limited to 500 characters. Please shorten your message.')
            return
        self.composer.set(updated)
        self.update_count()
        self.composer.input.focus_set()

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
            t.label(self.list, 'No comments yet. Ask the first question.', color=t.MUTED).pack(anchor='w', pady=12)
        for record in records:
            row = ttk.Frame(self.list, padding=(0, 10))
            row.pack(fill='x')
            who = record['nickname'] + (' · Seller' if record['user_id'] == self.item['seller_id'] else '')
            t.label(row, who, bold=True, color=t.BLUE).pack(anchor='w')
            t.label(row, record['content'], wraplength=710, justify='left', bg=t.PALE, padx=16, pady=12).pack(anchor='w', fill='x', pady=6)
            t.label(row, record['created_at'], size=10, color=t.MUTED).pack(anchor='w')
            ttk.Separator(row).pack(fill='x', pady=(10, 0))

    def send(self):
        if self.app.busy or not self.composer:
            return
        text = self.composer.get().strip()
        if not text or len(text) > 500:
            self.composer.show_error('Enter a comment of 1–500 characters.')
            self.composer.input.focus_set()
            return
        self.composer.show_error('')
        def saved(_):
            self.composer.set('')
            self.start()
            self.app.notify('Comment posted. Check back for a reply.')
        self.app.run_task(lambda: self.app.gateway.features.add_message(self.item['id'], text), saved,
                          lambda message: self.feedback.configure(text=message))


class InteractionPage(ScrollPage):
    def __init__(self, parent, app, kind='favorites', item_id=None):
        super().__init__(parent)
        self.app, self.kind, self.item_id = app, kind, item_id
        self.direction = 'sent'
        self.records = []
        self.only_available = False
        self.log_query = tk.StringVar(master=self, value='')
        self.panel = None
        introductions = {'favorites': ('Save it for later.', 'Keep items you like in one place.'),
            'messages': ('Talk through the details.', 'Open an item to continue its public discussion.'),
            'intentions': ('Let the seller know you are interested.', 'View sent and received enquiries and discuss the handover.'),
            'logs': ('Your recent activity on Campus Market.', 'Only your own activity is shown. Passwords and comment text are not recorded here.')}
        title, subtitle = introductions[kind]
        PageBanner(self.body, app, 'CONNECTIONS / '+TABS[kind], title, subtitle,
                   kind).pack(fill='x', pady=(0,22))
        tabs = ttk.Frame(self.body)
        tabs.pack(fill='x', pady=(0, 22))
        for value, title in TABS.items():
            t.button(tabs, title, lambda k=value: app.show('interactions', kind=k),
                     'selected' if kind == value else 'nav').pack(side='left', padx=(0, 12))
        t.button(tabs, 'Refresh', self.start, 'nav').pack(side='right')
        if kind == 'favorites':
            self.available = tk.BooleanVar(master=self, value=False)
            ttk.Checkbutton(self.body, text='Show available items only', variable=self.available,
                            command=self.filter_favorites).pack(anchor='w', pady=(0, 16))
        if kind == 'logs':
            search = ttk.Frame(self.body)
            search.pack(fill='x', pady=(0, 18))
            t.label(search, 'Search activity', size=11, color=t.MUTED).pack(side='left', padx=(0, 15))
            entry = ttk.Entry(search, textvariable=self.log_query)
            entry.pack(side='left', fill='x', expand=True)
            entry.bind('<KeyRelease>', lambda _: self.render())
        if kind == 'messages':
            note_card(self.body, 'Ask about the details.', 'Discuss condition, accessories and meeting places in each public item thread.').pack(fill='x', pady=(0, 18))
        if kind == 'intentions':
            self.meet_check = LocalChecklist(self.body, 'Before you meet', [
                'Check the condition and accessories', 'Agree on a convenient public meeting place', 'Inspect the item together before handing it over'])
            self.meet_check.pack(fill='x', pady=(0, 20))
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
        empty_state(self.area, 'Could not load ' + TABS[self.kind], message, self.start)

    def loaded(self, records):
        self.records = records
        self.render()

    def thread(self, item):
        self.clear()
        t.button(self.area, '‹ Back to comments', lambda: self.app.show('interactions', kind='messages'), 'nav').pack(anchor='w')
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
            for value, title, key in [('sent', 'Sent', 'user_id'), ('received', 'Received', 'seller_id')]:
                count = sum(r[key] == uid for r in self.records)
                t.button(top, f'{title}  {count}', lambda d=value: self.change_direction(d),
                         'selected' if self.direction == value else 'nav').pack(side='left', padx=(0, 8))
            t.label(self.area, 'An enquiry only expresses interest. It does not charge, reserve or mark the item as sold.',
                    size=11, color=t.MUTED).pack(anchor='w', pady=(0, 16))
            key = 'user_id' if self.direction == 'sent' else 'seller_id'
            records = [r for r in self.records if r[key] == uid]
        else:
            records = self.records
        if self.kind == 'favorites' and self.only_available:
            records = [r for r in records if r['status'] == 'Available']
        if self.kind == 'logs':
            query = self.log_query.get().strip().casefold()
            records = [r for r in records if query in (r['action_type']+' '+r.get('detail', '')).casefold()]
        if not records and ((self.kind == 'favorites' and self.only_available) or (self.kind == 'logs' and self.log_query.get().strip())):
            t.label(self.area, 'No matching records. Try a different filter.', color=t.MUTED).pack(pady=25)
            return
        if not records:
            messages = {'favorites': ('Your saved items go here', 'Save an item while browsing to find it quickly next time.'),
                        'messages': ('No conversations yet', 'Comments on your listings and discussions you have joined will appear here.'),
                        'intentions': ('No enquiries yet', 'Open an item and let the seller know you are interested.'),
                        'logs': ('No activity yet', 'Only your activity appears here, without passwords or comment text.')}
            title, detail = messages[self.kind]
            empty_state(self.area, title, detail, lambda: self.app.show('home'), 'Browse items  →')
            return
        if self.kind == 'logs':
            t.label(self.area, 'Your activity only · Newest first', color=t.MUTED).pack(anchor='w', pady=(0, 14))
            for record in records:
                row = ttk.Frame(self.area, padding=(18, 14), relief='solid', borderwidth=1)
                row.pack(fill='x', pady=(0, 10))
                t.label(row, '●  '+record['action_type'], bold=True, color=t.BLUE).pack(side='left')
                t.label(row, record.get('detail', ''), color=t.MUTED, wraplength=450).pack(side='left', padx=20)
                t.label(row, record.get('timestamp', ''), size=10, color=t.MUTED).pack(side='right')
            return
        t.label(self.area, f'{len(records)} records', color=t.MUTED).pack(anchor='w', pady=(0, 12))
        for record in records:
            item = record if self.kind == 'favorites' else record['item']
            row = ttk.Frame(self.area, padding=16, relief='solid', borderwidth=1)
            row.pack(fill='x', pady=(0, 14))
            ItemImage(row, item.get('image_path', ''), width=100, height=88).pack(side='left', padx=(0, 18))
            info = ttk.Frame(row)
            info.pack(side='left', fill='x', expand=True)
            t.label(info, item['name'], bold=True, size=15, wraplength=400).pack(anchor='w')
            price = f"¥ {item['price']:.2f}  ·  " if item.get('price') is not None else ''
            t.label(info, price+item['status'], color=t.BLUE if item['status'] == 'Available' else t.MUTED).pack(anchor='w', pady=6)
            actions = ttk.Frame(row)
            actions.pack(side='right')
            if self.kind == 'favorites':
                if item['status'] == 'Available' or item['seller_id'] == self.app.gateway.user_id() and item['status'] != 'Deleted':
                    t.button(actions, 'View item  →', lambda i=item['id']: self.app.show('detail', item_id=i), 'primary').pack(fill='x')
                if item['status'] == 'Available':
                    t.button(actions, 'Unsave', lambda i=item['id']: self.unfavorite(i), 'nav').pack(fill='x', pady=(6, 0))
                else:
                    t.label(actions, 'Saved history only', color=t.MUTED, size=10).pack(pady=6)
            elif self.kind == 'messages':
                last = record['messages'][-1]
                t.label(info, last['nickname']+': '+last['content'][:55], wraplength=480, color=t.MUTED, justify='left').pack(anchor='w')
                t.label(info, f"{len(record['messages'])} comments · {last['created_at']}", size=10, color=t.MUTED).pack(anchor='w', pady=(5, 0))
                t.button(actions, 'View comments  →', lambda i=item['id']: self.app.show('interactions', kind='messages', item_id=i), 'primary').pack()
            else:
                who = 'Seller: '+record['seller'] if self.direction == 'sent' else 'Buyer: '+record['buyer']
                status = 'Sent · Awaiting discussion' if record['status'] == 'pending' else record['status']
                t.label(info, who+'   /   '+status, color=t.MUTED).pack(anchor='w')
                t.label(info, record['created_at'], size=10, color=t.MUTED).pack(anchor='w', pady=(5, 0))
                t.button(actions, 'View item comments', lambda i=item['id']: self.app.show('interactions', kind='messages', item_id=i)).pack()

    def filter_favorites(self):
        self.only_available = self.available.get()
        self.render()

    def change_direction(self, direction):
        if not self.app.busy:
            self.direction = direction
            self.render()

    def unfavorite(self, item_id):
        self.app.run_task(lambda: self.app.gateway.features.toggle_favorite(item_id), lambda _: self.start())
