"""
Display Module
Manages the GUI display using Tkinter
"""
import tkinter as tk
from tkinter import ttk, font as tkfont
from datetime import datetime
from typing import List
import logging
from event_fetcher import Event


class DisplayManager:
    """Manages the GUI display for events"""
    
    def __init__(self, config: dict, secrets: dict = None):
        self.full_config = config  # Store full config
        self.secrets = secrets or {}  # Store secrets
        self.config = config['display']
        self.logger = logging.getLogger(__name__)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(self.config['window_title'])
        self.root.geometry(f"{self.config['width']}x{self.config['height']}")
        
        if self.config.get('fullscreen', False):
            self.root.attributes('-fullscreen', True)
            self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        
        # Configure colors
        self.bg_color = "#1a1a2e"
        self.fg_color = "#eaeaea"
        self.accent_color = "#16213e"
        self.highlight_color = "#0f3460"
        self.alarm_color = "#e94560"
        
        self.root.configure(bg=self.bg_color)
        
        # State - initialize before UI setup
        self.events = []
        self.is_alarm_active = False
        
        # News state
        self.news_items = []
        self.current_page = 0
        self.items_per_page = 5
        self.current_item_in_page = 0
        self.auto_read_active = False
        self.auto_read_on_tab_switch = True
        self._pending_auto_advance = False
        self._pending_speaking_text = None
        self._pending_hide_speaking = False
        
        # Config state
        self.config_entries = {}  # Store entry widgets for config
        self.on_save_config_callback = None
        
        # Setup UI
        self._setup_ui()
        
        # Start checking for pending auto-advance and speaking text
        self.root.after(100, self._check_pending_updates)
        
    def _setup_ui(self):
        """Setup the UI components"""
        # Header Frame
        header_frame = tk.Frame(self.root, bg=self.accent_color, height=80)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title
        title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
        self.title_label = tk.Label(
            header_frame,
            text="🤖 AI Reminder System",
            font=title_font,
            bg=self.accent_color,
            fg=self.fg_color
        )
        self.title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Clock
        clock_font = tkfont.Font(family="Helvetica", size=18)
        self.clock_label = tk.Label(
            header_frame,
            text="",
            font=clock_font,
            bg=self.accent_color,
            fg=self.fg_color
        )
        self.clock_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Status Frame
        status_frame = tk.Frame(self.root, bg=self.bg_color)
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        status_font = tkfont.Font(family="Helvetica", size=12)
        self.status_label = tk.Label(
            status_frame,
            text="🟢 System Ready",
            font=status_font,
            bg=self.bg_color,
            fg="#4ecca3"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Stop Alarm Button (initially hidden)
        button_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.stop_button = tk.Button(
            status_frame,
            text="🛑 STOP ALARM",
            font=button_font,
            bg=self.alarm_color,
            fg=self.fg_color,
            activebackground="#c0392b",
            activeforeground=self.fg_color,
            relief=tk.RAISED,
            bd=3,
            padx=20,
            pady=5,
            cursor="hand2",
            command=self._on_stop_button_click
        )
        # Button is hidden by default
        self.on_stop_alarm_callback = None
        
        # Speaking Text Frame (for displaying current voice output)
        self.speaking_frame = tk.Frame(self.root, bg=self.highlight_color, relief=tk.RAISED, bd=2)
        self.speaking_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.speaking_frame.pack_forget()  # Hidden by default
        
        speaking_title_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        speaking_title = tk.Label(
            self.speaking_frame,
            text="🔊 Speaking:",
            font=speaking_title_font,
            bg=self.highlight_color,
            fg="#4ecca3"
        )
        speaking_title.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        speaking_text_font = tkfont.Font(family="Helvetica", size=12)
        self.speaking_label = tk.Label(
            self.speaking_frame,
            text="",
            font=speaking_text_font,
            bg=self.highlight_color,
            fg=self.fg_color,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=self.config['width'] - 60
        )
        self.speaking_label.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Main Content Area with Tabs
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create notebook (tabbed interface)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=self.accent_color, 
                       foreground=self.fg_color,
                       padding=[20, 10],
                       font=('Helvetica', 11, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.highlight_color)],
                 foreground=[('selected', '#4ecca3')])
        
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Events Tab
        events_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(events_tab, text="📅 Events")
        
        # Scrollable canvas for events
        canvas = tk.Canvas(events_tab, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(events_tab, orient="vertical", command=canvas.yview)
        
        self.scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # News Tab
        self._setup_news_tab()
        
        # Config Tab
        self._setup_config_tab()
        
        # Update clock
        self._update_clock()
        
        # Auto-refresh event statuses
        self._auto_refresh_events()
    
    def _setup_news_tab(self):
        """Setup the news tab"""
        news_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(news_tab, text="📰 News")
        
        # Control Frame
        control_frame = tk.Frame(news_tab, bg=self.accent_color, height=60)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        control_frame.pack_propagate(False)
        
        button_font = tkfont.Font(family="Helvetica", size=11, weight="bold")
        
        # Fetch News Button
        self.fetch_news_button = tk.Button(
            control_frame,
            text="🔄 Fetch News",
            font=button_font,
            bg="#4ecca3",
            fg=self.bg_color,
            activebackground="#3dbb90",
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self._on_fetch_news_click
        )
        self.fetch_news_button.pack(side=tk.LEFT, padx=20, pady=10)
        
        # News counter label
        self.news_counter_label = tk.Label(
            control_frame,
            text="No news loaded",
            font=tkfont.Font(family="Helvetica", size=11),
            bg=self.accent_color,
            fg=self.fg_color
        )
        self.news_counter_label.pack(side=tk.LEFT, padx=10)
        
        # Page navigation label (right side)
        self.page_label = tk.Label(
            control_frame,
            text="Page 0/0",
            font=tkfont.Font(family="Helvetica", size=11, weight="bold"),
            bg=self.accent_color,
            fg=self.fg_color
        )
        self.page_label.pack(side=tk.RIGHT, padx=20)
        
        # News display area - scrollable frame for list of news
        news_canvas = tk.Canvas(news_tab, bg=self.bg_color, highlightthickness=0)
        news_scrollbar = ttk.Scrollbar(news_tab, orient="vertical", command=news_canvas.yview)
        
        self.news_scrollable_frame = tk.Frame(news_canvas, bg=self.bg_color)
        self.news_scrollable_frame.bind(
            "<Configure>",
            lambda e: news_canvas.configure(scrollregion=news_canvas.bbox("all"))
        )
        
        news_canvas.create_window((0, 0), window=self.news_scrollable_frame, anchor="nw")
        news_canvas.configure(yscrollcommand=news_scrollbar.set)
        
        news_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        news_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize callbacks
        self.on_fetch_news_callback = None
        self.on_read_news_callback = None
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def _setup_config_tab(self):
        """Setup the configuration tab"""
        config_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(config_tab, text="⚙️ Config")
        
        # Control Frame
        control_frame = tk.Frame(config_tab, bg=self.accent_color, height=60)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        control_frame.pack_propagate(False)
        
        button_font = tkfont.Font(family="Helvetica", size=11, weight="bold")
        
        # Save Config Button
        self.save_config_button = tk.Button(
            control_frame,
            text="💾 Save Configuration",
            font=button_font,
            bg="#4ecca3",
            fg=self.bg_color,
            activebackground="#3dbb90",
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self._on_save_config_click
        )
        self.save_config_button.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Status label for save feedback
        self.config_status_label = tk.Label(
            control_frame,
            text="",
            font=tkfont.Font(family="Helvetica", size=11),
            bg=self.accent_color,
            fg="#4ecca3"
        )
        self.config_status_label.pack(side=tk.LEFT, padx=10)
        
        # Scrollable config area
        config_canvas = tk.Canvas(config_tab, bg=self.bg_color, highlightthickness=0)
        config_scrollbar = ttk.Scrollbar(config_tab, orient="vertical", command=config_canvas.yview)
        
        self.config_scrollable_frame = tk.Frame(config_canvas, bg=self.bg_color)
        self.config_scrollable_frame.bind(
            "<Configure>",
            lambda e: config_canvas.configure(scrollregion=config_canvas.bbox("all"))
        )
        
        config_canvas.create_window((0, 0), window=self.config_scrollable_frame, anchor="nw")
        config_canvas.configure(yscrollcommand=config_scrollbar.set)
        
        config_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Build config form
        self._build_config_form()
        
    def _build_config_form(self):
        """Build the configuration form"""
        form_font = tkfont.Font(family="Helvetica", size=10)
        label_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        section_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        
        # API Keys Section
        self._add_section_header("🔑 API Keys", section_font)
        self._add_config_field("OpenAI API Key", "openai_api_key", 
                              self.secrets.get('openai_api_key', ''),
                              label_font, form_font, is_secret=True)
        self._add_config_field("Gemini API Key", "gemini_api_key",
                              self.secrets.get('gemini_api_key', ''),
                              label_font, form_font, is_secret=True)
        
        self._add_spacer()
        
        # TTS Configuration Section
        self._add_section_header("🔊 Text-to-Speech", section_font)
        tts_config = self.full_config.get('tts', {})
        self._add_config_field("Speech Rate (100-200)", "tts.rate",
                              str(tts_config.get('rate', 140)),
                              label_font, form_font)
        self._add_config_field("Volume (0.0-1.0)", "tts.volume",
                              str(tts_config.get('volume', 0.9)),
                              label_font, form_font)
        self._add_config_field("English Voice Name", "tts.voice_name",
                              tts_config.get('voice_name', 'Microsoft Zira Desktop'),
                              label_font, form_font)
        self._add_config_field("Chinese Voice Name", "tts.chinese_voice_name",
                              tts_config.get('chinese_voice_name', 'Microsoft Huihui Desktop'),
                              label_font, form_font)
        
        self._add_spacer()
        
        # Alarm Configuration Section
        self._add_section_header("⏰ Alarm Settings", section_font)
        alarm_config = self.full_config.get('alarm', {})
        self._add_config_field("Voice Reminder Interval (seconds)", "alarm.voice_reminder_interval",
                              str(alarm_config.get('voice_reminder_interval', 10)),
                              label_font, form_font)
        self._add_config_field("Auto Stop After (seconds)", "alarm.auto_stop_after",
                              str(alarm_config.get('auto_stop_after', 1800)),
                              label_font, form_font)
        
        self._add_spacer()
        
        # Chatbot Configuration Section
        self._add_section_header("🤖 Chatbot", section_font)
        chatbot_config = self.full_config.get('chatbot', {})
        self._add_config_field("Provider (openai/gemini)", "chatbot.provider",
                              chatbot_config.get('provider', 'openai'),
                              label_font, form_font)
        
        openai_config = chatbot_config.get('openai', {})
        self._add_config_field("OpenAI Model", "chatbot.openai.model",
                              openai_config.get('model', 'gpt-3.5-turbo'),
                              label_font, form_font)
        
        gemini_config = chatbot_config.get('gemini', {})
        self._add_config_field("Gemini Model", "chatbot.gemini.model",
                              gemini_config.get('model', 'gemini-pro'),
                              label_font, form_font)
        
        self._add_spacer()
        
        # News Configuration Section
        self._add_section_header("📰 News Feeds", section_font)
        news_config = self.full_config.get('news', {})
        self._add_config_field("Max Items Per Feed", "news.max_items_per_feed",
                              str(news_config.get('max_items_per_feed', 5)),
                              label_font, form_font)
        
        # All available news feeds (predefined list)
        all_feeds = {
            "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
            "CNN": "http://rss.cnn.com/rss/edition.rss",
            "Reuters": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            "TechCrunch": "https://techcrunch.com/feed/",
            "The Guardian": "https://www.theguardian.com/world/rss",
            "China Daily": "http://www.chinadaily.com.cn/rss/world_rss.xml",
            "Xinhua English": "http://www.news.cn/english/rss/englishrssnew.xml",
            "CGTN": "https://www.cgtn.com/rss/news.xml",
            "South China Morning Post": "https://www.scmp.com/rss/91/feed",
            "中新网即时新闻": "https://www.chinanews.com.cn/rss/scroll-news.xml"
        }
        
        # Current active feeds from config
        active_feeds = news_config.get('feeds', {})
        
        # Add checkboxes for each feed
        self._add_news_feed_checkboxes(all_feeds, active_feeds, label_font)
        
        # Add custom feed input
        self._add_custom_feed_input(active_feeds, all_feeds, label_font, form_font)
        
    def _add_news_feed_checkboxes(self, all_feeds, active_feeds, label_font):
        """Add checkboxes for news feeds"""
        self.feed_checkboxes = {}
        
        feeds_label = tk.Label(
            self.config_scrollable_frame,
            text="Select News Sources:",
            font=label_font,
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        feeds_label.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Create frame for checkboxes
        checkbox_frame = tk.Frame(self.config_scrollable_frame, bg=self.bg_color)
        checkbox_frame.pack(fill=tk.X, padx=20, pady=5)
        
        for feed_name, feed_url in all_feeds.items():
            var = tk.BooleanVar(value=feed_name in active_feeds)
            
            cb = tk.Checkbutton(
                checkbox_frame,
                text=feed_name,
                variable=var,
                bg=self.bg_color,
                fg=self.fg_color,
                selectcolor=self.accent_color,
                activebackground=self.bg_color,
                activeforeground=self.fg_color,
                font=tkfont.Font(family="Helvetica", size=10),
                anchor=tk.W
            )
            cb.pack(anchor=tk.W, pady=2)
            
            self.feed_checkboxes[feed_name] = {
                'var': var,
                'url': feed_url
            }
    
    def _add_custom_feed_input(self, active_feeds, all_feeds, label_font, form_font):
        """Add input fields for custom news feeds"""
        custom_label = tk.Label(
            self.config_scrollable_frame,
            text="Add Custom Feed:",
            font=label_font,
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        custom_label.pack(fill=tk.X, padx=10, pady=(15, 5))
        
        # Custom feed container
        custom_frame = tk.Frame(self.config_scrollable_frame, bg=self.accent_color, relief=tk.RAISED, bd=2)
        custom_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Feed name input
        name_row = tk.Frame(custom_frame, bg=self.accent_color)
        name_row.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        name_label = tk.Label(
            name_row,
            text="Feed Name:",
            font=form_font,
            bg=self.accent_color,
            fg=self.fg_color,
            width=15,
            anchor=tk.W
        )
        name_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.custom_feed_name = tk.Entry(
            name_row,
            font=form_font,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT
        )
        self.custom_feed_name.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        
        # Feed URL input
        url_row = tk.Frame(custom_frame, bg=self.accent_color)
        url_row.pack(fill=tk.X, padx=10, pady=(5, 5))
        
        url_label = tk.Label(
            url_row,
            text="Feed URL:",
            font=form_font,
            bg=self.accent_color,
            fg=self.fg_color,
            width=15,
            anchor=tk.W
        )
        url_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.custom_feed_url = tk.Entry(
            url_row,
            font=form_font,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT
        )
        self.custom_feed_url.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        
        # Add button
        add_button = tk.Button(
            custom_frame,
            text="➕ Add Feed",
            font=tkfont.Font(family="Helvetica", size=10, weight="bold"),
            bg="#4ecca3",
            fg=self.bg_color,
            activebackground="#3dbb90",
            relief=tk.RAISED,
            bd=2,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._on_add_custom_feed
        )
        add_button.pack(pady=(5, 10))
        
        # List of custom feeds
        self.custom_feeds_listbox_frame = tk.Frame(self.config_scrollable_frame, bg=self.bg_color)
        self.custom_feeds_listbox_frame.pack(fill=tk.X, padx=20, pady=(5, 10))
        
        # Store custom feeds added during session
        self.custom_feeds_list = []
        self._load_custom_feeds(active_feeds, all_feeds)
    
    def _load_custom_feeds(self, active_feeds, predefined_feeds):
        """Load custom feeds that are not in the predefined list"""
        for feed_name, feed_url in active_feeds.items():
            if feed_name not in predefined_feeds:
                self._add_custom_feed_to_list(feed_name, feed_url)
    
    def _on_add_custom_feed(self):
        """Handle adding a custom feed"""
        name = self.custom_feed_name.get().strip()
        url = self.custom_feed_url.get().strip()
        
        if name and url:
            self._add_custom_feed_to_list(name, url)
            
            # Clear inputs
            self.custom_feed_name.delete(0, tk.END)
            self.custom_feed_url.delete(0, tk.END)
        else:
            # Show error message briefly
            self.config_status_label.config(text="⚠️ Please enter both name and URL", fg="#e94560")
            self.root.after(3000, lambda: self.config_status_label.config(text=""))
    
    def _add_custom_feed_to_list(self, name, url):
        """Add a custom feed to the display list"""
        feed_frame = tk.Frame(self.custom_feeds_listbox_frame, bg=self.accent_color, relief=tk.RAISED, bd=1)
        feed_frame.pack(fill=tk.X, pady=2)
        
        var = tk.BooleanVar(value=True)
        
        cb = tk.Checkbutton(
            feed_frame,
            text=f"{name}",
            variable=var,
            bg=self.accent_color,
            fg=self.fg_color,
            selectcolor=self.bg_color,
            activebackground=self.accent_color,
            activeforeground=self.fg_color,
            font=tkfont.Font(family="Helvetica", size=9),
            anchor=tk.W
        )
        cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        
        # Delete button
        del_btn = tk.Button(
            feed_frame,
            text="🗑️",
            bg=self.alarm_color,
            fg=self.fg_color,
            relief=tk.FLAT,
            bd=0,
            padx=5,
            cursor="hand2",
            command=lambda: self._remove_custom_feed(feed_frame, name)
        )
        del_btn.pack(side=tk.RIGHT, padx=5, pady=2)
        
        self.custom_feeds_list.append({
            'name': name,
            'url': url,
            'var': var,
            'frame': feed_frame
        })
    
    def _remove_custom_feed(self, frame, name):
        """Remove a custom feed from the list"""
        frame.destroy()
        self.custom_feeds_list = [f for f in self.custom_feeds_list if f['name'] != name]
        
    def _add_section_header(self, text, font):
        """Add a section header"""
        header = tk.Label(
            self.config_scrollable_frame,
            text=text,
            font=font,
            bg=self.bg_color,
            fg="#4ecca3",
            anchor=tk.W
        )
        header.pack(fill=tk.X, padx=10, pady=(15, 5))
        
        separator = tk.Frame(self.config_scrollable_frame, bg=self.highlight_color, height=2)
        separator.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    def _add_config_field(self, label_text, config_key, value, label_font, entry_font, is_secret=False):
        """Add a configuration field"""
        row_frame = tk.Frame(self.config_scrollable_frame, bg=self.bg_color)
        row_frame.pack(fill=tk.X, padx=10, pady=5)
        
        label = tk.Label(
            row_frame,
            text=label_text + ":",
            font=label_font,
            bg=self.bg_color,
            fg=self.fg_color,
            width=30,
            anchor=tk.W
        )
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        entry = tk.Entry(
            row_frame,
            font=entry_font,
            bg=self.accent_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            show="*" if is_secret else None
        )
        entry.insert(0, value)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        
        self.config_entries[config_key] = entry
    
    def _add_info_text(self, label_text, info_text, label_font, text_font):
        """Add an informational text area"""
        row_frame = tk.Frame(self.config_scrollable_frame, bg=self.bg_color)
        row_frame.pack(fill=tk.X, padx=10, pady=5)
        
        label = tk.Label(
            row_frame,
            text=label_text + ":",
            font=label_font,
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.NW
        )
        label.pack(anchor=tk.W, padx=(0, 10), pady=(0, 5))
        
        text_widget = tk.Text(
            row_frame,
            font=text_font,
            bg=self.accent_color,
            fg=self.fg_color,
            height=6,
            wrap=tk.WORD,
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        text_widget.pack(fill=tk.X, expand=True)
        
        # Enable, insert text, then disable again
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(1.0, info_text)
        text_widget.config(state=tk.DISABLED)
    
    def _add_spacer(self):
        """Add a spacer between sections"""
        spacer = tk.Frame(self.config_scrollable_frame, bg=self.bg_color, height=10)
        spacer.pack(fill=tk.X)
    
    def _on_save_config_click(self):
        """Handle save config button click"""
        if self.on_save_config_callback:
            # Collect values from entries
            config_values = {}
            for key, entry in self.config_entries.items():
                config_values[key] = entry.get()
            
            # Collect selected news feeds
            news_feeds = {}
            
            # Add predefined feeds that are checked
            for feed_name, feed_data in self.feed_checkboxes.items():
                if feed_data['var'].get():
                    news_feeds[feed_name] = feed_data['url']
            
            # Add custom feeds that are checked
            for custom_feed in self.custom_feeds_list:
                if custom_feed['var'].get():
                    news_feeds[custom_feed['name']] = custom_feed['url']
            
            config_values['news.feeds'] = news_feeds
            
            self.on_save_config_callback(config_values)
            self.config_status_label.config(text="✅ Configuration saved!", fg="#4ecca3")
            # Clear status after 3 seconds
            self.root.after(3000, lambda: self.config_status_label.config(text=""))
        
    def set_config_callback(self, callback):
        """Set callback for config save"""
        self.on_save_config_callback = callback
        
    def _auto_refresh_events(self):
        """Auto-refresh events display to update statuses"""
        if self.events:
            self._refresh_events_display()
        # Refresh every 30 seconds
        self.root.after(30000, self._auto_refresh_events)
        
    def _update_clock(self):
        """Update the clock display"""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %B %d, %Y")
        self.clock_label.config(text=f"{time_str}\n{date_str}")
        self.root.after(1000, self._update_clock)
        
    def update_events(self, events: List[Event]):
        """Update the events display"""
        self.events = events
        self._refresh_events_display()
        
    def _refresh_events_display(self):
        """Refresh the events list on screen"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.events:
            no_events_label = tk.Label(
                self.scrollable_frame,
                text="📭 No events scheduled for today",
                font=tkfont.Font(family="Helvetica", size=16),
                bg=self.bg_color,
                fg=self.fg_color,
                pady=50
            )
            no_events_label.pack()
            return
        
        # Sort events by time
        sorted_events = sorted(self.events, key=lambda e: e.event_time)
        
        for event in sorted_events:
            self._create_event_widget(event)
    
    def _create_event_widget(self, event: Event):
        """Create a widget for a single event"""
        now = datetime.now()
        time_diff = (event.event_time - now).total_seconds()
        
        # Determine event status
        # In Progress: within 60 minutes after event time
        is_in_progress = -3600 <= time_diff <= 0  # 0 to -60 minutes
        # Expired/Completed: more than 60 minutes past
        is_expired = time_diff < -3600
        # Upcoming Soon: within 5 minutes before
        is_soon = 0 < time_diff <= 300
        # Future: more than 5 minutes away
        is_future = time_diff > 300
        
        # Determine status text and emoji
        if event.triggered:
            status_text = "COMPLETED"
            status_emoji = "✓"
            status_color = "#4ecca3"
        elif is_in_progress:
            status_text = "IN PROGRESS"
            status_emoji = "▶"
            status_color = "#f39c12"
        elif is_expired:
            status_text = "EXPIRED"
            status_emoji = "✗"
            status_color = "#666666"
        elif is_soon:
            status_text = "STARTING SOON"
            status_emoji = "🔔"
            status_color = self.alarm_color
        else:
            status_text = "UPCOMING"
            status_emoji = "📅"
            status_color = "#3498db"
        
        # Choose colors based on status
        if event.triggered or is_expired:
            bg = self.bg_color
            fg = "#666666"
            border_color = "#444444"
        elif is_in_progress:
            bg = "#f39c12"
            fg = self.fg_color
            border_color = "#f39c12"
        elif is_soon:
            bg = self.highlight_color
            fg = self.fg_color
            border_color = self.alarm_color
        else:
            bg = self.accent_color
            fg = self.fg_color
            border_color = self.accent_color
        
        # Event frame
        event_frame = tk.Frame(
            self.scrollable_frame,
            bg=border_color,
            padx=2,
            pady=2
        )
        event_frame.pack(fill=tk.X, pady=5)
        
        inner_frame = tk.Frame(event_frame, bg=bg, padx=15, pady=10)
        inner_frame.pack(fill=tk.BOTH)
        
        # Time
        time_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        time_label = tk.Label(
            inner_frame,
            text=event.event_time.strftime("%H:%M"),
            font=time_font,
            bg=bg,
            fg=fg
        )
        time_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Event details
        details_frame = tk.Frame(inner_frame, bg=bg)
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        title_font = tkfont.Font(family="Helvetica", size=14, weight="bold")
        title_label = tk.Label(
            details_frame,
            text=f"{status_emoji} {event.title}",
            font=title_font,
            bg=bg,
            fg=fg,
            anchor="w"
        )
        title_label.pack(fill=tk.X)
        
        # Status badge
        status_font = tkfont.Font(family="Helvetica", size=9, weight="bold")
        status_label = tk.Label(
            details_frame,
            text=f"● {status_text}",
            font=status_font,
            bg=bg,
            fg=status_color,
            anchor="w"
        )
        status_label.pack(fill=tk.X)
        
        if event.description:
            desc_font = tkfont.Font(family="Helvetica", size=11)
            desc_label = tk.Label(
                details_frame,
                text=event.description,
                font=desc_font,
                bg=bg,
                fg=fg,
                anchor="w",
                wraplength=500
            )
            desc_label.pack(fill=tk.X)
    
    def show_alarm(self, event: Event):
        """Show alarm notification"""
        self.is_alarm_active = True
        self.status_label.config(
            text=f"🔔 ALARM: {event.title}",
            fg=self.alarm_color
        )
        # Show stop button
        self.stop_button.pack(side=tk.RIGHT, padx=20)
        self._refresh_events_display()
        
    def clear_alarm(self):
        """Clear alarm notification"""
        self.is_alarm_active = False
        self.status_label.config(
            text="🟢 System Ready",
            fg="#4ecca3"
        )
        # Hide stop button
        self.stop_button.pack_forget()
        self._refresh_events_display()
    
    def _on_stop_button_click(self):
        """Handle stop button click"""
        self.logger.info("Stop button clicked on HMI")
        if self.on_stop_alarm_callback:
            self.on_stop_alarm_callback()
    
    def set_stop_alarm_callback(self, callback):
        """Set callback for stop alarm button"""
        self.on_stop_alarm_callback = callback
        
    def update_status(self, message: str, color: str = "#4ecca3"):
        """Update status message"""
        self.status_label.config(text=message, fg=color)
    
    def show_speaking_text(self, text: str):
        """Show text that is being spoken (thread-safe)"""
        self._pending_speaking_text = text
    
    def hide_speaking_text(self):
        """Hide speaking text display (thread-safe)"""
        self._pending_hide_speaking = True
    
    # News Tab Methods
    def set_news_callbacks(self, fetch_callback, read_callback):
        """Set callbacks for news functions"""
        self.on_fetch_news_callback = fetch_callback
        self.on_read_news_callback = read_callback
    
    def _on_fetch_news_click(self):
        """Handle fetch news button click"""
        self.logger.info("Fetch news button clicked")
        if self.on_fetch_news_callback:
            self.on_fetch_news_callback()
    

    
    def update_news(self, news_items):
        """Update news items and display first page"""
        self.news_items = news_items
        self.current_page = 0
        self.current_item_in_page = 0
        
        if news_items:
            total_pages = (len(news_items) + self.items_per_page - 1) // self.items_per_page
            self.news_counter_label.config(text=f"Loaded {len(news_items)} news items")
            self.page_label.config(text=f"Page {self.current_page + 1}/{total_pages}")
            self._display_current_page()
        else:
            self.news_counter_label.config(text="No news loaded")
            self.page_label.config(text="Page 0/0")
            # Clear display
            for widget in self.news_scrollable_frame.winfo_children():
                widget.destroy()
    
    def _display_current_page(self):
        """Display 5 news items for current page"""
        # Clear previous content
        for widget in self.news_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.news_items:
            no_news_label = tk.Label(
                self.news_scrollable_frame,
                text="No news items found. Click 'Fetch News' to load.",
                font=tkfont.Font(family="Helvetica", size=12),
                bg=self.bg_color,
                fg=self.fg_color,
                padx=20,
                pady=20
            )
            no_news_label.pack()
            return
        
        # Calculate which items to show
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.news_items))
        
        # Display items for current page
        for i in range(start_idx, end_idx):
            item = self.news_items[i]
            self._create_news_item_widget(item, i - start_idx)
    
    def _create_news_item_widget(self, item, index_in_page):
        """Create a widget for a single news item"""
        # Item frame with border
        item_frame = tk.Frame(
            self.news_scrollable_frame,
            bg="#0f3460",
            padx=2,
            pady=2
        )
        item_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Inner frame
        inner_frame = tk.Frame(item_frame, bg=self.accent_color, padx=15, pady=15)
        inner_frame.pack(fill=tk.BOTH)
        
        # Number badge
        number_label = tk.Label(
            inner_frame,
            text=f"{index_in_page + 1}",
            font=tkfont.Font(family="Helvetica", size=18, weight="bold"),
            bg="#4ecca3",
            fg=self.bg_color,
            width=3,
            height=2
        )
        number_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Content frame
        content_frame = tk.Frame(inner_frame, bg=self.accent_color)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            content_frame,
            text=item.title,
            font=tkfont.Font(family="Helvetica", size=14, weight="bold"),
            bg=self.accent_color,
            fg=self.fg_color,
            anchor="w",
            justify=tk.LEFT,
            wraplength=600
        )
        title_label.pack(fill=tk.X, pady=(0, 10))
        
        # Description
        desc_label = tk.Label(
            content_frame,
            text=item.description,
            font=tkfont.Font(family="Helvetica", size=11),
            bg=self.accent_color,
            fg="#cccccc",
            anchor="w",
            justify=tk.LEFT,
            wraplength=600
        )
        desc_label.pack(fill=tk.X)
    
    def _on_tab_changed(self, event):
        """Handle tab change event"""
        current_tab = self.notebook.index(self.notebook.select())
        
        # If switched to News tab (index 1) and has news items, start auto-read
        if current_tab == 1:  # News tab
            if not self.news_items and self.on_fetch_news_callback:
                # Auto-fetch news when switching to News tab for first time
                self.on_fetch_news_callback()
            elif self.news_items and self.auto_read_on_tab_switch and not self.auto_read_active:
                # Start auto-reading if news already loaded
                self.start_auto_read()
    
    def start_auto_read(self):
        """Start automatically reading news page by page"""
        if not self.news_items or self.auto_read_active:
            return
        
        self.auto_read_active = True
        self.current_page = 0
        self.current_item_in_page = 0
        self._display_current_page()
        self._read_current_item_auto()
    
    def stop_auto_read(self):
        """Stop auto-reading"""
        self.auto_read_active = False
    
    def _read_current_item_auto(self):
        """Read current news item with auto-advance"""
        if not self.auto_read_active or not self.news_items:
            self.logger.warning(f"Cannot read: active={self.auto_read_active}, items={len(self.news_items) if self.news_items else 0}")
            return
        
        # Calculate absolute index
        abs_index = self.current_page * self.items_per_page + self.current_item_in_page
        self.logger.info(f"Reading news at absolute index {abs_index} (page {self.current_page}, item {self.current_item_in_page})")
        
        if abs_index < len(self.news_items):
            item = self.news_items[abs_index]
            if self.on_read_news_callback:
                self.on_read_news_callback(item, auto_advance=True)
        else:
            self.logger.error(f"Index {abs_index} out of range (total: {len(self.news_items)})")
    
    def schedule_auto_advance(self):
        """Schedule auto advance from background thread (thread-safe)"""
        # Set a flag that will be checked by the GUI thread
        self._pending_auto_advance = True
        self.logger.info("Set pending auto-advance flag")
    
    def _check_pending_updates(self):
        """Check and process pending updates from background threads (called from GUI thread)"""
        # Check for pending auto-advance
        if hasattr(self, '_pending_auto_advance') and self._pending_auto_advance:
            self._pending_auto_advance = False
            self.logger.info("Processing pending auto-advance")
            self.auto_advance_news()
        
        # Check for pending speaking text updates
        if hasattr(self, '_pending_speaking_text') and self._pending_speaking_text is not None:
            text = self._pending_speaking_text
            self._pending_speaking_text = None
            self.speaking_label.config(text=text)
            self.speaking_frame.pack(fill=tk.X, padx=20, pady=(0, 10), after=self.status_label.master)
        
        # Check for pending hide speaking text
        if hasattr(self, '_pending_hide_speaking') and self._pending_hide_speaking:
            self._pending_hide_speaking = False
            self.speaking_frame.pack_forget()
        
        # Check again after 100ms
        self.root.after(100, self._check_pending_updates)
    
    def auto_advance_news(self):
        """Advance to next news item within page, or next page after all items read"""
        self.logger.info(f"auto_advance_news called: page={self.current_page}, item={self.current_item_in_page}, active={self.auto_read_active}")
        if not self.auto_read_active:
            self.logger.warning("Auto-read not active, stopping")
            return
        
        # Move to next item in current page
        self.current_item_in_page += 1
        self.logger.info(f"Advanced to item {self.current_item_in_page}")
        
        # Calculate how many items on current page
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.news_items))
        items_on_page = end_idx - start_idx
        
        # Check if we finished all items on current page
        if self.current_item_in_page >= items_on_page:
            # Move to next page
            self.current_item_in_page = 0
            self.current_page += 1
            
            total_pages = (len(self.news_items) + self.items_per_page - 1) // self.items_per_page
            
            # Loop back to first page if at end
            if self.current_page >= total_pages:
                self.current_page = 0
                self.update_status("🔄 Looping back to first page", "#4ecca3")
            
            # Update page display
            self._display_current_page()
            self.page_label.config(text=f"Page {self.current_page + 1}/{total_pages}")
        
        # Continue reading
        self._read_current_item_auto()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()
        
    def update(self):
        """Process pending GUI events"""
        self.root.update()
