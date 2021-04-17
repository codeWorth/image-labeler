import struct
from constants import *

class Label:
	def __init__(self, x, y, w, h, header, desc):
		if (
			(x < 0 or x >= UNSIGNED_SHORT_MAX) or 
			(y < 0 or y >= UNSIGNED_SHORT_MAX) or 
			(w < 0 or w >= UNSIGNED_SHORT_MAX) or 
			(h < 0 or h >= UNSIGNED_SHORT_MAX)
		):
			print("Invalid label coordinates or size")
			exit(0)

		if not(header.isascii()) or not(desc.isascii()):
			print("Header or description are not ascii")
			exit(0)

		headerLen = len(header)
		descLen = len(desc)
		if headerLen >= 256:
			print("Header can't be more than 255 characters")
			exit(0)
			
		if descLen >= UNSIGNED_SHORT_MAX:
			print("Description can't be more than", UNSIGNED_SHORT_MAX)
			exit(0)

		# I have a feeling that an empty header or description will cause problems
		# with the unpack and pack functions, so for now I'll just put a space there
		if headerLen == 0:
			header = " "
			headerLen = 1

		if descLen == 0:
			desc = " "
			descLen = 1

		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.header = header
		self.desc = desc

	def __str__(self):
		return self.header + ": (" + str(self.x) + "," + str(self.y) + "), " + str(self.w) + "x" + str(self.h)

	def encode(self):
		headerLen = len(self.header)
		descLen = len(self.desc)

		t = ENDIAN + "B5H" + str(headerLen)+"s" + str(descLen)+"s"
		return struct.pack(
			t, 
			headerLen, descLen, 
			self.x, self.y, self.w, self.h,
			self.header.encode("ascii"), self.desc.encode("ascii")
		)

	@staticmethod
	def labelFromBuffer(buffer):
		# hL means header length, dL means description length
		hL, dL = struct.unpack(ENDIAN + "BH", buffer.read(3))

		form = ENDIAN + "4H" + str(hL)+"s" + str(dL)+"s"
		x, y, w, h, hB, dB = struct.unpack(form, buffer.read(8 + hL + dL))
		return Label(x, y, w, h, hB.decode("ascii"), dB.decode("ascii"))

def seekLabelsChunk(buffer):
	marker = b'__'
	while len(marker) == 2:
		marker = buffer.read(2)
		if marker >= b'\xFF\xD0' and marker <= b'\xFF\xD7': # These markers are always followed by zero bytes
			yield marker 
		elif marker == SOS_MARKER: # Once we find start of image data, we're done
			yield SOS_MARKER
			return
		else: # All other markers are followed by block size
			size = int.from_bytes(buffer.read(2), byteorder='big', signed=False) # Always in big endian?
			buffer.seek(-4, SEEK_CUR) # Go back so we can yield the whole chunk at once
			# Original expression was + 4 - 2
			# +4 to account for moving backwards
			# -2 because size includes the bytes that give block length
			yield buffer.read(size + 2) 
			if marker == LABEL_MARKER: # Once we find label data, we're done
				return
				

	raise ValueError("Buffer reached EOF unexpectedly")

if __name__ == "__main__":	
	with open("img_orig.jpg", "rb") as img, open("img_mod.jpg", "wb") as new_img:
		labels = [ # Sample data
			Label(20, 20, 50, 50, "TEST1", "important text goes here"),
			Label(450, 200, 100, 300, "Big MAN", "unimportant text here!"),
			Label(800, 200, 100, 50, "small guy", "new phone")
		] 
		labelBytes = [label.encode() for label in labels]
		totalBytes = 0
		for b in labelBytes:
			totalBytes += len(b)

		if img.read(2) != JPEG_HEADER:
			print("Not a valid JPEG")
			exit(0)
		else:
			new_img.write(JPEG_HEADER)

		new_img.write(LABEL_MARKER)
		new_img.write(struct.pack(ENDIAN + "H", totalBytes + 4)) # Add 2 to include this short, 2 for number of labels short
		new_img.write(struct.pack(ENDIAN + "H", len(labelBytes)))
		for label in labelBytes:
			new_img.write(label)

		for chunk in seekLabelsChunk(img):
			if chunk[:2] != LABEL_MARKER:
				new_img.write(chunk)

		# Once we read the start of image data or pass existing label marker, 
		# just write the rest of the file
		b = img.read(READ_CHUNKS)
		while b != b'':
			new_img.write(b)
			b = img.read(READ_CHUNKS)