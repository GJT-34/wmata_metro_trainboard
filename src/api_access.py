import gc, os, time
from config import config
from utils import STATIONS_FOR_PREDICTIONS

_LINE_NAME_MAP = {
    'RED': 'RD', 'YELLOW': 'YL', 'GREEN': 'GR',
    'ORANGE': 'OR', 'SILVER': 'SV', 'BLUE': 'BL'
}

class MetroApi:
    def __init__(self):
        # Cache the API key once
        self._api_key = os.getenv("METRO_API_KEY")
        self.corrections = STATIONS_FOR_PREDICTIONS
        
        self._api_base = "https://api.wmata.com"
        self._wmata_base = "https://wmata.com"

    def fetch_train_predictions(self, requests, station_cfg: dict):
        path = '/StationPrediction.svc/json/GetPrediction/'
        url = f"{self._api_base}{path}{station_cfg['station_code']}"
        headers = {'api_key': self._api_key}
        retries = config.get('metro_api_retries', 3)

        for attempt in range(retries):
            try:
                # Use timeout to prevent hanging the Matrix refresh
                with requests.get(url, headers=headers, timeout=10) as response:
                    if response.status_code in (401, 403):
                        print(f"Auth Error: {response.status_code}")
                        return None
                    
                    if response.status_code != 200:
                        time.sleep(1)
                        continue
                    
                    data = response.json()
                    gc.collect() # Clean up before processing
                    return self._process_train_data(data, station_cfg)
            except Exception as e:
                print(f"Conn Error: {e}")
                if attempt < retries - 1: time.sleep(2)
        return []

    def fetch_rail_alerts(self, requests):
        url = self._wmata_base + "/rider_tools/metro_service_status/feeds/mis/rail.xml"
        try:
            with requests.get(url, timeout=10) as response:
                if response.status_code == 200:
                    clean = bytearray(b for b in response.content if b < 128)
                    text = clean.decode('utf-8')
                    gc.collect()
                    return self._parse_rss_alerts(text)
        except Exception as e:
            print(f"Alert Fetch Error: {type(e).__name__}: {e}")
        return []

    def _parse_rss_alerts(self, text):
        alerts = []
        pos = 0
        while True:
            start = text.find('<item>', pos)
            if start == -1:
                break
            end = text.find('</item>', start)
            if end == -1:
                break
            item = text[start:end]
            title = self._extract_tag(item, 'title')
            desc = self._extract_tag(item, 'description')
            if title and desc:
                desc = (desc.replace('\r', '').replace('\n', ' ')
                            .replace('&amp;', '&').replace('&lt;', '<')
                            .replace('&gt;', '>').replace('&quot;', '"')
                            .replace('&apos;', "'").replace('&#39;', "'").replace('&#x27;', "'")
                            .replace('&#47;', '/').replace('&#x2f;', '/').replace('&#x2F;', '/'))
                desc_lower = desc.lower()
                cutoff = len(desc)
                for marker in ('. for more info', '. info'):
                    idx = desc_lower.find(marker)
                    if idx != -1:
                        cutoff = min(cutoff, idx + 1)
                desc = desc[:cutoff].strip()
                codes = [_LINE_NAME_MAP.get(p.strip(), p.strip()) for p in title.split(',') if p.strip()]
                alerts.append({
                    'LinesAffected': '; '.join(codes) + ';' if codes else 'All',
                    'Description': desc.strip()
                })
            pos = end + 7
        gc.collect()
        return alerts

    def _extract_tag(self, text, tag):
        open_tag = f'<{tag}>'
        start = text.find(open_tag)
        if start == -1:
            return ''
        start += len(open_tag)
        end = text.find(f'</{tag}>', start)
        return text[start:end].strip() if end != -1 else ''

    def fetch_elevator_outages(self, requests):
        path = '/Incidents.svc/json/ElevatorIncidents'
        url = f"{self._api_base}{path}"
        headers = {"api_key": self._api_key}
        try:
            gc.collect()
            with requests.get(url, headers=headers, timeout=10) as response:
                if response.status_code == 200:
                    raw = response.json().get("ElevatorIncidents", [])
                    if not raw:
                        return []
                    station_codes = [
                        inc.get('StationCode') for inc in raw 
                        if inc and inc.get('UnitType') == "ELEVATOR" and inc.get('StationCode')
                    ]
                    raw = None
                    gc.collect()
                    return list(set(station_codes))
        except Exception as e:
            print(f"Elevator API Error: {e}")
            return []

    def fetch_bus_predictions(self, requests, stop_id):
        url = f"{self._api_base}/NextBusService.svc/json/jPredictions?StopID={stop_id}"
        headers = {'api_key': self._api_key}
        retries = config.get('metro_api_retries', 3)
        for attempt in range(retries):
            try:
                with requests.get(url, headers=headers, timeout=10) as response:
                    if response.status_code in (401, 403):
                        print(f"Auth Error: {response.status_code}")
                        return {}
                    if response.status_code != 200:
                        time.sleep(1)
                        continue
                    data = response.json()
                    gc.collect()
                    return self._process_bus_data(data)
            except Exception as e:
                print(f"Bus API Error: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
        return {}

    def _process_bus_data(self, json_data):
        """Group predictions by route; return {route_id: {direction_text, times}}."""
        routes = {}
        for p in json_data.get('Predictions', []):
            rid = p.get('RouteID', '')
            mins = p.get('Minutes', 0)
            dtxt = p.get('DirectionText', '')
            if rid not in routes:
                routes[rid] = {'direction_text': dtxt, 'times': []}
            routes[rid]['times'].append(mins)
        for r in routes:
            routes[r]['times'].sort()
        gc.collect()
        return routes

    def _process_train_data(self, json_data, station_cfg):
        target_lines = station_cfg.get('lines', [])
        target_groups = [str(g) for g in station_cfg.get('groups', [])]
        transit_time = int(station_cfg.get('transit_time', 0))
        
        trains = json_data.get('Trains', [])
        if not trains: return []

        # List comprehension for efficiency
        processed_list = []
        for t in trains:
            line = t.get('Line')
            group = str(t.get('Group'))
            
            if (not target_lines or line in target_lines) and (not target_groups or group in target_groups):
                m_raw = t.get('Min', '--')
                
                # Numeric value for sorting and pruning
                if m_raw in ("ARR", "BRD"): val = 0
                elif m_raw.isdigit(): val = int(m_raw)
                else: val = -1 # Delayed/Unknown
                
                processed_list.append({
                    'n_min': val,
                    'normalized': self._normalize_train_response(t)
                })

        # Sort: Valid times first, then delays (-1)
        processed_list.sort(key=lambda x: (x['n_min'] == -1, x['n_min']))

        # Pruning (Keep the board legible)
        limit = 4 if not station_cfg.get('train_header', True) else 3
        while len(processed_list) > limit:
            first_mins = processed_list[0]['n_min']
            # If the soonest train is uncatchable, pop it
            if -1 < first_mins < transit_time:
                processed_list.pop(0)
            else:
                break

        return [item['normalized'] for item in processed_list[:limit]]

    def _normalize_train_response(self, t):
        line = t.get('Line', '--')
        
        # Pull the map once per train to avoid repetitive config.get calls
        line_map = config.get('train_line_color', {})
        line_hex = line_map.get(line, config.get('text_color', 0xFFFFFF))
        
        raw_dest = t.get('DestinationName', 'Unknown')
        dest = self._get_corrected_dest_case(raw_dest)
        dest = self._get_corrected_dest_value(dest)
        
        return {
            'line_abbrev': line,
            'line_hex': line_hex,
            'car': t.get('Car', '-'),
            'destination': dest,
            'min': self._get_corrected_min_value(t.get('Min', '--')),
            'group': t.get('Group', '1')
        }

    def _get_corrected_dest_value(self, dest):
        dest_lower = dest.lower()
        for key, corrected in self.corrections.items():
            if dest_lower.startswith(key):
                return corrected
        return dest

    def _get_corrected_dest_case(self, dest):
        if not dest.isupper(): return dest
        return " ".join([w[0].upper() + w[1:].lower() for w in dest.split()])

    def _get_corrected_min_value(self, min_val):
        mapping = {'ARR': 'AR', 'BRD': 'BD', 'DLY': 'DY', '---': 'DY'}
        return mapping.get(min_val, str(min_val)[:2])