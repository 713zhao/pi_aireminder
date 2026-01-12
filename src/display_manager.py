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
    
    def __init__(self, config: dict):
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
        
        # Setup UI
        self._setup_ui()
        
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
        
        # Events Frame
        events_frame = tk.Frame(self.root, bg=self.bg_color)
        events_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Scrollable canvas for events
        canvas = tk.Canvas(events_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(events_frame, orient="vertical", command=canvas.yview)
        
        self.scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Update clock
        self._update_clock()
        
        # Auto-refresh event statuses
        self._auto_refresh_events()
        
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
        
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()
        
    def update(self):
        """Process pending GUI events"""
        self.root.update()
