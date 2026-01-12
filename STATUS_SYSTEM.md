# Event Status System - Quick Reference

## Status Types

The UI now displays events with dynamic statuses that update automatically:

### 📅 UPCOMING (Blue)
- **Condition**: Event is more than 5 minutes away
- **Display**: Blue accent background
- **Icon**: 📅
- **Color**: #3498db

### 🔔 STARTING SOON (Red Alert)
- **Condition**: Event starts within 5 minutes
- **Display**: Red highlighted border, prominent display
- **Icon**: 🔔
- **Color**: #e94560 (alarm red)

### ▶ IN PROGRESS (Orange)
- **Condition**: Event started and within 60 minutes of start time
- **Display**: Orange background, stands out clearly
- **Icon**: ▶ (play symbol)
- **Color**: #f39c12 (orange)
- **Time Window**: From event time to 60 minutes after

### ✓ COMPLETED (Green)
- **Condition**: Event was triggered and marked as done
- **Display**: Green checkmark, grayed out appearance
- **Icon**: ✓
- **Color**: #4ecca3 (success green)

### ✗ EXPIRED (Gray)
- **Condition**: Event is more than 60 minutes past start time
- **Display**: Grayed out, faded appearance
- **Icon**: ✗
- **Color**: #666666 (gray)

## Auto-Refresh

- Statuses automatically update every **30 seconds**
- No manual refresh needed
- Real-time status transitions as time progresses

## Status Transitions

An event flows through these statuses over time:

```
UPCOMING (📅)
    ↓
    [5 minutes before]
    ↓
STARTING SOON (🔔)
    ↓
    [event time arrives]
    ↓
IN PROGRESS (▶)
    ↓
    [60 minutes pass OR manually completed]
    ↓
EXPIRED (✗) or COMPLETED (✓)
```

## Visual Indicators

### Border Colors
- **Blue**: Upcoming events
- **Red**: Starting soon (alert)
- **Orange**: In progress
- **Gray**: Expired/Completed

### Background Colors
- **Dark Accent (#16213e)**: Normal upcoming
- **Highlight Blue (#0f3460)**: Starting soon
- **Orange (#f39c12)**: In progress
- **Dark Background (#1a1a2e)**: Expired/Completed

### Text Colors
- **Light Gray (#eaeaea)**: Active events
- **Dark Gray (#666666)**: Expired/Completed events

## Time Calculations

```python
now = current time
event_time = scheduled event time
time_diff = event_time - now

# Status determination:
if event.triggered:
    status = "COMPLETED"
elif -3600 <= time_diff <= 0:  # 0 to -60 minutes
    status = "IN PROGRESS"
elif time_diff < -3600:  # more than 60 minutes past
    status = "EXPIRED"
elif 0 < time_diff <= 300:  # within 5 minutes before
    status = "STARTING SOON"
else:  # more than 5 minutes away
    status = "UPCOMING"
```

## Testing

Use the test scripts to see all statuses:

```bash
# Basic GUI test
python test_gui.py

# Enhanced test with all status types
python test_gui_enhanced.py
```

## Configuration

Status refresh interval can be adjusted in the code:
- Location: `src/display_manager.py`
- Method: `_auto_refresh_events()`
- Default: 30000ms (30 seconds)

To change refresh rate:
```python
# Change from 30 seconds to 10 seconds
self.root.after(10000, self._auto_refresh_events)
```

## Customization

Colors and time windows can be customized:

### In Progress Duration
Default: 60 minutes (3600 seconds)
```python
# In display_manager.py, _create_event_widget()
is_in_progress = -3600 <= time_diff <= 0  # Change 3600 to desired seconds
```

### Starting Soon Window
Default: 5 minutes (300 seconds)
```python
is_soon = 0 < time_diff <= 300  # Change 300 to desired seconds
```

### Status Colors
Modify in `display_manager.py` `__init__` method:
```python
self.alarm_color = "#e94560"  # Starting soon / alarm
self.accent_color = "#16213e"  # Normal background
# etc.
```
