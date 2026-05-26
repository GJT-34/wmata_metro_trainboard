import gc
import time
from config import config

STATIONS_FOR_PREDICTIONS = {
    'no p': 'NoPasngr',
    'nop': 'NoPasngr',
    'ssenger': 'NoPasngr',
    'last': 'Last Trn',
    'lst': 'Last Trn',
    'addi': 'Addsn Rd',
    'anac': 'Anacstia',
    'arl': 'Arl Cem',
    'ball': 'Ballston',
    'benn': 'Benn Rd',
    'brad': 'BraddkRd',
    'bran': 'Brnch Av',
    'broo': 'Brooklnd',
    'capital h': 'Cap Hgts',
    'cap h': 'Cap Hgts',
    'capital s': 'CapitolS',
    'cap s': 'CapitolS',
    'chev': 'Chevrly',
    'clar': 'Clarndn',
    'clev': 'Cleve Pk',
    'coll': 'Collge Pk',
    'colu': 'Col Hgts',
    'col h': 'Col Hgts',
    'cong': 'CongHgts',
    'court': 'CrtHouse',
    'crt': 'CrtHouse',
    'crys': 'CrystlCy',
    'dean': 'Deanwd',
    'down': 'Largo',
    'dt l': 'Largo',
    'dunn': 'Dunn Lor',
    'dupo': 'DupntCir',
    'east f': 'E Flls Ch',
    'e f': 'E Flls Ch',
    'easte': 'East Mkt',
    'eisen': 'Eisen Av',
    'farragut n': 'Farrgt N',
    'farragut w': 'Farrgt W',
    'federal c': 'Fed Ctr',
    'fed c': 'Fed Ctr',
    'federal t': 'Fed Tri',
    'fed t': 'Fed Tri',
    'fogg': 'Foggy Bt',
    'fore': 'ForstGln',
    'fort': 'Ft Tottn',
    'ft': 'Ft Tottn',
    'fra': 'Frnconia',
    'frnc': 'Frnconia',
    'frie': 'FrndHgts',
    'frnd': 'FrndHgts',
    'gall': 'GallryPl',
    'china': 'GallryPl',
    'geor': 'Georg Av',
    'ga a': 'Georg Av',
    'petw': 'Georg Av',
    'gros': 'Grsvnor',
    'hunt': 'Hntingtn',
    'hyat': 'Hyatts X',
    'inno': 'Inno Ctr',
    'jud': 'Judi Sq',
    'kin': 'King St',
    'lan': 'Landovr',
    'lou': 'LoudnGty',
    'mcl': 'McLean',
    'mcp': 'McPh Sq',
    'med': 'Med Ctr',
    'met': 'MetroCtr',
    'min': 'Minn Av',
    'mn a': 'Minn Av',
    'mor': 'Morgn Bd',
    'mt': 'Mt Vn Sq',
    'nav': 'Navy Yd',
    'nay': 'NaylorRd',
    'new': 'NewCrltn',
    'nom': 'NoMa',
    'north b': 'N Bethsd',
    'n b': 'N Bethsd',
    'pentagon c': 'PntgnCty',
    'potomac a': 'Potmc Av',
    'potomaca': 'Potmc Av',
    'potomac y': 'Potmc Yd',
    'potomacy': 'Potmc Yd',
    'res': 'RestnCtr',
    'rho': 'RI Av',
    'bren': 'RI Av',
    'roc': 'Rockvlle',
    'ron': 'NatlArpt',
    'nat': 'NatlArpt',
    'dca': 'NatlArpt',
    'washington n': 'NatlArpt',
    'ros': 'Rosslyn',
    'shad': 'Shady Gr',
    'shaw': 'Shaw',
    'silv': 'SilvrSpr',
    'sm': 'Smithson',
    'sou': 'South Av',
    'spr': 'Spr Hill',
    'sta': 'Stadium',
    'ten': 'Tenleytn',
    'twi': 'Twinbrk',
    'u s': 'U St',
    'unio': 'Union St',
    'van d': 'Van Dorn',
    'van n': 'Van Ness',
    'vie': 'Vienna',
    'fai': 'Vienna',
    'vir': 'VirgnaSq',
    'va s': 'VirgnaSq',
    'washington d': 'Dulles',
    'dulles': 'Dulles',
    'iad': 'Dulles',
    'wat': 'Wtrfrnt',
    'west f': 'W Flls Ch',
    'w f': 'W Flls Ch',
    'west h': 'W Hyatts',
    'w h': 'W Hyatts',
    'wieh': 'Wiehle',
    'wood': 'WoodlyPk',
    'zoo': 'WoodlyPk'
}

STATIONS_FOR_OUTAGES = {
    'G03': 'Addison Rd',
    'F06': 'Anacostia',
    'F02': 'Archives',
    'C06': 'Arl Cemetary',
    'N12': 'Ashburn',
    'K04': 'Ballston',
    'G01': 'Benning Rd',
    'A09': 'Bethesda',
    'C12': 'Braddock Rd',
    'F11': 'Branch Av',
    'B05': 'Brookland',
    'G02': 'Capitol Heights',
    'D05': 'Capitol South',
    'D11': 'Cheverly',
    'K02': 'Clarendon',
    'A05': 'Cleveland Park',
    'E09': 'College Park',
    'E04': 'Columbia Heights',
    'F07': 'Congress Heights',
    'K01': 'Court House',
    'C09': 'Crystal City',
    'D10': 'Deanwood',
    'G05': 'Largo',
    'K07': 'Dunn Loring',
    'A03': 'Dupont Circle',
    'K05': 'East Falls Church',
    'D06': 'Eastern Market',
    'C14': 'Eisenhower Av',
    'A02': 'Farragut North',
    'C03': 'Farragut West',
    'D04': 'Federal Center SW',
    'D01': 'Federal Triangle',
    'C04': 'Foggy Bottom',
    'B09': 'Forest Glen',
    'B06': 'Fort Totten',
    'E06': 'Fort Totten',
    'J03': 'Franconia',
    'A08': 'Friendship Heights',
    'B01': 'Gallery Pl',
    'F01': 'Gallery Pl',
    'E05': 'Georgia Ave',
    'B11': 'Glenmont',
    'E10': 'Greenbelt',
    'N03': 'Greensboro',
    'A11': 'Grosvenor',
    'N08': 'Herndon',
    'C15': 'Huntington',
    'E08': 'Hyattsville Crossing',
    'N09': 'Innovation Center',
    'B02': 'Judiciary Sq',
    'C13': 'King St',
    'D12': 'Landover',
    'D03': 'L\'Enfant Plaza',
    'F03': 'L\'Enfant Plaza',
    'N11': 'Loudon Gateway',
    'N01': 'McLean',
    'C02': 'McPherson Sq',
    'A10': 'Medical Center',
    'A01': 'Metro Center',
    'C01': 'Metro Center',
    'D09': 'Minnesota Av',
    'G04': 'Morgan Blvd',
    'E01': 'Mt Vernon Sq',
    'F05': 'Navy Yard',
    'F09': 'Naylor Road',
    'D13': 'New Carrollton',
    'B35': 'NoMa',
    'A12': 'North Bethesda',
    'C07': 'Pentagon',
    'C08': 'Pentagon City',
    'D07': 'Potomac Av',
    'C11': 'Potomac Yard',
    'N07': 'Reston Town Center',
    'B04': 'Rhode Island Av',
    'A14': 'Rockville',
    'C10': 'National Airport',
    'C05': 'Rosslyn',
    'A15': 'Shady Grove',
    'E02': 'Shaw-Howard U',
    'B08': 'Silver Spring',
    'D02': 'Smithsonian',
    'F08': 'Southern Av',
    'N04': 'Spring Hill',
    'D08': 'Stadium',
    'F10': 'Suitland',
    'B07': 'Takoma',
    'A07': 'Tenleytown',
    'A13': 'Twinbrook',
    'N02': 'Tysons',
    'E03': 'U St',
    'B03': 'Union Station',
    'J02': 'Van Dorn St',
    'A06': 'Van Ness',
    'K08': 'Vienna',
    'K03': 'Virginia Sq',
    'N10': 'Dulles',
    'F04': 'Waterfront',
    'K06': 'West Falls Church',
    'E07': 'West Hyattsville',
    'B10': 'Wheaton',
    'N06': 'Wiehle',
    'A04': 'Woodley Park'
}

def safe_refresh(display_obj):
    try:
        display_obj.refresh()
    except RuntimeError:
        pass

def log_screen(start_secs, is_rotating, active_station):
    """Formats and prints current screen information to the serial console."""
    name = active_station.get('station_code', 'A01')
    lines = ", ".join(active_station.get('lines', []))
    groups = ", ".join(str(g) for g in active_station.get('groups', []))
    status = "[ROTATING]" if is_rotating else "[STATIONARY]"

    parts = [f"[{time.monotonic() - start_secs:.1f}s]", status, name]
    if lines:
        parts.append(f"({lines})")
    if groups:
        parts.append(f"(track(s) {groups})")
    print(" ".join(parts))

def report_memory():
    """Reports total used RAM and the percentage of the total heap consumed."""
    gc.collect()
    free = gc.mem_free()
    alloc = gc.mem_alloc()
    total = free + alloc
    
    # Calculate how much is actually in use
    used = total - free
    # Percentage of the total heap currently used
    used_percent = (used / total) * 100
    
    print(f"RAM Used: {used/1024:.1f} KB of {total/1024:.1f} KB ({used_percent:.1f}%)")

def wrap_text_pixel_perfect(text, max_width, font, first_row_offset=0):
    rows = []
    current_row = ""
    words = []
    temp_word = ""
    
    # Step 1: Split (Keep your existing logic)
    for char in text:
        temp_word += char
        if char in [" ", "-", ":", "/", ","]:
            words.append(temp_word)
            temp_word = ""
    if temp_word:
        words.append(temp_word)

    # Step 2: Wrap (Updated to handle the offset)
    is_first_row = True
    
    for word in words:
        test_row = current_row + word
        
        # If it's the first row, we subtract the offset from the max_width
        current_limit = max_width - first_row_offset if is_first_row else max_width
        
        if calculate_string_width(test_row.rstrip(), font) <= current_limit:
            current_row = test_row
        else:
            if current_row:
                rows.append(current_row.rstrip())
            current_row = word if not word.isspace() else ""
            is_first_row = False # All subsequent rows use the full max_width
            
    if current_row:
        rows.append(current_row.rstrip())
        
    return rows

def calculate_string_width(string, font):
    """Returns the total pixel width of a string."""
    width = 0
    for char in string:
        glyph = font.get_glyph(ord(char))
        if glyph:
            width += glyph.shift_x
    return width

def sort_wmata_lines(line_list):
    """
    Sorts a list of WMATA line codes into the official 
    signage order: Red, Yellow, Green, Orange, Silver, Blue.
    """
    # Official WMATA priority ranking
    priority = {
        'RD': 1,  # Red
        'YL': 2,  # Yellow
        'GR': 3,  # Green
        'OR': 4,  # Orange
        'SV': 5,  # Silver
        'BL': 6   # Blue
    }
    
    # Sort using the dictionary rank as the key
    # If a line code isn't in the dict, it gets rank 99 (end of list)
    return sorted(line_list, key=lambda line: priority.get(line.upper(), 99))
