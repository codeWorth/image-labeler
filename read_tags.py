import struct

SEEK_START = 0
SEEK_CUR = 1
POINTER_TAGS = [b'\x87\x69', b'\x88\x25']

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

def convertValueWithFormat(value, formatNum, endian):
	if formatNum == 7:
		return "NULL"
	elif formatNum == 1 or formatNum == 3 or formatNum == 4:
		return int.from_bytes(value, byteorder=endian, signed=False)
	elif formatNum == 2:
		return value.decode("ascii")
	elif formatNum == 5:
		return (
			int.from_bytes(value[:4], byteorder=endian, signed=False),
			int.from_bytes(value[4:], byteorder=endian, signed=False)
		)
	elif formatNum == 6 or formatNum == 8 or formatNum == 9:
		return int.from_bytes(value, byteorder=endian, signed=True)
	elif formatNum == 10:
		return (
			int.from_bytes(value[:4], byteorder=endian, signed=True),
			int.from_bytes(value[4:], byteorder=endian, signed=True)
		)
	elif formatNum == 11:
		return struct.unpack("f", value)
	elif formatNum == 12:
		return struct.unpack("d", value)
	else:
		print("Invalid format!")
		exit(0)


with open("img_labeled.jpg", "rb") as img:
	print(img.read(4).hex())
	# img.seek(4, SEEK_CUR) # Skip FF and marker (not used)
	print("Data size =", int.from_bytes(img.read(2), byteorder='big', signed=False))
	img.seek(6, SEEK_CUR) # Skip EXIF00 
	offStart = 12

	endianCode = img.read(2)
	if endianCode == b'II':
		endian = "little"
	elif endianCode == b'MM':
		endian = "big"
	else:
		print("INVALID ENDIAN")
		exit(0)

	print("Endianness =", endian)

	img.seek(2, SEEK_CUR) # Skip 0x002A (depending on endianness)
	firstIFDOffset = int.from_bytes(img.read(4), byteorder=endian, signed=False)
	print("Offset to first IFD =", firstIFDOffset)

	firstIFDOffset = 2335

	# Offset is relative to TIFF header start, which begins after EXIF00 ends
	img.seek(firstIFDOffset + offStart, SEEK_START)
	dirEntryCount = int.from_bytes(img.read(2), byteorder=endian, signed=False)
	print("Directory entries =", dirEntryCount)

	# each entry is 12 bytes long
	for i in range(dirEntryCount):
		# Go to correct place in header in case previous header caused a jump to somewhere in the data
		img.seek(offStart + firstIFDOffset + 2 + i*12, SEEK_START)

		tag = img.read(2)
		valFormat = int.from_bytes(img.read(2), byteorder=endian, signed=False)
		components = int.from_bytes(img.read(4), byteorder=endian, signed=False)
		val = img.read(4)

		size = sizeOfFormat(valFormat)
		totalBytes = components * size
		if totalBytes > 4:
			offset = int.from_bytes(val, byteorder=endian, signed=False)
			img.seek(offStart + offset, SEEK_START)
			data = img.read(totalBytes)
			print(str(i+1), "|", tag.hex(), "->", offset, "->", [convertValueWithFormat(data[i*size:i*size+size], valFormat, endian) for i in range(components)])
		else:
			if size == 0:
				size = 4 # if it was undefined format, just send the whole 4 bytes to convert function
			print(str(i+1), "|", tag.hex(), "=", [convertValueWithFormat(val[i*size:i*size+size], valFormat, endian) for i in range(0, 4, size)])

	img.seek(offStart + firstIFDOffset + 2 + dirEntryCount*12, SEEK_START)
	print("Next IFD =", int.from_bytes(img.read(4), byteorder=endian, signed=False))
	