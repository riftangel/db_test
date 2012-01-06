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
    import curses.ascii
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

#
# Show/Hide All Panel
#
def show_all_panels(really=True):

    if really:
        scrpan.show()
        labelpan.show()
        fieldpan.show()
    else:
        scrpan.hide()
        labelpan.hide()
        fieldpan.hide()
        
    curses.panel.update_panels()
    curses.doupdate()
        
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
        self.tab_h = 40
        self.tab_w = 48
        self.tab_x = (self.scrw - self.tab_w) / 2
        self.tab_y = (self.scrh - self.tab_h) / 2

        self.tab_pos_x = 0
        self.tab_pos_y = 0
        
        # TBD: May be able bypass win/pad
        self.tab_win = curses.newwin(self.tab_h, self.tab_w, self.tab_y, self.tab_x)
        self.tab_pan = curses.panel.new_panel(self.tab_win)

        # TBD: Need to handle border (add to tab_h, tab_w)
        self.tab_pad_border = 1
        
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
        tab = [ [ 'column_name0', 16, type(""), 0,  col0_content ], \
                [ 'column_name1', 12, type(0), 0, col1_content ], \
                [ 'column_name2', 25, type(True), 0, col2_content] ]
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

        # newpad(nlines, ncolumns)
        self.tab_pad = curses.newpad( self.tab_all_row_h , self.tab_all_col_w )
        
    def refresh(self):

        # Start at first/column 0
        self.tab_col_index = 0

        # Color pair is 1 base
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)
        
        # Compute pannel for each column
        pad_col_pos = 0         # TBD: Support border (per column? active ?)
        pad_col_idx = 0
        col_color_index = 1
        for col_def in self.tab_def:
            pad_row_pos = 0
            col_width = col_def[1]
            col_pad  = col_width * ' '            
            col_text = col_def[0] + col_pad
            self.tab_pad.addnstr(pad_row_pos, pad_col_pos, col_text, col_width, \
                                 curses.color_pair(col_color_index) )
            for row_data in col_def[4]:                
                pad_row_pos += 1
                row_selected = 0
                if pad_row_pos == self.tab_pos_y and pad_col_idx == self.tab_pos_x:
                    row_selected = curses.A_BOLD
                self.tab_pad.addnstr(pad_row_pos, pad_col_pos, str(row_data)+col_pad, col_width, \
                                     curses.color_pair(col_color_index) + row_selected)                
            pad_col_pos += col_width
            col_color_index +=1
            pad_col_idx += 1

        # pad.refresh( orig_row, orig_col, min_row, min_col, max_row, max_col )
        self.tab_pad.refresh( 0, 0, self.tab_y, self.tab_x, \
                              self.tab_y+self.tab_h, self.tab_x+self.tab_w )
        
    def display(self):
        self.refresh()

    # Handle key functions
    def process_up(self):
        if self.tab_pos_y:
            self.tab_pos_y -= 1
        
    def process_down(self):
        self.tab_pos_y += 1

    def process_right(self):
        self.tab_pos_x += 1

    def process_left(self):
        if self.tab_pos_x:
            self.tab_pos_x -= 1
            
    def navigate(self):
        
        self.tab_pad.keypad(1)
        self.key = -1
        self.valid_keys = { curses.KEY_UP   : self.process_up, \
                            curses.KEY_DOWN : self.process_down, \
                            curses.KEY_RIGHT: self.process_right, \
                            curses.KEY_LEFT : self.process_left }        
        while True:
            self.key = self.tab_pad.getch()
            if self.key != -1:
                # Debug
                fieldwin.addstr(3, 0, 'key : '+str(self.key)+'   ', curses.A_BOLD)
                curses.panel.update_panels()
                curses.doupdate()
            if self.key == ord('\n'):
                break
            if self.key in self.valid_keys.keys():
                self.valid_keys[ self.key ]()
                self.refresh()
            
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

#
# Forms
#

#
# Basic Password Window
# Only ASCII characters (32-126) allowed for now
# Basic ^H/BS/DEL(ETE) key support
#
class password_window():

    def __init__(self, x, y, width):
        self.win_x = x
        self.win_y = y
        self.win_w = width
        self.passwd = bytearray(' ' * (self.win_w - 2))
        self.show_passwd = False
        self.inkey = -1
        
    def display(self):
        self.win = curses.newwin( 3, self.win_w, self.win_y,self.win_x)
        self.win.box()
        self.win.move(1,1)
        self.win.keypad(1)
        curses.doupdate()

    def refresh(self):
        self.win.box()
        if self.inkey != -1:
            self.win.addstr(0,0,str(self.inkey))  
        if self.show_passwd:
            self.pwd_str = str(self.passwd)[:self.cur_pos] + ' ' * self.win_w
        else:
            self.pwd_str = self.cur_pos * '*' + ' ' * self.win_w
        self.win.addnstr(1,1,self.pwd_str, self.win_w-2)
        self.win.move(1,self.cur_pos+1)
        
    def getpwd(self,show_passwd=False):
        self.show_passwd = show_passwd
        inkey = 0
        self.cur_pos = 0
        while True:
            self.inkey = inkey = self.win.getch()
            if inkey in (curses.ascii.BS, curses.KEY_BACKSPACE,curses.KEY_DC,curses.ascii.DEL):
                self.passwd[self.cur_pos] = ' '
                if self.cur_pos: self.cur_pos -= 1
                self.refresh()
                continue
            if inkey == ord('\n'):
                break
            if self.cur_pos == self.win_w - 2 - 1:
                self.refresh()
                continue
            if not (inkey >= 32 and inkey <= 126):
                self.refresh()
                continue
            self.passwd[self.cur_pos] = chr(inkey&0xFF)
            self.cur_pos += 1
            self.refresh()
        return str(self.passwd)[:self.cur_pos]

#
# Ask for Meta PWD before starting the App
#
def ask_meta_pwd(meta_hello='Please enter Meta Password'):

    scrh, scrw = scrwin.getmaxyx()
    pww = 32
    pwh = 3
    pwx = (scrw - pww) / 2
    pwy = (scrh - pwh) / 2

    show_all_panels(really=False)
    scrwin.clear()
    win = curses.newwin(1, pww, pwy-2,pwx)
    panel = curses.panel.new_panel(win)
    panel.top()
    panel.show()
    pad = (((pww-2) - len(meta_hello))/2)*' '
    win.addnstr(0,0,meta_hello+pad,pww-2)
    curses.panel.update_panels()
    curses.doupdate()
    
    pww = password_window(pwx,pwy,pww)
    pww.display()
    pwd = pww.getpwd()
    
if __name__ == '__main__':
    print 'DB Check'

    initialize_curses_vars(True)
#
# Meta Pwd
#
    ask_meta_pwd()
    
# dialog = test_dialog()
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
    
