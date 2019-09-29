"""Starfield demo for the card10 badge
Copyright (C) 2019 Frank Abelbeck <frank.abelbeck@googlemail.com>

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
n_stars     = 50   # number of concurrently displayed stars
warp        = 4    # initial warp factor; can be increased/decreased with the bottom right/left buttons
                   #   the warp factor describes how fast the stars are moving
                   #   speed along z dimension: z = z - 2 * warp ** 2 (per frame)
warp_target = 4    # target value for warp speed factor; needed for smooth step-up/step-down
warp_step   = 0.2  # when changing the warp factor, this describes how fast a new target value is reached
d_warp      = 0    # currently applied warp factor step size
shading     = 255  # colour of stars is white, scaled down to black with distance
                   #   r = g = b = 255 - int(shading*z/z_max)
                   #   shading=0: no scaling
		   #   shading=127: stars at z_max are grey
		   #   shading=255: stars at z_max are black (no pop-up)
WIDTH       = 160  # screen width [px]
HEIGHT      = 80   # screen height [px]
buttonState = 0    # button state
toremove    = []   # list of star indices marked for removal
if __name__ == "__main__":
	# initialise starfield with stars at random positions, sorted back to front
	starfield = [[urandom.randint(-x_max,x_max),urandom.randint(-y_max,y_max),z,-1,-1] for z in sorted([urandom.randint(0,z_max) for i in range(0,n_stars)],reverse=True)]
	# indefinite loop
	while True:
		# take cycle start time
		t0 = utime.time_ms()
		# read button states, process changes, save state for next cycle
		btns = buttons.read(buttons.BOTTOM_LEFT | buttons.BOTTOM_RIGHT)
		if btns & buttons.BOTTOM_LEFT == 0 and buttonState & buttons.BOTTOM_LEFT != 0:
			# reduce warp speed (bottom left button, falling edge)
			warp_target = max(int(warp) - 1,0)
			if warp_target < int(warp):
				d_warp = -warp_step
			else:
				d_warp = 0
		elif btns & buttons.BOTTOM_RIGHT == 0 and buttonState & buttons.BOTTOM_RIGHT != 0:
			# increase warp speed (bottom right button, falling edge)
			warp_target = min(int(warp) + 1,9)
			if warp_target > int(warp):
				d_warp = +warp_step
			else:
				d_warp = 0
		buttonState = btns
		# calculate z stepping based on warp factor
		z_step = 2 * warp ** 2
		# update warp factor
		warp = warp + d_warp
		if d_warp > 0 and warp >= warp_target or d_warp < 0 and warp <= warp_target:
			# if target warp factor is reached, set new integer factor and stop stepping
			warp = warp_target
			d_warp = 0
		# iterate over starfield...
		with display.open() as d:
			d.clear()
			# replace obsolete stars
			for i in toremove:
				starfield[i] = [urandom.randint(-x_max,x_max),urandom.randint(-y_max,y_max),z_max,-1,-1]
			# process all stars
			toremove = []
			for i,(x,y,z,sxold,syold) in enumerate(starfield):
				# move star one step closer in z-direction
				if z <= z_step:
					# z underflow: mark star
					toremove.append(i)
				starfield[i][2] = z - z_step
				# draw star at new position
				sx = int(WIDTH/2 + l_focal*x/z)
				sy = int(HEIGHT/2 + l_focal*y/z)
				if sx >= 0 and sx < WIDTH and sy >= 0 and sy < HEIGHT:
					# star in view: render it
					c = 255 - int(shading*z/z_max)
					if sxold >= 0 and syold >= 0:
						# previous position available: draw line
						d.line(sx,sy,sxold,syold,col=(c,c,c))
						if d_warp == 0:
							# only save old screen coordinates if warp factor is constant
							starfield[i][3] = sx
							starfield[i][4] = sy
					else:
						# fresh star: draw pixel and store screen coordinates
						d.pixel(sx,sy,col=(c,c,c))
						starfield[i][3] = sx
						starfield[i][4] = sy
				else:
					# star out of view: remove, create a new one
					toremove.append(i)
			# print additional info and update display
			dt = utime.time_ms() - t0
			try:
				fps = int(1000 / dt)
			except ZeroDivisionError:
				fps = -1
			d.print("warp {:.1f}".format(warp),fg=(192,192,192),posx=0,posy=0,font=0)
			d.print("{}* {}fps".format(n_stars,fps),fg=(192,192,192),posx=0,posy=70,font=0)
			d.update()
		# sleep only if there is time left in the cycle
		if dt < cycletime:
			utime.sleep_ms(cycletime-dt)
