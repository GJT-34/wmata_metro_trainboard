import displayio
from adafruit_display_text.label import Label
from config import config

# train_display_mode values:
# 1 - Colored arrow + car length
# 2 - Two-letter train line abbreviation
# 3 - First letter of train line + colored arrow

class TrainBoard:
    def __init__(self, parent_group, font):
        self.parent_group = parent_group
        self.font = font
        self.trains = []
        self.current_station_code = None
        self.current_cols = None
        self.current_head = None
        self.current_alt = None
        self.header_label = None

    def refresh(self, station_cfg, train_predictions):
        new_code = station_cfg.get('station_code')
        new_cols = station_cfg.get('train_display_mode', 1)
        new_head = station_cfg.get('train_header', True)
        new_alt = station_cfg.get('alt_train_header', '')

        # 1. Configuration Change Detection
        if (new_code != self.current_station_code or
            new_cols != self.current_cols or
            new_head != self.current_head or
            new_alt != self.current_alt):

            self._build_layout(station_cfg)
            self.current_station_code = new_code
            self.current_cols = new_cols
            self.current_head = new_head
            self.current_alt = new_alt

        # 2. Dynamic Header Update
        if self.header_label and new_head:
            self.header_label.text = station_cfg.get('alt_train_header', 'Metro')

        # 3. Data Injection
        #  We loop through all pre-allocated rows. 
        #  If there's no data for a row, it hides itself.
        for i, row in enumerate(self.trains):
            if train_predictions and i < len(train_predictions):
                t = train_predictions[i]
                row.update(
                    line_abbrev=t['line_abbrev'],
                    line_hex=t['line_hex'],
                    car=t['car'], 
                    destination=t['destination'], 
                    minutes=t['min'], 
                    group=t.get('group')
                )
            else:
                row.group.hidden = True

    def _build_layout(self, station_cfg):
        # Clear the physical display group
        while len(self.parent_group) > 0:
            self.parent_group.pop()
        
        self.trains = [] 
        header_type = station_cfg.get('train_header', True)
        alt_title = station_cfg.get('alt_train_header', '')
        first_cols = station_cfg.get('train_display_mode', 3)
        row_height = 8
        current_y = 0

        # --- A. HEADER GENERATION ---
        if header_type:
            if alt_title:
                # Centered Station Name Header
                self.header_label = Label(
                    self.font, color=config['heading_color'],
                    text=alt_title,
                    base_alignment=True, anchor_point=(0.5, 0), anchored_position=(32, current_y)
                )
                self.parent_group.append(self.header_label)
            else:
                # Standard Header
                if first_cols == 1:
                    # 'MIN' is at 65 b/c fonts have one pixel of padding on right-hand side
                    h_source = [("LN", 0, 0), ("CAR", 0, 12), ("DST", 0, 29), ("MIN", 1, 65)]
                else:
                    h_source = [("LN", 0, 0), ("DEST", 0, 13), ("MIN", 1, 65)]

                for text, anchor_x, pos in h_source:
                    self.parent_group.append(Label(
                        self.font, color=config['heading_color'], text=text,
                        base_alignment=True,
                        anchor_point=(anchor_x, 0),
                        anchored_position=(pos, current_y)
                    ))
                self.header_label = None
            current_y += row_height
            num_rows = 3
        else:
            # No Header - Use all 4 rows
            self.header_label = None
            num_rows = 4

        # --- B. ROW ALLOCATION ---
        for _ in range(num_rows):
            row = Train(self.parent_group, current_y, first_cols, self.font)
            self.trains.append(row)
            current_y += row_height
        
class Train:
    def __init__(self, parent_group, y_pos, first_cols, font):
        self.y = y_pos
        self.first_cols = first_cols
        self.font = font
        self.group = displayio.Group()
            
        self.line_label = Label(font, color=config['text_color'], text="",
                               base_alignment=True, anchor_point=(0, 1), anchored_position=(0, (y_pos + 7)))
        
        self.car_label = Label(font, color=config['text_color'], text="",
                               base_alignment=True, anchor_point=(0, 1), anchored_position=(6, (y_pos + 7)))        
        
        self.destination_label = Label(font, color=config['text_color'], text="",
                                        base_alignment=True, anchor_point=(0, 1), anchored_position=(13, (y_pos + 7)))
        
        self.min_label = Label(font, color=config['text_color'], text="",
                               base_alignment=True, anchor_point=(1, 1), anchored_position=(65, (y_pos + 7)))

        self.shape_bm = displayio.Bitmap(3, 7, 2)
        self.shape_pal = displayio.Palette(2)
        self.shape_pal.make_transparent(0)
        self.shape_pal[1] = config['text_color'] 
        
        self.shape_tg = displayio.TileGrid(self.shape_bm, pixel_shader=self.shape_pal, x=0, y=self.y)
        self.shape_tg.hidden = True

        self.group.append(self.shape_tg)
        self.group.append(self.line_label)
        self.group.append(self.car_label)
        self.group.append(self.destination_label)
        self.group.append(self.min_label)
        
        parent_group.append(self.group)
        self.group.hidden = True

    def update(self, line_abbrev, line_hex, car, destination, minutes, group):
        self.group.hidden = False
        
        # 1. Determine Text Color based on config
        use_line_colors = config.get('show_lines_in_their_colors', False)
        text_row_color = line_hex if use_line_colors else config['text_color']

        # 2. COLUMN 1: TEXT (Modes 2 & 3)
        if self.first_cols in (2, 3):
            self.line_label.text = str(line_abbrev)[0] if self.first_cols == 3 else str(line_abbrev)
            self.line_label.color = text_row_color
        else:
            self.line_label.text = ""

        # 3. COLUMN 1: SHAPE (Modes 1 & 3)
        if self.first_cols in (1, 3):
            self.shape_pal[1] = line_hex 
            
            # X-Offset: If letter is present (Mode 3), shift arrow right
            self.shape_tg.x = 7 if self.first_cols == 3 else 0
            
            direction = config.get(f'group_{group}_arrow_direction') if group in (1, 2, "1", "2") else None
            self._update_shape_bitmap(direction)
            self.shape_tg.hidden = False
        else:
            self.shape_tg.hidden = True

        # 4. CAR COLUMN (Only Mode 1)
        if self.first_cols == 1:
            self.car_label.text = str(car) if car else "-"
            self.car_label.color = config.get('text_color_8-car', 0x00FF00) if str(car) == "8" else config['text_color']
        else:
            self.car_label.text = ""

        # 5. DESTINATION & MINUTES
        self.destination_label.text = str(destination)[:config.get('dest_max_characters', 8)]
        self.min_label.text = str(minutes)

    def _update_shape_bitmap(self, direction):
        # Clear bitmap (fill with 0)
        for i in range(21):
            self.shape_bm[i % 3, i // 3] = 0
        
        if direction == 'left':
            pixels = [(0,2),(0,3),(0,4),(1,1),(1,2),(1,3),(1,4),(1,5),(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6)]
        elif direction == 'right':
            pixels = [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,1),(1,2),(1,3),(1,4),(1,5),(2,2),(2,3),(2,4)]
        else: # Standard Rect
            pixels = [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6)]
        
        for px in pixels:
            self.shape_bm[px[0], px[1]] = 1