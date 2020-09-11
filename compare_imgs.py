CHUNKS = 4
with open("img.jpg", "rb") as img1, open("img_labeled.jpg", "rb") as img2:
	b1 = img1.read(CHUNKS)
	b2 = img2.read(CHUNKS)

	while b1 != b'' and b2 != b'':
		if b1 != b2:
			print("Failure!")
			# i1 = img1.tell()
			# i2 = img2.tell()
			# img1.seek(0, 0)
			# img2.seek(0, 0)
			# print(img1.read(i1+8).hex())
			# print(img2.read(i2+8).hex())

			img1.seek(0,0)
			img2.seek(0,0)
			print(img1.read(16).hex())
			print(img2.read(16).hex())

			exit(0)

		b1 = img1.read(CHUNKS)
		b2 = img2.read(CHUNKS)

print("Perfect match!")