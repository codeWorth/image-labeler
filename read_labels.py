import struct
from write_labels import decodeLabel, Label

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

SEEK_START = 0
SEEK_CUR = 1
LABEL_EXIF_TAG = b'\x44\x44'

with open("img_labeled.jpg", "rb") as img:
	img.seek(12, SEEK_CUR) # Skip FF, marker, data size, and EXIF00 
	offStart = 12

	endianCode = img.read(2)
	if endianCode == b'II':
		endian = "little"
	elif endianCode == b'MM':
		endian = "big"
	else:
		print("INVALID ENDIAN")
		exit(0)

	img.seek(2, SEEK_CUR) # Skip 0x002A (depending on endianness)
	firstIFDOffset = int.from_bytes(img.read(4), byteorder=endian, signed=False)

	# Offset is relative to TIFF header start, which begins after EXIF00 ends
	img.seek(firstIFDOffset + offStart, SEEK_START)
	dirEntryCount = int.from_bytes(img.read(2), byteorder=endian, signed=False)

	# each entry is 12 bytes long
	for i in range(dirEntryCount):
		# Go to next directory header
		img.seek(offStart + firstIFDOffset + 2 + i*12, SEEK_START)

		tag = img.read(2)
		if tag != LABEL_EXIF_TAG:
			continue

		img.seek(6, SEEK_CUR) # Skip data type and # of components
		labelLocation = int.from_bytes(img.read(4), byteorder=endian, signed=False)
		img.seek(offStart + labelLocation, SEEK_START) # go to labels' data

		numLabels = int.from_bytes(img.read(2), byteorder=endian, signed=False)
		img.seek(2, SEEK_CUR) # Skip size of upcoming data

		labels = []
		for i in range(numLabels):
			labels.append(decodeLabel(img, endian))

		print([str(label) for label in labels])