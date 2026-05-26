config = {

    # See https://github.com/GJT-34/dc-metro/blob/main/CONFIGURE.md for info
    #   on configuration options.

    ###################################
    # Settings You Are Likely to Adjust
    ###################################
    
    # Train Arrival Prediction Screens
    'train_arrival_screens': [
        {
            'station_code': 'K01',
            'lines': ['OR', 'SV',],
            'groups': [1,],           
            'transit_time': 0,
            'train_display_mode': 1,
            'train_header': True,
            'alt_train_header': '',
        },
        {
            'station_code': 'K01',
            'lines': ['OR', 'SV',],
            'groups': [2,],           
            'transit_time': 0,
            'train_display_mode': 1,
            'train_header': True,
            'alt_train_header': '',
        },
    ],

    'bus_arrival_screens': [
        {
            'stop_id': '1002290',
            'lines': ['C61', 'D80',],
            'transit_time': 0,
            'bus_header': True,
            'bus_display_mode': 2,
            'alt_bus_header1': '',
            'alt_bus_header2': '',
        },
    ],

    # Rail Status, Rail Alert, and Elevator Outage Screens
    'rail_status_display_frequency': 120,
    'rail_alert_display_frequency': 600,
    'rail_alert_lines': [],
    'elevator_outage_display_frequency': -1,

    ########################################
    # Settings You Are Less likely to Adjust
    ########################################
    
    # Wifi & API Settings
    'wifi_max_attempts': 5,
    'metro_api_fetch_intermission': 20,
    'metro_api_retries': 3,

    # UI Behavior
    'start_in_rotating_mode': True,
    'general_rotation_speed': 8,
    'alerts_rotation_speed': 5,
    'show_splash': True,
    'splash_rotation_speed': 3,
    'dest_max_characters': 8,

    # Visual Styling & Colors
    'text_color': 0xFF6600,
    'text_color_8-car': 0x00FF00,
    'heading_color': 0xFF0000,
    'show_lines_in_their_colors': False,
    'status_dash_color': 0xFF6600,
    'status_exclamation_color': 0xFF0000,
    'train_line_color': {
        'RD': 0xFF0000,
        'OR': 0xFF3300,
        'YL': 0xFFFF00,
        'GR': 0x00FF00,
        'BL': 0x0000FF,
        'SV': 0x666666,
    },
    'indicator_pixels_color': [
        0x000000, # 0: Off
        0xFF0000, # 1
        0x0000FF, # 2
        0xFFFF00, # 3
        0x00FFFF, # 4
    ],

    # Arrow Directional Layout
    'group_1_arrow_direction': 'right', 
    'group_2_arrow_direction': 'left',

    # Button Timing
    'long_press_threshold': 0.5,
    'long_blink_time': 0.5,
    'short_blink_time': 0.25,
    
}