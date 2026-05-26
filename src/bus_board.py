import displayio
from adafruit_display_text.label import Label


class BusBoard:
    def __init__(self, parent_group, font, cfg):
        self.group = displayio.Group()
        self._current_h1 = None
        self._current_h2 = None
        self._heading_color = cfg.get('heading_color', 0xFF0000)
        self._text_color = cfg.get('text_color', 0xFF6600)

        colors = [self._heading_color, self._heading_color, self._text_color, self._text_color]
        self.labels = []
        for i, color in enumerate(colors):
            lbl = Label(font, text=' ', color=color,
                        anchor_point=(0.5, 0), anchored_position=(32, i * 8))
            self.group.append(lbl)
            self.labels.append(lbl)

        self.ol_left = []
        self.ol_right = []
        for i in range(4):
            left = Label(font, text=' ', color=self._text_color,
                         anchor_point=(0, 0), anchored_position=(0, i * 8))
            right = Label(font, text=' ', color=self._text_color,
                          anchor_point=(1.0, 0), anchored_position=(63, i * 8))
            self.group.append(left)
            self.group.append(right)
            self.ol_left.append(left)
            self.ol_right.append(right)

        parent_group.append(self.group)

    def refresh(self, page_data):
        show_header = page_data.get('show_header', True)
        stop_cfg = page_data.get('config_details', {})
        routes = page_data.get('routes', [])
        heading_color = self._heading_color
        text_color = self._text_color
        display_mode = page_data.get('display_mode', 2)

        if display_mode == 1:
            self._current_h1 = None
            self._current_h2 = None

            alt2 = stop_cfg.get('alt_bus_header2', '') if show_header else ''
            if not show_header:
                header_rows = 0
            elif alt2:
                header_rows = 2
            else:
                header_rows = 1

            arrivals = page_data.get('arrivals', [])[:4 - header_rows]

            for lbl in self.labels:
                lbl.text = ' '
            for i in range(4):
                self.ol_left[i].text = ' '
                self.ol_right[i].text = ' '

            if header_rows >= 1:
                alt1 = stop_cfg.get('alt_bus_header1', '')
                self.labels[0].color = heading_color
                self.labels[0].text = alt1 if alt1 else f"STOP {stop_cfg.get('stop_id', '?')}"
            if header_rows == 2:
                self.labels[1].color = heading_color
                self.labels[1].text = alt2

            for idx, arr in enumerate(arrivals):
                row = header_rows + idx
                self.ol_left[row].text = f"{arr['route_id']} {arr['direction']}"
                self.ol_right[row].text = f"{arr['time']} min"

        else:
            for i in range(4):
                self.ol_left[i].text = ' '
                self.ol_right[i].text = ' '

            if show_header:
                alt1 = stop_cfg.get('alt_bus_header1', '')
                alt2 = stop_cfg.get('alt_bus_header2', '')
                h1 = alt1 if alt1 else f"STOP {stop_cfg.get('stop_id', '?')}"
                h2 = alt2 if alt2 else ' '

                if h1 != self._current_h1:
                    self.labels[0].color = heading_color
                    self.labels[0].text = h1
                    self._current_h1 = h1
                if h2 != self._current_h2:
                    self.labels[1].color = heading_color
                    self.labels[1].text = h2
                    self._current_h2 = h2

                r = routes[0] if routes else None
                self.labels[2].color = text_color
                self.labels[2].text = f"{r.get('route_id', '??')} {r.get('direction', '??')}" if r else ' '
                self.labels[3].color = text_color
                self.labels[3].text = _format_minutes(r.get('times', [])) if r else ' '

            else:
                self._current_h1 = None
                self._current_h2 = None
                for row_pair, r in enumerate(routes[:2]):
                    base = row_pair * 2
                    self.labels[base].color = text_color
                    self.labels[base].text = f"{r.get('route_id', '??')} {r.get('direction', '??')}"
                    self.labels[base + 1].color = text_color
                    self.labels[base + 1].text = _format_minutes(r.get('times', []))
                if len(routes) < 2:
                    self.labels[2].text = ' '
                    self.labels[3].text = ' '


def _format_minutes(arrivals):
    if not arrivals:
        return ' '
    strs = [str(t) for t in sorted(arrivals[:3])]
    if len(strs) == 1:
        return f"{strs[0]} min"
    if len(strs) == 2:
        return f"{strs[0]} & {strs[1]} min"
    return f"{strs[0]}, {strs[1]}, & {strs[2]} min"
