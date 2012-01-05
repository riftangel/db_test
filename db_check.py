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
# Dialog class
# http://docs.python.org/library/curses.html
#
def test_dialog():

    # Compute location in parent window (default main screen window)
    scrh, scrw = scrwin.getmaxyx()
    diag_h = 10
    diag_w = 24
    diag_x = (scrw - diag_w) / 2
    diag_y = (scrh - diag_h) / 2
    
    diag_win = curses.newwin(diag_h, diag_w, diag_y, diag_x)
    diag_pan = curses.panel.new_panel(diag_win)

    diag_pan.top()
    diag_pan.show()

    # Basic Dialog. Title, Message, Buttons
    diag_title = 'Dialog Title'
    diag_title_x = (diag_w - len(diag_title)) / 2  # Best if we don't skip 1 char for border/boxing
    diag_title_y = 1            # skip 1 char for border/boxing
    diag_title_border_x = 1
    color = curses.COLOR_BLUE
    curses.init_pair( color, curses.COLOR_BLUE, curses.COLOR_WHITE)
    diag_pan.window().addstr( diag_title_y, diag_title_border_x, (diag_w - diag_title_border_x * 2) * ' ', \
                              curses.color_pair(color) )
    diag_pan.window().addstr( diag_title_y, diag_title_x, diag_title, curses.color_pair(color) )
    
    curses.panel.update_panels()
    curses.doupdate()

    diag_win.box()
    
    while diag_win.getch() == -1:
        pass
    
if __name__ == '__main__':
    print 'DB Check'

    initialize_curses_vars(True)

    test_dialog()

    reset_terminal()
    sys.exit(0)
    
    edata = crypto_aes_encrypt_blob( 'this is some text to encrypt', 'my secret key' )
    ddata = crypto_aes_decrypt_blob( edata, 'my secret key' )

    fieldwin.erase()
    fieldwin.addnstr(0,0, edata, fieldw, curses.A_BOLD)
    fieldwin.addnstr(1,0, ddata, fieldw)

    initialize_sqlite_vars()
    
    redraw_display()
    
    reset_terminal()
    
