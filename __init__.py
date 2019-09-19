"""Starfield demo for the card10 badge
Copyright (C) 2019 Frank Abelbeck <frank@abelbck.de>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import display # needed to draw something to the screen
import utime   # needed for timing and sleeping
import urandom # needed for random creation of new stars
import buttons # needed for button event processing

cycletime   = 40   # how long should one rendering cycle (frame) take at most [ms]
l_focal     = 40   # focal length; smaller: wider field of view; larger: narrower field of view
z_max       = 1000 # starfield volume, z dimension: 0..z_max
x_max       = 1000 # starfield volume, x dimension: -x_max..x_max
y_max       = 1000 # starfield volume, y dimension: -y_max..y_max
n_stars     = 50   # number of concurrently displayed stars inside the starfield volume
warp        = 4    # initial warp factor; can be increased/decreased with the bottom right/left buttons
                   #   the warp factor describes how fast the stars are moving
                   #   speed along z dimension: z = z - 2 * warp ** 2 (per frame)
shading     = 255  # colour of stars is white, scaled down to black with distance
                   #   r = g = b = 255 - int(shading*z/z_max)
                   #   shading=0: no scaling
		   #   shading=127: stars at z_max are grey
		   #   shading=255: stars at z_max are black
WIDTH       = 160  # screen width [px]
HEIGHT      = 80   # screen height [px]
buttonState = 0    # button state
boolInfo    = True # show information on screen? (can be toggled with top right button)
loadbuffer  = []   # used for timing (moving average filter)
n_loadmavg  = 32   # number of cycle timing values (moving average filter)
if __name__ == "__main__":
	# initialise starfield with stars at random positions
	starfield = [[urandom.randint(-x_max,x_max),urandom.randint(-y_max,y_max),z,-1,-1] for z in sorted([urandom.randint(0,z_max) for i in range(0,n_stars)],reverse=True)]
	# indefinite loop
	while True:
		# take cycle start time
		t0 = utime.time_ms()
		# read button states, process changes, save state for next cycle
		btns = buttons.read(buttons.BOTTOM_LEFT | buttons.BOTTOM_RIGHT | buttons.TOP_RIGHT)
		if btns & buttons.BOTTOM_LEFT == 0 and buttonState & buttons.BOTTOM_LEFT != 0:
			# reduce warp speed (bottom left button, falling edge)
			warp = max(warp - 1,0)
		elif btns & buttons.BOTTOM_RIGHT == 0 and buttonState & buttons.BOTTOM_RIGHT != 0:
			# increase warp speed (bottom right button, falling edge)
			warp = min(warp + 1,9)
		elif btns & buttons.TOP_RIGHT == 0 and buttonState & buttons.TOP_RIGHT != 0:
			# toggle debug info (top right button, falling edge)
			boolInfo = not boolInfo
		buttonState = btns
		# calculate z stepping based on warp factor
		z_step = 2 * warp ** 2
		# iterate over starfield...
		with display.open() as d:
			if btns & buttons.BOTTOM_RIGHT == 0 and btns & buttons.BOTTOM_LEFT == 0:
				# clear screen only if no warp buttons are held down
				d.clear()
			for i,(x,y,z,sxold,syold) in enumerate(starfield):
				# step 1: move star one step closer in z-direction
				z = z - z_step
				if z <= 0:
					# z underflow: reset z, create new x/y coordinates
					del starfield[i]
					x = urandom.randint(-x_max,x_max)
					y = urandom.randint(-y_max,y_max)
					z = z_max
					sxold = -1
					syold = -1
					starfield.insert(0,[x,y,z,sxold,syold])
				else:
					starfield[i][2] = z
				# step 2: draw star at new position
				sx = int(WIDTH/2 + l_focal*x/z)
				sy = int(HEIGHT/2 + l_focal*y/z)
				if sx >= 0 and sx < WIDTH and sy >= 0 and sy < HEIGHT:
					c = 255 - int(shading*z/z_max)
					if sxold >= 0 and syold >= 0:
						d.line(sx,sy,sxold,syold,col=(c,c,c))
					else:
						d.pixel(sx,sy,col=(c,c,c))
				starfield[i][3] = sx
				starfield[i][4] = sy
			# take cycle stop time and store in load buffer; remove oldest entries to keep a constant buffer size
			loadbuffer.append(utime.time_ms()-t0)
			while len(loadbuffer) > n_loadmavg: loadbuffer.pop(0)
			# finally, redraw, sleep and repeat; print additional info if activated
			if boolInfo:
				# calculate moving average of the load buffer and print information
				cycleload = int(100 * (sum(loadbuffer) / len(loadbuffer)) / cycletime)
				d.print("warp {}".format(warp),fg=(192,192,192),posx=0,posy=0,font=0)
				d.print("{}* load {}".format(n_stars,cycleload),fg=(192,192,192),posx=0,posy=70,font=0)
			d.update()
		# sleep only if there is time cycleload
		utime.sleep_ms(cycletime-loadbuffer[-1])
