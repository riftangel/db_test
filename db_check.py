#
# DB Check
#
from Crypto.Cipher import AES
import sqlite3
from struct import *
import sys

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

    curses.doupdate()

# Init curses and bail-out if error
try:
    import curses
    import curses.panel
    
    scrwin = curses.initscr()
    curses.noecho()
    curses.cbreak()
except:
    print 'Looks like you dont have the curses python module on your system.'
    print 'On Windows use the Cygwin port of python instead of native python port.'
    sys.exit(-1)

# Initialize SCR globals
scrh, scrw = scrwin.getmaxyx()
scrpan = curses.panel.new_panel(scrwin)
labelh, labelw, labely, labelx = scrh - 2, 9, 1, 2
labelwin = curses.newwin(labelh, labelw, labely, labelx)
labelpan = curses.panel.new_panel(labelwin)
fieldh, fieldw, fieldy, fieldx = scrh - 2, scrw - 2 - labelw - 3, 1, labelw + 3
fieldwin = curses.newwin(fieldh, fieldw, fieldy, fieldx)
fieldpan = curses.panel.new_panel(fieldwin)
prepare_display()

# Make sure to reset terminal to original state
# When curses wrapper is used this is not required.
def reset_terminal():
    curses.nocbreak()
    curses.echo()
    curses.endwin()
        
if __name__ == '__main__':
    print 'DB Check'

    edata = crypto_aes_encrypt_blob( 'this is some text to encrypt', 'my secret key' )
    ddata = crypto_aes_decrypt_blob( edata, 'my secret key' )
    
    print edata
    print ddata

    reset_terminal()
    
