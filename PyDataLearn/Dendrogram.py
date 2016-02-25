from PIL import Image, ImageDraw, ImageFont
import random

#GREAT MORE RECURSION I LOVE THIS
def getheight(clust):
	if clust.left == None and clust.right == None: return 1
	return getheight(clust.left) + getheight(clust.right)

def getdepth(clust):
	if clust.left == None and clust.right == None: return 0
	return max(getdepth(clust.left), getdepth(clust.right)) + clust.distance

#this takes a cluster of biclusters and labels corresponding to their ID's and displays them
def drawdendrogram(clust, labels, jpeg='clusters.jpg'):
	h = getheight(clust)*20
	w = 1200
	depth = getdepth(clust)

	#scale depth to width
	scaling = float(w - 150)/depth

	img = Image.new('RGB', (w,h), (255, 255, 255))
	draw = ImageDraw.Draw(img)

	draw.line((0, h/2, 10, h/2), fill=(255, 0, 0))

	drawnode(draw, clust, 10, (h/2), scaling, labels)
	img.save(jpeg, 'JPEG')

def drawnode(draw, clust, x, y, scaling, labels):
	if clust.id < 0:
		h1 = getheight(clust.left)*20
		h2 = getheight(clust.right)*20

		top = y - (h1 + h2)/2
		bottom = y + (h1 + h2)/2

		ll = clust.distance*scaling

		#vertical line from cluster to children
		draw.line((x, top+h1/2, x, bottom - h2/2), fill=(255, 0, 0))

		#horizontal line to left
		draw.line((x, top+h1/2, x + 11, top + h1/2), fill=(255, 0, 0))

		#horizontal line to right
		draw.line((x, bottom  - h2/2, x + 11, bottom - h2/2), fill=(255, 0, 0))

		drawnode(draw, clust.left, x + 11, top + h1/2, scaling, labels)
		drawnode(draw, clust.right, x + 11, bottom - h2/2, scaling, labels)
	else:
		draw.text((x + 5, y - 7), labels[clust.id], (0, 0, 0))\


#this takes a 2D representation and draws it (such as one output from scaledown)
def draw2d(data, labels, jpeg="mds2d.jpg"):
	fnt = ImageFont.truetype('Pillow/Tests/fonts/DejaVuSans.ttf', 20)

	img = Image.new("RGB", (2000, 2000), (255, 255, 255))
	draw = ImageDraw.Draw(img)
	draw.fontmode = "1"
	for i in xrange(len(data)):
		x = (data[i][0] + 0.5)*1000
		y = (data[i][1] + 0.5)*1000
		draw.text((x, y), labels[i], (0, 0, 0), font=fnt)
	img.save(jpeg, 'JPEG')