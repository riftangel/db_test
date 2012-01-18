#
# Very Simple Layout Engine
#

import copy

class mcell():

    def __init__(self, pos_x = -1, pos_y = -1, prio = -1, expand = -1, \
                 ctype= -1, size_x = -1, size_y = 1, content = None):
        self.pos_x  = pos_x
        self.pos_y  = pos_y
        self.prio   = prio
        self.expand = expand            # b01 = expand_x, b10 = expand_y
        self.ctype   = ctype
        self.size_x = size_x
        self.size_y = size_y
        self.content = content

    def __repr__(self):
        return 'class_' + str( self.get_pos_xy() )

    def compute_content_size(self):

        if self.content == None:
            return 0, 0,
        sx = sy = 0
        for entity in self.content:
            sx = max( sx, entity.get_size_x())
            sy = max( sy, entity.get_size_y())
        return sx, sy
        
    def recompute_size(self):
        sx, sy = self.compute_content_size()
        return sx, sy
    
    def get_size_x(self):
        sx = self.size_x
        if sx == -1:
            sx, sy = self.recompute_size()
        return sx
    
    def get_size_y(self):
        sy = self.size_y
        if sy == -1:
            sx, sy = self.recompute_size()
        return sy
    
    def get_pos_xy(self):
        return self.pos_x, self.pos_y

    def get_pos_x(self):
        return self.pos_x

    def get_pos_y(self):
        return self.pos_y

    def get_ctype(self):
        return self.ctype

    def get_expand_mode(self):
        return self.expand

    def get_prio(self):
        return self.prio

    def get_content(self):
        return self.content

CTYPE_SIZER = 0
CTYPE_LABEL = 1
CTYPE_INPUT = 2
CTYPE_BTN   = 3

EXPAND_CELL_NONE = 0
EXPAND_CELL_X    = 1
EXPAND_CELL_Y    = 2

# Content Cell ( X, Y, PRIO, EXPAND, TYPE, WIDTH, HEIGHT, None | Attribute_List )
cnt0  = mcell( 0, 0, 0, 0, CTYPE_LABEL, 10, 3, None )
cnt1  = mcell( 0, 1, 0, 0, CTYPE_LABEL, 15, 5, None )
cnt2  = mcell( 0, 0, 0, 0, CTYPE_LABEL, 13, 3, None )
cnt3  = mcell( 0, 0, 0, 0, CTYPE_LABEL, 12, 3, None )
cnt4  = mcell( 0, 0, 0, 0, CTYPE_BTN,   10, 3, None )

# Sizing Cell ( X, Y, PRIO, EXPAND, TYPE, WIDTH, HEIGHT, Content_List )
cell0 = mcell( 0, 0, 0, 0, 0, -1, -1, [cnt0] )
cell1 = mcell( 1, 0, 0, 0, 0, -1, -1, [cnt1] )
cell2 = mcell( 9, 0, 1, 2, 0, -1, -1, [cnt2] )
cell3 = mcell( 0, 1, 0, 1, 0, -1, -1, [cnt3] )
cell4 = mcell( 0, 5, 0, 1, 0, -1, -1, [cnt4] )

cell_def0 = [ cell0 ]
cell_def1 = [ cell1 ]
cell_def2 = [ cell2 ]
cell_def3 = [ cell3 ]
cell_def4 = [ cell4 ]

# Matrix Layout
layout_def = [ cell_def0, cell_def1, cell_def2, cell_def3, cell_def4 ]

#layout_mat = []
#row_s = []
#col_s = []
lm_dx = 0
lm_dy = 0

def adjust_cell_xy( mat, x, y ):

    for ix in range(0, len(mat)):
        for iy in range(0,len(mat[0])):
            if mat[ix][iy] == -1:
                continue
            if mat[ix][iy][1].get_pos_x() == x and mat[ix][iy][1].get_pos_y() == y:
                return mat[ix][iy][0]
            
def compute_layout_matrix( ld ):

    mat = []
    dim_x = 0
    dim_y = 0

    # First compute layout matrix x,y
    for cell in ld:
        # TBD; Handle multiple cell
        xcell = cell[0]
        if xcell.get_pos_x() > dim_x: dim_x = xcell.get_pos_x()
        if xcell.get_pos_y() > dim_y: dim_y = xcell.get_pos_y()

    # Base 0 adjustment
    dim_x += 1
    dim_y += 1
    
    # Two build the layour matrix
    mat = [-1] * dim_x
    for index in range(0, dim_x):
        mat[ index ] = [-1] * dim_y

    # Fill Mat w/o expending cell (just orig)
    for cell in ld:
        # TBD; Handle multiple cell
        xcell = cell[0]
        ix, iy = xcell.get_pos_xy()
        if mat[ ix ] [ iy ] != -1:
            mat[ ix ][ iy ] .append(xcell)
        mat[ ix ] [ iy ] = [xcell]

    # Display Layout Mat
    tcol_s = [0] * dim_x
    trow_s = [0] * dim_y
    display_layout_mat(mat, trow_s, tcol_s)

    # Collapse Matrix before Expand
    # TBD: Make it this optional
    nmat = []
    for ix in range( 0, dim_x):
        tbremove = True
        for iy in range( 0, dim_y):
            if mat[ ix ][ iy ] != -1:
                tbremove = False
        if not tbremove:
            nmat.append(mat[ix])            
    #display_layout_mat(nmat, trow_s, tcol_s)
    mat = copy.deepcopy(nmat)
    dim_x = len(nmat)
    row_offset = 0
    for iy in range( 0, dim_y):
        tbremove = True
        for ix in range( 0, dim_x):
            if mat[ ix ][ iy ] != -1:
                tbremove = False
        if tbremove:
            for ix in range( 0, len(nmat)):
                del(nmat[ix][iy-row_offset])
            row_offset += 1
    mat = nmat
    dim_x = len(nmat)
    dim_y = len(nmat[0])
    display_layout_mat(mat, trow_s, tcol_s)
    # Reset Cell x,y position
    for ix in range( 0, dim_x):
        for iy in range( 0, dim_y):
            if mat[ ix ][ iy ] != -1:
                curr = [[ix,iy]] + mat[ix][iy]
                print curr
                mat[ix][iy] = curr
    print mat
    
    # Expand cell starting w/ the highest PRIO (e.g. 1 for now)
    cprio = 0
    for cprio in (1,0):
        for cell in ld:
            # Sizer Cell always 1st
            xcell = cell[0]
            if xcell.get_ctype() != 0:
                continue
            if xcell.get_prio() != cprio:
                continue
            expand = xcell.get_expand_mode()
            if expand not in (1,2,3):
                continue
            
            ix = xcell.get_pos_x()
            iy = xcell.get_pos_y()
            
            # Find adjutsed cell x,y in collapsed mat (if enabled)
            ix, iy = adjust_cell_xy( mat, ix, iy)
            
            if (expand & 1):
                # Expand X                
                for cx in range(ix, dim_x):
                    if mat[ cx ][ iy ] == -1:
                        ##print '* U ', cx, iy
                        ccell = copy.deepcopy( xcell )
                        ccell.size_x = ccell.size_y = -1
                        ccell.content = None
                        mat[ cx ][ iy ] = [ [cx, iy], ccell ]
            if (expand & 2):
                # Expand Y
                for cy in range(iy, dim_y):
                    if mat[ ix ][ cy ] == -1:
                        ##print '* U ', ix, cy
                        ccell = copy.deepcopy( xcell )
                        ccell.size_x = ccell.size_y = -1
                        ccell.content = None
                        mat[ ix ][ cy ] = [ [ix,cy], ccell ]                

    display_layout_mat(mat, trow_s, tcol_s)

    print mat
    
    # Compute Cell Size
    col_size = [-1] * dim_x
    row_size = [-1] * dim_y

    # ROW_SIZE
    for iy in range(0, dim_y):
        rs = 0
        for ix in range(0, dim_x):
            if type(mat[ix][iy]) != type([]):
                continue
            for cell in mat[ix][iy]:
                if type(cell) == type([]):
                    continue
                rs = max( rs, cell.get_size_y())
        row_size[iy] = rs

    # COL_SIZE
    for ix in range(0, dim_x):
        cs = 0
        for iy in range(0, dim_y):
            if type(mat[ix][iy]) != type([]):
                continue            
            for cell in mat[ix][iy]:
                if type(cell) == type([]):
                    continue                
                cs = max( cs, cell.get_size_x())
        col_size[ix] = cs
     
    return dim_x, dim_y, mat, row_size, col_size

def display_layout_mat( lmat, row_s, col_s ):

    dim_x = len( lmat )
    dim_y = len( lmat[0] )

    print '     ',
    for ix in range(0, dim_x):
        size_text = '<  %3d  >  . ' % col_s[ix]
        print size_text,
    print
    for iy in range(0, dim_y):
        print '%3d' % row_s[iy], ' ',
        for ix in range(0, dim_x):
            if lmat[ix][iy] != -1:
                # TBD: Handle multiple cells
                if type([]) == type(lmat[ix][iy][ 0 ]):
                    cell = lmat[ix][iy][1]
                else:
                    cell = lmat[ix][iy][0]
                cell_text = "(%3d,%3d)" % ( cell.get_pos_x(), cell.get_pos_y() )
            else:
                cell_text = "(udf,udf)"
            print cell_text, ' | ',
        print

def compact_layout( lmat ):
    pass

def adjust_layout_to_panel(lmat, row_s, col_s, adjx, adjy):

    dim_x = len( lmat )
    dim_y = len( lmat[0] )

    # TBD : Only appy to cell marked as expand local cell
    sum_col = 0
    for ix in range(0, dim_x):
        sum_col += col_s[ix]
    for ix in range(0, dim_x):
        col_s[ix] =  ((100.0 / (sum_col * 1.0)) * col_s[ix]) * adjx / 100.0  
        
def main(scrx=80, scry=25):
    
    global lm_x, lm_y
    global layout_mat, row_s, col_s

    lm_x, lm_y, layout_mat, row_s, col_s = compute_layout_matrix( layout_def )
    display_layout_mat( layout_mat, row_s, col_s )
    adjust_layout_to_panel( layout_mat, row_s, col_s, scrx, scry)
    display_layout_mat( layout_mat, row_s, col_s )
    
if __name__ == '__main__':

    main()
