import time
time.sleep(2) # Give the hardware and USB serial a moment to settle
import displayio 
displayio.release_displays() # Release displays to help prevent Errno 5
import board
from digitalio import DigitalInOut, Direction, Pull
import gc
import os
import adafruit_requests
import adafruit_connection_manager
from adafruit_matrixportal.matrix import Matrix
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
import wifi
import supervisor
supervisor.runtime.autoreload = False

from config import config
from api_access import MetroApi
from train_board import TrainBoard
from alert_board import AlertBoard
from bus_board import BusBoard
from utils import report_memory, log_screen, safe_refresh, wrap_text_pixel_perfect, STATIONS_FOR_OUTAGES

gc.collect()

# --- 1. Hardware & Display Setup ---

matrix = Matrix(width=64, height=32, bit_depth=3)
display = matrix.display
display.auto_refresh = False

matrix_group = displayio.Group() # trains/alerts: in super_group
trains_subgroup = displayio.Group() # train arrival data: in matrix_group
alerts_subgroup = displayio.Group() # alerts data: in matrix_group
buses_subgroup = displayio.Group() # bus arrival data: in matrix_group
matrix_group.append(trains_subgroup)
matrix_group.append(alerts_subgroup)
matrix_group.append(buses_subgroup)
indicator_group = displayio.Group() # button press indicators: in super_group
super_group = displayio.Group() # the root container
super_group.append(matrix_group)
super_group.append(indicator_group)
display.root_group = super_group

shared_font = bitmap_font.load_font('metroesque.bdf')

loading_label = Label(
    shared_font, 
    text="Loading...", 
    color=config['text_color'],
    base_alignment=True,
    anchor_point=(0.5, 1),
    anchored_position=(32, 19)
)
matrix_group.append(loading_label)
safe_refresh(display)

gc.collect()

# --- 2. Indicators & Buttons ---

indicator_pixels_color = config.get('indicator_pixels_color', [0x000000])
indicator_bitmap = displayio.Bitmap(64, 1, len(indicator_pixels_color))
indicator_palette = displayio.Palette(len(indicator_pixels_color))
for i, color in enumerate(indicator_pixels_color):
    indicator_palette[i] = color
indicator_tile_grid = displayio.TileGrid(indicator_bitmap, pixel_shader=indicator_palette)
indicator_pixels_subgroup = displayio.Group(x=0, y=31)
indicator_pixels_subgroup.append(indicator_tile_grid)
indicator_group.append(indicator_pixels_subgroup)

def get_pin(pin_id):
    try:
        p = DigitalInOut(pin_id)
        p.direction = Direction.INPUT
        p.pull = Pull.UP
        return p
    except ValueError:
        # If the pin is already in use (common during soft-reboots)
        # some users prefer to deinit, but usually, a clean script start handles it.
        raise RuntimeError(f"Could not initialize pin {pin_id}. Is it already in use?")

pin_up = get_pin(board.BUTTON_UP)
pin_down = get_pin(board.BUTTON_DOWN)

gc.collect()

# --- 3. WiFi Setup ---

radio = wifi.radio
wifi_max_attempts = config.get('wifi_max_attempts', 5)
attempt = 0
connected = False
print("Connecting to wifi...")

while not connected:
    try:
        loading_label.text = f"     Wifi\ntry {attempt+1} of {wifi_max_attempts}"
        loading_label.anchored_position=(32, 23)
        safe_refresh(display)

        radio.connect(os.getenv("WIFI_SSID"), os.getenv("WIFI_PASSWORD"))
            
        connected = True
        loading_label.text = ""

    except Exception as e:
        attempt += 1
        print(f"Attempt {attempt} failed: {e}")
        if attempt >= wifi_max_attempts:
            loading_label.color = config.get('heading_color', 0xFF0000)
            loading_label.text = "Wifi Error"
            safe_refresh(display)
            while True:
                time.sleep(60)
        else:
            time.sleep(2)

pool = adafruit_connection_manager.get_radio_socketpool(radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
requests = adafruit_requests.Session(pool, ssl_context)
print("Connected!")

gc.collect()

# --- 4. State Management ---
api = MetroApi()
train_board = TrainBoard(trains_subgroup, shared_font)
alert_board = AlertBoard(alerts_subgroup, shared_font)
bus_board = BusBoard(buses_subgroup, shared_font, config)
start_secs = time.monotonic() 
current_idx = 0
is_rotating = config.get('start_in_rotating_mode', True)
show_rail_alerts = config.get('rail_alert_display_frequency', 600) >= 0
show_elevator_outages = config.get('elevator_outage_display_frequency', 1200) >= 0
up_was_pressed = down_was_pressed = False
button_up_time = button_down_time = 0
def set_indicator(color_idx):
    for x in range(64): indicator_bitmap[x, 0] = color_idx

def blink_indicator_pixels(color_idx, times, duration):
    for _ in range(times):
        set_indicator(color_idx); safe_refresh(display); time.sleep(duration)
        set_indicator(0); safe_refresh(display); time.sleep(duration)

def check_buttons():
    global up_was_pressed, down_was_pressed, button_up_time, button_down_time
    global is_rotating, show_rail_alerts, show_elevator_outages
    
    now = time.monotonic()
    threshold = config.get('long_press_threshold', 0.5)
    long_blink = config.get('long_blink_time', 0.5)
    short_blink = config.get('short_blink_time', 0.25)

    # --- UP BUTTON: Rotate (Long) / Advance (Short) ---

    if not pin_up.value and not up_was_pressed:
        button_up_time = now
        up_was_pressed = True

    if pin_up.value and up_was_pressed:
        duration = now - button_up_time
        up_was_pressed = False # Reset immediately

        if duration >= threshold:
            # --- LONG PRESS: TOGGLE STATE ---
            is_rotating = not is_rotating
            
            if not is_rotating:
                # Toggled to Stationary: 1 indicator pixels blink using color 1
                print(f"[{time.monotonic() - start_secs:.1f}s] STATE: STATIONARY")
                blink_indicator_pixels(1, 1, long_blink)
            else:
                # Toggled to Rotating: 2 indicator pixels blinks using color 1
                print(f"[{time.monotonic() - start_secs:.1f}s] STATE: ROTATING")
                blink_indicator_pixels(1, 2, short_blink)
            
            return "STATE_CHANGE_ROTATION"
            
        else:
            # --- SHORT PRESS: ADVANCE ---
            # 1 blink using color 2
            print("MANUAL ADVANCE")
            blink_indicator_pixels(2, 1, short_blink)
            return "MOVE_NEXT"

    # --- DOWN BUTTON: Detailed Alerts (Short) / Elevator Outages (Long) ---
    if not pin_down.value and not down_was_pressed:
        button_down_time = now
        down_was_pressed = True
        
    if pin_down.value and down_was_pressed:
        duration = now - button_down_time
        down_was_pressed = False
        
        if duration < threshold:
            # SHORT PRESS: Toggle Elevator Outages (True/False)
            show_elevator_outages = not show_elevator_outages
            new_state = show_elevator_outages
            
            # Visual Feedback: 1 blink for OFF, 2 blinks for ON (color 4)
            blinks = 2 if new_state else 1
            blink_indicator_pixels(4, blinks, long_blink)
            
            state_label = "ON" if new_state else "OFF"
            print(f"[{time.monotonic() - start_secs:.1f}s] ELEVATOR OUTAGES: {state_label}")

            return "JUMP_ELEVATOR_OUTAGES" if new_state else "STATE_CHANGE_ALERTS"

        else:
            # LONG PRESS: Toggle Detailed Rail Alerts (True/False)
            show_rail_alerts = not show_rail_alerts
            new_state = show_rail_alerts

            # Visual Feedback: 1 blink for OFF, 2 blinks for ON (color 3)
            blinks = 2 if new_state else 1
            blink_indicator_pixels(3, blinks, short_blink)

            state_label = "ON" if new_state else "OFF"
            print(f"[{time.monotonic() - start_secs:.1f}s] DETAILED ALERTS: {state_label}")
            return "JUMP_RAIL_ALERTS" if new_state else "STATE_CHANGE_ALERTS"


    return None

gc.collect()
report_memory()

# --- 5. Main Loop ---

pending_items = []
train_cursor = 0
bus_cursor = 0
conductor_phase = 'trains'
active_item = None
need_next_item = True
last_rail_status_display_time = -config.get('rail_status_display_frequency', 60)
last_rail_alert_display_time = -config.get('rail_alert_display_frequency', 60)
last_elevator_outages_display_time = -config.get('elevator_outage_display_frequency', 60)
last_rotation_time = time.monotonic()
loading_label.hidden = True
trains_subgroup.hidden = True
alerts_subgroup.hidden = True
buses_subgroup.hidden = True
safe_refresh(display)
intermission = config.get('metro_api_fetch_intermission', 30)
last_fetch_time_alerts = -100
last_fetch_time_elevators = -100
last_fetch_time_trains = {}
last_fetch_time_buses = {}
rail_alerts = []
elevator_outages = []
train_predictions_cache = {}
bus_predictions_cache = {}

# Terminology: "line" means train line, not a line of pixels or a line of text

while True:
    gc.collect()
    now = time.monotonic()

    # --- 1. THE CONDUCTOR (JIT: determines the next screen when needed) ---
    if need_next_item and not pending_items:
        train_screens = config.get('train_arrival_screens', [])

        # Phase: trains — emit one screen at a time
        if conductor_phase == 'trains':
            while train_cursor < len(train_screens) and not pending_items:
                stat = train_screens[train_cursor]
                train_cursor += 1
                if stat.get('station_code', ''):
                    pending_items.append({
                        'type': 'train',
                        'station_code': stat.get('station_code', 'A01'),
                        'config_details': stat
                    })
            if train_cursor >= len(train_screens) and not pending_items:
                train_cursor = 0
                conductor_phase = 'buses'

        # Phase: buses — fetch and queue bus arrival pages
        if conductor_phase == 'buses':
            bus_screens = config.get('bus_arrival_screens', [])

            while bus_cursor < len(bus_screens) and not pending_items:
                stop_cfg = bus_screens[bus_cursor]
                bus_cursor += 1
                stop_id = stop_cfg.get('stop_id', '')
                if stop_id:
                    filter_lines = stop_cfg.get('lines', [])
                    transit_time = int(stop_cfg.get('transit_time', 0))

                    if (now - last_fetch_time_buses.get(stop_id, -100)) >= intermission:
                        try:
                            raw = api.fetch_bus_predictions(requests, stop_id)
                            bus_predictions_cache[stop_id] = raw
                            last_fetch_time_buses[stop_id] = now
                            print(f"[{time.monotonic() - start_secs:.1f}s] Fresh Fetch: {stop_id}")
                        except Exception as e:
                            print(f"[{time.monotonic() - start_secs:.1f}s] [ERROR] Bus Fetch: {e}")
                            if stop_id not in bus_predictions_cache:
                                bus_predictions_cache[stop_id] = {}
                    raw = bus_predictions_cache.get(stop_id, {})
                    gc.collect()

                    route_pages = []
                    for route_id, rdata in raw.items():
                        if filter_lines and route_id not in filter_lines:
                            continue
                        times = [t for t in rdata['times'] if t >= transit_time]
                        if not times:
                            continue
                        dtxt = rdata['direction_text']
                        _dir = dtxt.split()[0] if dtxt else '??'
                        direction = {'East': 'EB', 'West': 'WB', 'North': 'NB', 'South': 'SB'}.get(_dir, _dir)
                        route_pages.append({
                            'route_id': route_id,
                            'direction': direction,
                            'times': times[:3],
                        })

                    show_header = stop_cfg.get('bus_header', True)
                    display_mode = stop_cfg.get('bus_display_mode', 2)

                    if display_mode == 1:
                        flat = []
                        for r in route_pages:
                            for t in r['times']:
                                flat.append({'route_id': r['route_id'], 'direction': r['direction'], 'time': t})
                        flat.sort(key=lambda x: x['time'])
                        pending_items.append({
                            'type': 'bus', 'display_mode': 1,
                            'show_header': show_header,
                            'config_details': stop_cfg, 'arrivals': flat[:4]
                        })
                    elif show_header:
                        # One route per page, header on every page
                        if route_pages:
                            for r in route_pages:
                                pending_items.append({
                                    'type': 'bus', 'show_header': True,
                                    'config_details': stop_cfg, 'routes': [r]
                                })
                        else:
                            pending_items.append({
                                'type': 'bus', 'show_header': True,
                                'config_details': stop_cfg, 'routes': []
                            })
                    else:
                        # Two routes per page, no header
                        for i in range(0, len(route_pages), 2):
                            pending_items.append({
                                'type': 'bus', 'show_header': False,
                                'config_details': stop_cfg, 'routes': route_pages[i:i+2]
                            })

                    if pending_items:
                        print(f"Queued items: {len(pending_items)}")

            if bus_cursor >= len(bus_screens) and not pending_items:
                bus_cursor = 0
                conductor_phase = 'rail_alerts'

        # Phase: rail_alerts — fetch and queue rail status + detailed alerts
        if conductor_phase == 'rail_alerts':
            status_interval = config.get('rail_status_display_frequency', 120)
            alert_interval = config.get('rail_alert_display_frequency', 600)

            time_since_status = now - last_rail_status_display_time
            time_since_alerts = now - last_rail_alert_display_time

            due_for_status = status_interval >= 0 and (status_interval == 0 or time_since_status >= status_interval)
            due_for_alerts = show_rail_alerts and (alert_interval == 0 or time_since_alerts >= alert_interval)

            if due_for_status or due_for_alerts:
                try:
                    if (now - last_fetch_time_alerts) >= intermission:
                        rail_alerts = api.fetch_rail_alerts(requests) or []
                        last_fetch_time_alerts = now
                        print(f"[{time.monotonic() - start_secs:.1f}s] Fresh Fetch: Rail Alerts")

                    # --- RAIL STATUS ---
                    if due_for_status:
                        all_lines = ["RD", "YL", "GR", "OR", "SV", "BL"]
                        affected_lines = []
                        for inc in rail_alerts:
                            affected = inc.get('LinesAffected', '')
                            for l in all_lines:
                                if l in affected and l not in affected_lines:
                                    affected_lines.append(l)
                        unaffected_lines = [l for l in all_lines if l not in affected_lines]

                        pending_items.append({
                            'type': 'rail_status',
                            'unaffected_lines_list': unaffected_lines,
                            'affected_lines_list': affected_lines
                        })

                    # --- DETAILED ALERTS ---
                    if due_for_alerts and rail_alerts:
                        target_lines = config.get('rail_alert_lines', [])
                        alert_pages_added = False
                        use_fancy = config.get('show_lines_in_their_colors', False)

                        for inc in rail_alerts:
                            lines_str = inc.get('LinesAffected', 'All').rstrip(';')
                            affected_lines_list = [l.strip() for l in lines_str.split(';') if l.strip()]

                            if not target_lines or any(line in affected_lines_list for line in target_lines):
                                desc = inc.get('Description', '').strip()
                                if not desc:
                                    continue

                                if not use_fancy:
                                    clean_lines = lines_str.rstrip('; ').replace(';', ',')
                                    full_text = f"{clean_lines}: {desc}"
                                    all_wrapped = wrap_text_pixel_perfect(full_text, 65, shared_font)
                                else:
                                    all_wrapped = wrap_text_pixel_perfect(desc, 65, shared_font)

                                if not all_wrapped:
                                    print("Wrap_text_pixel_perfect returned nothing")
                                    continue

                                if config.get('show_splash') and not alert_pages_added:
                                    pending_items.append({'type': 'splash', 'header': "METRORAIL\nALERTS"})
                                    alert_pages_added = True

                                if not use_fancy:
                                    for i in range(0, len(all_wrapped), 4):
                                        pending_items.append({
                                            'type': 'rail_alert',
                                            'lines_affected': lines_str,
                                            'body_lines': "\n".join(all_wrapped[i:i+4]),
                                            'page_index': i // 4
                                        })
                                else:
                                    pending_items.append({
                                        'type': 'rail_alert',
                                        'lines_affected': lines_str,
                                        'body_lines': "\n".join(all_wrapped[:3]),
                                        'page_index': 0
                                    })
                                    remaining = all_wrapped[3:]
                                    for i in range(0, len(remaining), 4):
                                        pending_items.append({
                                            'type': 'rail_alert',
                                            'lines_affected': lines_str,
                                            'body_lines': "\n".join(remaining[i:i+4]),
                                            'page_index': (i // 4) + 1
                                        })

                except Exception as e:
                    print(f"[{time.monotonic() - start_secs:.1f}s] [ERROR] Rail Logic: {e}")

            if pending_items:
                print(f"Queued items: {len(pending_items)}")
            conductor_phase = 'elevator_outages'

        # Phase: elevator_outages — only runs when rail_alerts queued nothing
        if conductor_phase == 'elevator_outages' and not pending_items:
            elevator_outage_interval = config.get('elevator_outage_display_frequency', 1200)
            time_since_last_elevator_outage = now - last_elevator_outages_display_time
            if show_elevator_outages and (elevator_outage_interval == 0 or time_since_last_elevator_outage >= elevator_outage_interval):
                try:
                    if (now - last_fetch_time_elevators) >= intermission:
                        elevator_outages = api.fetch_elevator_outages(requests) or []
                        last_fetch_time_elevators = now
                        print(f"[{time.monotonic() - start_secs:.1f}s] Fresh Fetch: Elevator Outages")

                    if elevator_outages:
                        outage_counts = {}
                        for code in elevator_outages:
                            if code in STATIONS_FOR_OUTAGES:
                                name = STATIONS_FOR_OUTAGES[code]
                                outage_counts[name] = outage_counts.get(name, 0) + 1

                        if outage_counts:
                            full_sentence = alert_board.build_elevator_string(outage_counts)
                            wrapped = wrap_text_pixel_perfect(full_sentence, 65, shared_font)

                            if config.get('show_splash'):
                                pending_items.append({'type': 'splash', 'header': "ELEVATOR\nOUTAGES", 'color': 0xFF6600})

                            for i in range(0, len(wrapped), 4):
                                pending_items.append({
                                    'type': 'elevator_outage',
                                    'body_lines': "\n".join(wrapped[i:i+4]),
                                    'page_index': i // 4
                                })
                            print(f"Queued items: {len(pending_items)}")
                except Exception as e:
                    print(f"[{time.monotonic() - start_secs:.1f}s] [ERROR] Elevator Logic: {e}")

            conductor_phase = 'trains'

            # If neither phase queued anything, start the next train cycle immediately
            if not pending_items and train_screens:
                for i, stat in enumerate(train_screens):
                    if stat.get('station_code', ''):
                        pending_items.append({
                            'type': 'train',
                            'station_code': stat.get('station_code', 'A01'),
                            'config_details': stat
                        })
                        train_cursor = i + 1
                        break

    if need_next_item:
        if pending_items:
            active_item = pending_items.pop(0)
        need_next_item = False

    # --- 2. THE PERFORMER (HANDLES UI EXECUTION LOGIC)
    if active_item is None:
        time.sleep(1)
        need_next_item = True
        continue

    try:
        if active_item['type'] == 'train':
            trains_subgroup.hidden = False
            alerts_subgroup.hidden = True
            buses_subgroup.hidden = True

            target_cfg = active_item.get('config_details')
            s_code = active_item.get('station_code')
            lines = "".join(target_cfg.get('lines', []))
            group_name = "".join([str(g) for g in target_cfg.get('groups', [])])
            cache_key = f"{s_code}_{group_name}"
            
            age = now - last_fetch_time_trains.get(cache_key, -100)

            if age >= intermission:
                try:
                    train_predictions = api.fetch_train_predictions(requests, target_cfg) or []
                    train_predictions_cache[cache_key] = train_predictions
                    last_fetch_time_trains[cache_key] = now
                    print(f"[{time.monotonic() - start_secs:.1f}s] Fresh Fetch: {cache_key}")
                except Exception as e:
                    print(f"[{time.monotonic() - start_secs:.1f}s] [API] Fail: {e}")
                    if cache_key not in train_predictions_cache:
                        train_predictions_cache[cache_key] = []
                
            train_data = train_predictions_cache.get(cache_key, [])
            train_board.refresh(target_cfg, train_data)
            log_screen(start_secs, is_rotating, target_cfg)

        elif active_item['type'] == 'bus':
            trains_subgroup.hidden = True
            alerts_subgroup.hidden = True
            buses_subgroup.hidden = False
            bus_board.refresh(active_item)
            route_ids = [r.get('route_id', '??') for r in active_item.get('routes', [])]
            log_screen(start_secs, is_rotating,
                       {'station_code': 'BUS', 'lines': route_ids, 'groups': []})

        elif active_item['type'] in ['splash', 'rail_status', 'rail_alert', 'elevator_outage']:
            trains_subgroup.hidden = True
            alerts_subgroup.hidden = False
            buses_subgroup.hidden = True
            
            # 1. Determine the Mode and Color
            a_type = active_item['type']
            
            # Use heading_color for splashes, otherwise use functional alert colors
            if a_type == 'splash':
                alert_color = config.get('heading_color', 0xFF0000)
            else:
                alert_color = config.get('text_color', 0xFF6600)

            # 2. Routing to the Unified Update
            if a_type == 'splash':                
                alert_board.update('splash', None, header_text=active_item['header'], color=alert_color)
            
            elif a_type == 'rail_status':
                data = {
                    'unaffected_lines': active_item.get('unaffected_lines_list', []),
                    'affected_lines': active_item.get('affected_lines_list', [])
                }
                alert_board.update('rail_status', data)

            elif a_type == 'rail_alert':
                data = {
                    'lines_affected': active_item.get('lines_affected', 'All'),
                    'body_lines': active_item.get('body_lines', ''),
                    'page_index': active_item.get('page_index', 0)
                }
                # Let the board handle the rest!
                alert_board.update('detail', data, color=alert_color)

            elif a_type == 'elevator_outage':
                alert_board.update('elevator_outage', active_item.get('body_lines', ''))

            # 3. Logging
            if a_type == 'splash':
                log_name = 'SPLASH'
                log_lines = [active_item.get('header', '').replace('\n', ' ')]
            elif a_type == 'rail_status':
                log_name = 'STATUS'
                log_lines = []
            elif a_type == 'rail_alert':
                log_name = 'ALERT(S)'
                log_lines = []
            else:
                log_name = 'ELEVATOR OUTAGE(S)'
                log_lines = []
            log_screen(start_secs, is_rotating, {'station_code': log_name, 'lines': log_lines, 'groups': []})

    except Exception as e:
        print(f"[{time.monotonic() - start_secs:.1f}s] [ERROR] Loop execution: {e}")

    # --- 3. THE STAGE MANAGER (TIMING & ROTATION) ---
    safe_refresh(display)
    report_memory()

    if active_item.get('type') == 'splash':
        rotation_wait = config.get('splash_rotation_speed', 2)

    elif active_item.get('type') in ['rail_alert', 'elevator_outage']:
        rotation_wait = config.get('alerts_rotation_speed', 5)

    else:
        # Existing speed for the main train predictions
        rotation_wait = config.get('general_rotation_speed', 7)

    # We need to know if the loop ended because of a button press 
    # or because time just ran out.
    
    start_wait = time.monotonic()
    btn_result = None
    while (time.monotonic() - start_wait) < rotation_wait:
        btn_result = check_buttons()
        if btn_result:
            break
        time.sleep(0.05)

    # Check for Alert Mode Changes
    if btn_result == "JUMP_RAIL_ALERTS":
        pending_items = []
        train_cursor = 0
        bus_cursor = 0
        conductor_phase = 'rail_alerts'
        last_rail_alert_display_time = 0
        last_rail_status_display_time = 0
        need_next_item = True
        print(f"[{time.monotonic() - start_secs:.1f}s] Jumping to Rail Alerts.")

    elif btn_result == "JUMP_ELEVATOR_OUTAGES":
        pending_items = []
        train_cursor = 0
        bus_cursor = 0
        conductor_phase = 'elevator_outages'
        last_elevator_outages_display_time = 0
        need_next_item = True
        print(f"[{time.monotonic() - start_secs:.1f}s] Jumping to Elevator Outages.")

    elif btn_result == "STATE_CHANGE_ALERTS":
        pending_items = []
        train_cursor = 0
        bus_cursor = 0
        conductor_phase = 'trains'
        last_rail_alert_display_time = 0
        last_rail_status_display_time = 0
        last_elevator_outages_display_time = 0
        need_next_item = True
        print(f"[{time.monotonic() - start_secs:.1f}s] Alert Mode Changed: Resetting to Start.")

    # Check for Rotation Toggles (stay on current screen)
    elif btn_result == "STATE_CHANGE_ROTATION":
        print(f"[{time.monotonic() - start_secs:.1f}s] Rotation Toggled: is_rotating={is_rotating}")

    # Handle Manual Advance or Automatic Rotation
    else:
        should_advance = (is_rotating and not btn_result) or (btn_result == "MOVE_NEXT")

        if should_advance:
            p_type = active_item.get('type')
            if p_type == 'rail_status':
                last_rail_status_display_time = time.monotonic()
            elif p_type == 'rail_alert':
                last_rail_alert_display_time = time.monotonic()
            elif p_type == 'elevator_outage':
                last_elevator_outages_display_time = time.monotonic()

            need_next_item = True
            last_rotation_time = time.monotonic()
        # else: paused — active_item persists, need_next_item stays False
