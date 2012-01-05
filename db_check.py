#!/usr/bin/env python
#
# DB Check
#

#
# import all required modules
#
from struct import *
import sys
# Check sqlite3
import sqlite3
# Check Crypto package (only one import)
from Crypto.Cipher import AES
# Check curses (more than likely available except may be on native Windows port
try:
    import curses
    import curses.panel
except:
    print '* curses import error : not available on your system'
#
# Basic CRYPTO DATA header
#
# !4sIIIIIII= (dtype, ilen, olen, cmode, cbmode, ksize, bsize, ipad)
#
def build_crypto_header( dtype, ilen, olen, cmode, cbmode, ksize, bsize, p0=0):

    str = pack('!4sIIIIIII', dtype, ilen, olen, cmode, cbmode, ksize, bsize, p0)
    return str.encode('hex')

def extract_crypt_header( header ):

    blob = header.decode('hex')
    return unpack('!4sIIIIIII', blob)


# Set AES default to 256, CBC
def crypto_aes_encrypt_blob( data, key, iv='not_so_secure_default_iv' ):

    # Make Encryption Key 32 characters long
    ekey = (key[:32] + 32*'.')[:32]

    # Round data to perfect modulo 16
    ilen = len(data)
    if len(data) % 16:
        data = data + (16 - len(data) % 16) *'.'
    olen = len(data)

    obj = AES.new( ekey, AES.MODE_CBC)
    cypher_text = obj.encrypt( data )

    header = build_crypto_header('HEX.',ilen,olen,0,AES.MODE_CBC,32,AES.block_size)

    return header + cypher_text.encode('hex')

def crypto_aes_decrypt_blob( data, key, iv='not_so_secure_default_iv' ):

    # DATA = HEADER + CRYPTED_DATA
    header = data[:64]
    dtype,ilen,olen,cmode,cbmode,ksize,bsize,pad = extract_crypt_header( header )
    data = data[64:].decode('hex')

    if len(data) % 16:
        raise 'CRYPTO_AES_DECRYPT_BLOB: invalid data len'

    # Make Encryption Key 32 characters long
    dkey = (key[:32] + 32*'.')[:32]
    
    obj = AES.new( dkey, AES.MODE_CBC)
    clear_text = obj.decrypt( data )

    return clear_text[:ilen]

# Class to display db test data using curses
#
# Some demo code available at : http://www.koders.com/python/fidA40DCDA1C47ABC61283C82D221B2ADEC649A648B.aspx
#
class MainCursesDisplayModule:

    def __init__(self):
        self.status = 0

    def init_curses(self):
        self.status = 1

# Prepare curses related data before initial display
def prepare_display():

    try:
        scrwin.border(ord('|'),ord('|'),ord('-'),ord('-'),ord(' '),ord(' '),ord(' '),ord(' '))
        labelwin.addstr(0, 0, 'id:')
        labelwin.addstr(1, 0, 'name:')
        labelwin.addstr(2, 0, 'dest:')
        labelwin.addstr(3, 0, 'progress:')
        labelwin.addstr(4, 0, 'status:')
        labelwin.addstr(5, 0, 'speed:')
        labelwin.addstr(6, 0, 'totals:')
        labelwin.addstr(7, 0, 'error(s):')
    except curses.error: 
        pass
    
    fieldwin.nodelay(1)
    curses.panel.update_panels()
    curses.doupdate()

def redraw_display():

    inchar = -1
    while inchar != ord('q'):
        inchar = fieldwin.getch()

        if inchar != -1:
            # fieldwin.erase()
            fieldwin.addnstr(3, 0, str(inchar), fieldw, curses.A_BOLD)
            curses.panel.update_panels()
            curses.doupdate()

#
# Initialize curses globals
# Note: Need to retain a reference to pan or window else they get garbage collected
# 
labelwin, labelpan = None, None
fieldwin, fieldpan = None, None
scrwin, scrpan, fieldw = None, None, None

def initialize_curses_vars(first=False):

    # First call we initialize also curses else we just recompute the vars (e.g. SIGWINCH)
    if first:
        try:
            global scrwin
            scrwin = curses.initscr()
            curses.start_color()
            curses.noecho()
            curses.cbreak()
            scrwin.keypad(1)
        except:
            print '* curses initialization error *'
            sys.exit(-1)

    # Init Global Variables (compute window and panel sizes)
    global win_maxY, win_maxX
    win_maxY, win_maxX = scrwin.getmaxyx()

    global scrpan
    scrh, scrw = scrwin.getmaxyx()
    scrpan = curses.panel.new_panel(scrwin)

    global labelwin, labelpan 
    labelh, labelw, labely, labelx = scrh - 2, 9, 1, 2
    labelwin = curses.newwin(labelh, labelw, labely, labelx)
    labelpan = curses.panel.new_panel(labelwin)

    global fieldwin, fieldpan, fieldw
    fieldh, fieldw, fieldy, fieldx = scrh - 2, scrw - 2 - labelw - 3, 1, labelw + 3
    fieldwin = curses.newwin(fieldh, fieldw, fieldy, fieldx)
    fieldpan = curses.panel.new_panel(fieldwin)

    # Display fixed info (e.g. Global labels)
    prepare_display()
    
# Make sure to reset terminal to original state
# When curses wrapper is used this is not required.
def reset_terminal():
    curses.nocbreak()
    curses.echo()
    scrwin.erase()
    labelwin.erase()
    fieldwin.erase()
    curses.panel.update_panels()
    curses.doupdate()
    curses.endwin()

#
# DB Stuff
#
# http://docs.python.org/dev/library/sqlite3.html
# http://www.doughellmann.com/PyMOTW/sqlite3/
# 
db_dict = {}
db_con  = None
db_cursor = None

def initialize_sqlite_vars(db_name='test.db'):

    global db_dict, db_con, db_cursor

    db_con = sqlite3.connect(db_name)
    db_con.isolation_level = None
    db_cur = db_con.cursor()

    statement = 'select * from vault'

    pos = 3
    db_cur.execute( statement )
    for entry in db_cur:
        fieldwin.addnstr(pos, 0, str(entry), fieldw)
        pos += 1
#
# Simple Exception Class
#
class InvalidArg(Exception):
    def __init__(self, txt, value):
        self.txt = txt
        self.value = value
    def __str__(self):
        return repr(self.value)
    
# Dialog class
# http://docs.python.org/library/curses.html
#
class table_window():

    def __init__(self):
        # Compute location in parent window
        self.scrh, self.scrw = scrwin.getmaxyx()
        self.tab_h = 20
        self.tab_w = 24
        self.tab_x = (self.scrw - self.tab_w) / 2
        self.tab_y = (self.scrh - self.tab_h) / 2

        self.tab_win = curses.newwin(self.tab_h, self.tab_w, self.tab_y, self.tab_x)
        self.tab_pan = curses.panel.new_panel(self.tab_win)

    def populate(self):

        col0_content = ('row of data\n' * 30).split('\n')
        col1_content = []
        col2_content = []
        for value in range(0,20):
            col1_content.append( value )
            if value % 2:
                col2_content.append( True )
            else:
                col2_content.append( False )
        # Name, Width, Type, Attributes (bit_flags), content]
        tab = [ [ 'column_name0', 8, type(""), 0,  col0_content ], \
                [ 'column_name1', 4, type(0), 0, col1_content ], \
                [ 'column_name2', 2, type(True), 0, col2_content] ]
        self.tab_def = tab
        
        # Compute size of all columns plus L/R borders
        self.tab_all_col_w = 0
        for col in tab:
            self.tab_all_col_w += col[1] + 1
        self.tab_all_col_w += 1

        # Compute max row size
        self.tab_all_row_h = 0
        for col in tab:
            if len( col[4] ) > self.tab_all_row_h:
                self.tab_all_row_h = len( col[4] )
        self.tab_all_row_h += 1        # Add 1 ROW for Title

        # pad should be at least equal to the window size
        if self.tab_all_col_w < self.tab_w:
            self.tab_all_col_w = self.tab_w
        if self.tab_all_row_h < self.tab_h:
            self.tab_all_row_h = self.tab_h
            
        self.tab_pad = curses.newpad( self.tab_all_col_w , self.tab_all_row_h )
        #        for y in range(0, self.tab_all_col_w):
        #    for x in range(0, self.tab_all_row_h):
        #        try: self.tab_pad.addch( y,x, ord('a') + (x*x + y*y) % 26)
        #        except curses.error: pass
        
    def refresh(self):

        # Start at first/column 0
        self.tab_col_index = 0

        # Compute pannel for each column
        # ...

    def display(self):
        
        fieldwin.addnstr(1, 0, str(self.tab_all_col_w), fieldw, curses.A_BOLD)
        fieldwin.addnstr(2, 0, str(self.tab_all_row_h), fieldw, curses.A_BOLD)
        curses.panel.update_panels()

        #        self.tab_pad.box()
        self.tab_pad.addnstr(1,0,"0123456789"*4, self.tab_w-4, curses.A_BOLD)
        self.tab_pad.addnstr(2,1,str(self.tab_all_col_w), self.tab_w-4, curses.A_BOLD)
        self.tab_pad.addnstr(3,1,str(self.tab_all_row_h), self.tab_w-4, curses.A_BOLD)
        self.tab_pad.addnstr(4,1,str(self.tab_w), self.tab_w-4, curses.A_BOLD)
        self.tab_pad.addnstr(5,1,str(self.tab_h), self.tab_w-4, curses.A_BOLD)
        
        #self.tab_win.box()
        self.tab_pad.box()
        self.tab_pad.refresh( 0, 0, self.tab_y, self.tab_x, \
                              self.tab_y+self.tab_w+2, self.tab_x+self.tab_h )
        curses.panel.update_panels()
        curses.doupdate()
        
    def navigate(self):
        
        self.tab_win.keypad(1)
        while True:
            self.key = self.tab_win.getch()
            if self.key == ord('\n'):
                break
            
class test_dialog():

    def __init__(self):
        # Compute location in parent window (default main screen window)
        scrh, scrw = scrwin.getmaxyx()
        self.diag_h = 10
        self.diag_w = 24
        self.diag_x = (scrw - self.diag_w) / 2
        self.diag_y = (scrh - self.diag_h) / 2

        # Sanity check
        if self.diag_h < 5:
            raise InvalidArg('* dialog height is too small', self.diag_h)

        self.diag_win = curses.newwin(self.diag_h, self.diag_w, self.diag_y, self.diag_x)
        self.diag_pan = curses.panel.new_panel(self.diag_win)

        # Basic Dialog. Title, Message, Buttons
        self.diag_title = 'Dialog Title'
        self.diag_title_x = (self.diag_w - len(self.diag_title)) / 2  # Best if we don't skip 1 char for border/boxing
        self.diag_title_y = 1            # skip 1 char for border/boxing
        self.diag_title_border_x = 1
        self.diag_title_color = curses.COLOR_BLUE
        curses.init_pair( self.diag_title_color, self.diag_title_color, curses.COLOR_WHITE)
 
        # Content Area
        self.diag_content = ('random test to fill dialog\n' * self.diag_h).split('\n')
        self.diag_content = ['Simple Dialog', 'with basic header', 'content and buttons', 'more', 'and more' ]
        self.diag_content += [ 'to come', 'in future release' ]
        self.diag_content_y = 2
        self.diag_content_x = 1
        self.diag_content_index = 0
        self.diag_content_pos = 0   # Start from the begining of the content list

        # Buttons Area
        self.diag_btn_orig = [ 'OK', 'BACK', 'CANCEL' ]
        self.diag_btn_select = 0
        self.diag_btn = self.diag_btn_orig[:]
        self.diag_btn[ self.diag_btn_select ] = '<' + self.diag_btn[ self.diag_btn_select ] + '>'
        self.diag_btn_text = reduce( lambda x,y: x + ' ' + y, self.diag_btn)
        self.diag_btn_w = reduce( lambda x,y: x + y + 1, map( lambda x: len(x), self.diag_btn) ) + 2 # L/R borders
        self.diag_btn_x = ( self.diag_w - self.diag_btn_w) / 2
        self.diag_btn_y = self.diag_h - 2
        self.diag_btn_border_x = 1
        self.diag_btn_color = curses.COLOR_RED
        curses.init_pair( self.diag_btn_color, self.diag_btn_color, curses.COLOR_WHITE)

        # Misc
        self.key = -1
        self.valid_keys = { curses.KEY_UP   : self.process_up, \
                            curses.KEY_DOWN : self.process_down, \
                            curses.KEY_RIGHT: self.process_right, \
                            curses.KEY_LEFT : self.process_left }

    def process_up(self):
        if self.diag_content_pos < len( self.diag_content ) - 1:
            self.diag_content_pos += 1
        
    def process_down(self):
        if self.diag_content_pos:
            self.diag_content_pos -= 1

    def process_right(self):
        if self.diag_btn_select < len( self.diag_btn ) -1 :
            self.diag_btn_select += 1

    def process_left(self):
        if self.diag_btn_select:
            self.diag_btn_select -= 1
    
    def process_dialog(self):

        self.diag_win.keypad(1)
        while True:
            self.key = self.diag_win.getch()
            # Debug
            fieldwin.addnstr(3, 0, str(self.key), fieldw, curses.A_BOLD)
            fieldwin.addnstr(4, 0, str(self.valid_keys.keys()), fieldw, curses.A_BOLD)
            curses.panel.update_panels()
            curses.doupdate()
            
            if self.key == ord('\n'):
                break
            if self.key in self.valid_keys.keys():
                self.valid_keys[ self.key ]()
                self.refresh()

    def add_title(self):
       self.diag_pan.window().addstr( self.diag_title_y, self.diag_title_border_x, \
                                      (self.diag_w - self.diag_title_border_x * 2) * ' ', \
                                      curses.color_pair(self.diag_title_color) )
       self.diag_pan.window().addstr( self.diag_title_y, self.diag_title_x, self.diag_title, \
                                       curses.color_pair(self.diag_title_color) )

    def add_content(self):
        self.diag_content_index = 0
        for self.diag_content_line in self.diag_content[self.diag_content_pos:]:
            if (self.diag_content_index + self.diag_content_pos ) > len(self.diag_content):
                break
            if self.diag_content_index == ( self.diag_h - 3 ): # L/R BORDERS + TITLE + BUTTON (- 1 for ZERO base)
                break
            self.diag_pan.window().addstr(self.diag_content_y + self.diag_content_index, self.diag_content_x, \
                                     self.diag_content_line )
            self.diag_content_index += 1

    def add_buttons(self):
        self.diag_btn = self.diag_btn_orig[:]
        self.diag_btn[ self.diag_btn_select ] = '<' + self.diag_btn[ self.diag_btn_select ] + '>'
        self.diag_btn_text = reduce( lambda x,y: x + ' ' + y, self.diag_btn)
        
        self.diag_pan.window().addstr( self.diag_btn_y, self.diag_btn_border_x, \
                                       (self.diag_w - self.diag_btn_border_x * 2) * ' ', \
                                       curses.color_pair(self.diag_btn_color) )
        self.diag_pan.window().addstr( self.diag_btn_y, self.diag_btn_x, \
                                       self.diag_btn_text, curses.color_pair(self.diag_btn_color) )
        
    def display(self):

        self.add_title()
        self.add_content()
        self.add_buttons()
        
        self.diag_pan.top()
        self.diag_pan.show()
        self.diag_win.box()
        
        curses.panel.update_panels()
        curses.doupdate()

        self.process_dialog()

    def refresh(self):

        # TBD: Need to support only content area refresh (use separate pan)
        self.diag_pan.window().erase()
        self.add_title()
        self.add_content()
        self.add_buttons()
        self.diag_win.box()
        
        curses.panel.update_panels()
        curses.doupdate()
            
if __name__ == '__main__':
    print 'DB Check'

    initialize_curses_vars(True)

#    dialog = test_dialog()
#    dialog.display()

    tab = table_window()
    tab.populate()
    tab.refresh()
    tab.display()
    tab.navigate()
    
    reset_terminal()
    # print '* dialog return *', dialog.diag_btn_select    
    sys.exit(0)
    
    edata = crypto_aes_encrypt_blob( 'this is some text to encrypt', 'my secret key' )
    ddata = crypto_aes_decrypt_blob( edata, 'my secret key' )

    fieldwin.erase()
    fieldwin.addnstr(0,0, edata, fieldw, curses.A_BOLD)
    fieldwin.addnstr(1,0, ddata, fieldw)

    initialize_sqlite_vars()
    
    redraw_display()
    
    reset_terminal()
    
