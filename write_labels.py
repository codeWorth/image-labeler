import struct

# IMPORTANT:
# This program will potentially break Maker Notes exif data!
# This is because Maker Notes are proprietary, so I can't go through
# and update the pointers when I insert data

# Header is:
# 1. Number of labels, unsigned short
# 2. Total size of upcoming data in bytes, unsigned short
#
# Each label is:
# 1. Header string length, byte
# 2. Description string length, short
# 3. x position, unsigned short
# 4. y position, unsigned short
# 5. x width, unsigned short
# 6. y width, unsigned short
# 7. Label header, ascii char string
# 8. Label description, ascii char string

EXIF_TAG = b'\x44\x44' # Currently unused tag, idk if this is good practice!
SEEK_START = 0
SEEK_CUR = 1
UNSIGNED_SHORT_MAX = 65536
POINTER_TAGS = [b'\x87\x69', b'\x88\x25']
UNSIGNED_SHORT_FORMAT = 4
READ_CHUNKS = 65536

def sizeOfFormat(format_):
	if format_ == 7:
		return 0
	elif format_ == 1 or format_ == 2 or format_ == 6:
		return 1
	elif format_ == 3 or format_ == 8:
		return 2
	elif format_ == 4 or format_ == 9 or format_ == 11:
		return 4
	elif format_ == 5 or format_ == 10 or format_ == 12:
		return 8
	else:
		print("Invalid format!")
		exit(0)

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

def encodeLabel(label, endian):
	headerLen = len(label.header)
	descLen = len(label.desc)

	if endian == "little":
		t = "<B5H" + str(headerLen)+"s" + str(descLen)+"s"
	elif endian == "big":
		t = ">B5H" + str(headerLen)+"s" + str(descLen)+"s"
	else:
		print("Invalid endianness")
		exit(0)

	return struct.pack(
		t, 
		headerLen, descLen, 
		label.x, label.y, label.w, label.h,
		label.header.encode("ascii"), label.desc.encode("ascii")
	)

def decodeLabel(buffer, endian):
	if endian == "little":
		t = "<"
	elif endian == "big":
		t = ">"
	else:
		print("Invalid endianness")
		exit(0)

	# hL means header length, dL means description length
	hL, dL = struct.unpack(t + "BH", buffer.read(3))

	form = t + "4H" + str(hL)+"s" + str(dL)+"s"
	x, y, w, h, hB, dB = struct.unpack(form, buffer.read(8 + hL + dL))
	return Label(x, y, w, h, hB.decode("ascii"), dB.decode("ascii"))

if __name__ == "__main__":
	labels = [
		Label(20, 20, 50, 50, "TEST1", "important text goes here"),
		Label(450, 200, 100, 300, "Big MAN", "unimportant text here!"),
		Label(800, 200, 100, 50, "small guy", "new phone")
	]

	ifdOffsets = []
	offStart = 12
	endian = "little"
	arrow = "<"
	hadOldLabels = False
	oldLabelsLocation = 0
	newLabelsLocation = 0
	oldLabelsSize = 0
	newLabelsSize = 0

	with open("img_orig.jpg", "rb") as img, open("img_labeled.jpg", "wb") as new_img:
		img.seek(4, SEEK_CUR) # Skip FF and marker (not used)
		dataSize = int.from_bytes(img.read(2), byteorder='big', signed=False)
		img.seek(6, SEEK_CUR) # Skip EXIF00 
		
		endianCode = img.read(2)
		if endianCode == b'II':
			endian = "little"
			arrow = "<"
		elif endianCode == b'MM':
			endian = "big"
			arrow = ">"
		else:
			print("INVALID ENDIAN")
			exit(0)
		
		labelBytes = [encodeLabel(label, endian) for label in labels]
		newLabelsSize = 4 # 2 shorts in header
		for lb in labelBytes:
			newLabelsSize += len(lb)

		img.seek(2, SEEK_CUR) # Skip 0x002A (depending on endianness)
		firstIFDOffset = int.from_bytes(img.read(4), byteorder=endian, signed=False)
		# Offset is relative to TIFF header start, which begins after EXIF00 ends
		img.seek(firstIFDOffset + offStart, SEEK_START)
		dirEntryCount = int.from_bytes(img.read(2), byteorder=endian, signed=False)

		pointerEntries = {}
		for i in range(dirEntryCount):
			# Go to correct place in header, each entry is 12 bytes long
			img.seek(offStart + firstIFDOffset + 2 + i*12, SEEK_START)

			tag = img.read(2)
			if tag == EXIF_TAG:
				img.seek(6, SEEK_CUR) # skip format and components
				oldLabelsLocation = int.from_bytes(img.read(4), byteorder=endian, signed=False)
				img.seek(offStart + oldLabelsLocation, SEEK_START) # Go to labels data
				img.seek(2, SEEK_CUR) # Skip # of labels
				oldLabelsSize = int.from_bytes(img.read(2), byteorder=endian, signed=False)
				hadOldLabels = True

			else:
				valFormat = int.from_bytes(img.read(2), byteorder=endian, signed=False)
				components = int.from_bytes(img.read(4), byteorder=endian, signed=False)
				size = sizeOfFormat(valFormat)
				totalBytes = components * size
				inPT = (tag in POINTER_TAGS)	
				if inPT or totalBytes > 4: # if this header entry is a pointer, save it for later
					pointerEntries[str(i)] = [inPT, int.from_bytes(img.read(4), byteorder=endian, signed=False)]

		# This might not be needed, just makes sure we're in the right place at the end
		img.seek(offStart + firstIFDOffset + 2 + dirEntryCount*12, SEEK_START)
		nextIFD = int.from_bytes(img.read(4), byteorder=endian, signed=False)

		dataSize = dataSize - oldLabelsSize + newLabelsSize
		newNextIFD = nextIFD - oldLabelsSize + newLabelsSize
		if hadOldLabels: 
			newLabelsLocation = oldLabelsLocation
			for key in pointerEntries:
				if pointerEntries[key][1] > oldLabelsLocation:
					pointerEntries[key][1] = pointerEntries[key][1] - oldLabelsSize + newLabelsSize
					if pointerEntries[key][0]:
						ifdOffsets.append(pointerEntries[key][1])

		else:
			# +12 for header entry that will be inserted
			# substract offStart because nextIFD is relative to file start, but label location should be relative to IFD start
			newLabelsLocation = nextIFD + 12 - offStart 
			dataSize += 12
			newNextIFD += 12
			for key in pointerEntries:
				pointerEntries[key][1] += 12
				if pointerEntries[key][0]:
						ifdOffsets.append(pointerEntries[key][1])
		

		# Copy data to other buffer now ---
		img.seek(0, SEEK_START)
		b = img.read(4)
		new_img.write(b)

		img.seek(2, SEEK_CUR)
		new_img.write(struct.pack(arrow + "H", dataSize))

		b = img.read(firstIFDOffset + offStart - 6)
		new_img.write(b) # write until number of directory headers

		img.seek(2, SEEK_CUR)
		if hadOldLabels:
			new_img.write(struct.pack(arrow + "H", dirEntryCount))
		else:
			new_img.write(struct.pack(arrow + "H", dirEntryCount+1))
		
		for i in range(dirEntryCount):
			if str(i) in pointerEntries:	
				b = img.read(8)
				new_img.write(b)
				img.seek(4, SEEK_CUR)
				loc = pointerEntries[str(i)][1]
				new_img.write(struct.pack(arrow + "L", loc))
			else:
				b = img.read(12)
				new_img.write(b)
				
		if not(hadOldLabels):
			header = struct.pack(arrow + "2sH2L", EXIF_TAG, UNSIGNED_SHORT_FORMAT, 1, newLabelsLocation)
			new_img.write(header)

		img.seek(4, SEEK_CUR)
		new_img.write(struct.pack(arrow + "L", newNextIFD))

		if hadOldLabels:
			b = img.read(oldLabelsLocation - img.tell() + offStart)
		else:
			b = img.read(nextIFD - img.tell())
		new_img.write(b) # write all data before labels

		img.seek(oldLabelsSize, SEEK_CUR) # skip over old labels
		new_img.write(struct.pack(arrow + "2H", len(labelBytes), newLabelsSize))
		for lb in labelBytes:
			new_img.write(lb)

		b = img.read(READ_CHUNKS)
		while b != b'': # write the rest of the file
			new_img.write(b)
			b = img.read(READ_CHUNKS)

	with open("img_labeled.jpg", "r+b") as new_img:
		while len(ifdOffsets) > 0:
			ifdOffset = ifdOffsets.pop()
			if ifdOffset < newLabelsLocation and hadOldLabels:
				continue

			new_img.seek(ifdOffset + offStart, SEEK_START)
			dirEntryCount = int.from_bytes(new_img.read(2), byteorder=endian, signed=False)

			for i in range(dirEntryCount):
				new_img.seek(offStart + ifdOffset + 2 + i*12, SEEK_START)

				tag = new_img.read(2)
				valFormat = int.from_bytes(new_img.read(2), byteorder=endian, signed=False)
				components = int.from_bytes(new_img.read(4), byteorder=endian, signed=False)
				size = sizeOfFormat(valFormat)
				totalBytes = components * size
				inPT = (tag in POINTER_TAGS)	
				if inPT or totalBytes > 4: # if this header entry is a pointer
					loc = int.from_bytes(new_img.read(4), byteorder=endian, signed=False)
					if ifdOffset > newLabelsLocation:
						loc = loc - oldLabelsSize + newLabelsSize
					if not(hadOldLabels):
						loc += 12

					new_img.seek(offStart + ifdOffset + 10 + i*12, SEEK_START)
					new_img.write(struct.pack(arrow + "L", loc)) # update pointer to be correct
					if inPT:
						ifdOffsets.append(loc)
