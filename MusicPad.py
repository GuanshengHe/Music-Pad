# Class for MusicPad used in DSP Lab Project
# Created by Guansheng He @ Nov, 12

from math import cos, pi 
import pyaudio
import struct
import numpy as np
import Tkinter as Tk

# Geometric Parameters
line_distance = 50
pad_width = 9 * line_distance
pad_height = 7 * line_distance

# Audio Parameters
Fs = 8000 #8000
Ta = 0.2 # Decay time (seconds)
f = np.array([261.63, 293.66, 329.63, 349.23, 392, 440, 493.88]) # Frequency (Hz)
BLOCKSIZE = 512 #512

class MusicPad(Tk.Tk):
	
	"""MusicPad"""
	
	def __init__(self):
		
		self.master = Tk.Tk.__init__(self)
		self.pad = Tk.Canvas(self.master, width = pad_width, height = pad_height)
		self.cursor = self.construct_pad()
		self.gain = Tk.DoubleVar()
		self.Btxt = Tk.StringVar()
		self.patterns = []
		self.RUNNING = True
		self.PLAYING = False

		self.create_sliders_buttons()

		self.x = np.zeros((len(f), BLOCKSIZE))
		self.y = np.zeros((len(f), BLOCKSIZE))
		coef = self.getFilterCoefficients(Fs, Ta, f)
		self.b0 = coef[0]
		self.a1 = coef[1]
		self.a2 = coef[2]
		self.p = pyaudio.PyAudio()
		self.stream = self.open_stream()

		self.run()
	
	
	def construct_pad(self):

		for x in range(line_distance, pad_width, line_distance):
			self.pad.create_line(x, 0, x, pad_height, fill="#476042")

		for y in range(line_distance, pad_height, line_distance):
			self.pad.create_line(0, y, pad_width, y, fill = "#476042")

		self.pad.pack(expand = Tk.YES, fill = Tk.BOTH)
		self.pad.bind("<Button-1>", self.pad_click)

		return self.pad.create_line(0, 0, 0, pad_height, fill = 'red')

	
	def create_sliders_buttons(self):

		# Volume slider
		self.gain.set(50)
		Tk.Scale(self.master, label = 'Gain', variable = self.gain,
			from_ = 0, to = 100, orient = Tk.HORIZONTAL).pack(fill = Tk.X)
		
		# Player control
		self.Btxt.set('Play')
		Tk.Button(self.master, textvariable = self.Btxt, command = self.player_control).pack(fill = Tk.X)
		
		# Reset
		Tk.Button(self.master, text = 'Reset', command = self.pad_reset).pack(fill = Tk.X)
		
		# Exit
		Tk.Button(self.master, text = 'Quit', command = self.pad_quit).pack(side = Tk.BOTTOM, fill = Tk.X)


	def getFilterCoefficients(self, Fs, Ta, f):

		r = 0.01**(1.0/(Ta*Fs))
		om = 2.0 * pi * f / Fs
		a1 = -2 * r * np.cos(om)
		a2 = r**2
		b0 = np.sin(om)
		return b0, a1, a2


	def open_stream(self):

		return  self.p.open(
			format = pyaudio.paInt16,
			channels= 1,
			rate = Fs,
			input = True,
			output = True,
			frames_per_buffer = 128)


	def pad_click(self, event):

		for i in range(pad_width-line_distance, -line_distance, -line_distance):
			if i < event.x:
				x1 = i
				break
	
		for i in range(pad_height-line_distance, -line_distance, -line_distance):
			if i < event.y:
				y1 = i
				break

		change = False
		for pattern in self.patterns:

			# Obtain current pattern's coordinates
			c = self.pad.coords(pattern)
			(xp, yp) = (c[0], c[1])
			
			# Same column
			if x1 == xp:

				change = True
				self.pad.delete(pattern)
				self.patterns.remove(pattern)
				
				# Different pattern
				if y1 != yp:
					p = self.pad.create_rectangle(x1, y1, x1+line_distance, pad_height, fill = "green")
					self.patterns.append(p)
				break
				
		# New pattern (new column)
		if not change:
			p = self.pad.create_rectangle(x1, y1, x1+line_distance, pad_height, fill = "green")
			self.patterns.append(p)


	def player_control(self):

		if self.Btxt.get() == 'Pause':
			self.Btxt.set('Play')
		
		else:
			self.Btxt.set('Pause')
		
		self.PLAYING = not self.PLAYING

	
	def pad_reset(self):

		for p in self.patterns:
			self.pad.delete(p)
		self.patterns = []

		x1 = self.pad.coords(self.cursor)[0]
		self.pad.move(self.cursor, -x1, 0)
		self.gain.set(50)

	
	def pad_quit(self):

		print("Quit")
		self.RUNNING = False

	
	def move_cursor(self):

		if self.PLAYING:
			self.pad.tag_raise(self.cursor)
			x = self.pad.coords(self.cursor)[0]
			if x == pad_width:
				self.pad.move(self.cursor, -pad_width, 0)
			self.pad.move(self.cursor, line_distance/5, 0)

	
	def play_patterns(self):
		
		self.x[:, 0] = 0
		
		# Obtain pattern information from self.patterns
		t = self.pad.coords(self.cursor)[0]
		f_idx = -1
		for p in self.patterns:
			c = self.pad.coords(p)
			if t == c[0] + line_distance/5:
				f_idx = int(len(f) - c[1]/line_distance - 1)
		
		if f_idx != -1:
			self.x[f_idx, 0] = 1.0 * self.gain.get() / 100 * (2**15-1)
		
		for i in range(BLOCKSIZE):
				self.y[:,i] = self.b0*self.x[:,i]-self.a1*self.y[:,i-1]-self.a2*self.y[:,i-2]
		
		output = self.y.sum(axis = 0).tolist()
		output_string = struct.pack('h' * BLOCKSIZE, *output)
		self.stream.write(output_string)
		#self.pad.move(self.cursor, line_distance*4/5, 0)
		

	def run(self):

		if self.RUNNING:
			
			if self.PLAYING:
				self.move_cursor()
				self.play_patterns()
			
			self.after(25, self.run)

		else:
			
			self.stream.stop_stream()
			self.stream.close()
			self.p.terminate()
			self.destroy()


mp = MusicPad()
mp.mainloop()