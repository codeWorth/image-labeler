import struct
from constants import *
from write_label_newblock import Label, seekLabelsChunk

class ArrayStream:
	def __init__(self, array, cursor=0):
		self.array = array
		self.cursor = cursor
		if cursor >= len(self.array):
			raise ValueError("Cursor position cannot exceed array bounds")

	def read(self, count):
		section = self.array[self.cursor:self.cursor + count]
		self.cursor += count
		return section

if __name__ == "__main__":
	with open("img_mod.jpg", "rb") as img:
		if img.read(2) != JPEG_HEADER:
			print("Not a valid JPEG")
			exit(0)

		for chunk in seekLabelsChunk(img):
			if chunk[:2] == LABEL_MARKER:
				numLabels = struct.unpack(ENDIAN + "H", chunk[4:6])[0]
				chunkStream = ArrayStream(chunk, cursor=6)
				for i in range(numLabels):
					print(Label.labelFromBuffer(chunkStream))
		
