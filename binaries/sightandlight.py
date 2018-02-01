import math,operator,pygame

# Find intersection of RAY & SEGMENT
def getIntersection(ray,segment):

	# RAY in parametric: Point + Delta*T1
	r_px = ray[0][0]
	r_py = ray[0][1]
	r_dx = ray[1][0]-ray[0][0]
	r_dy = ray[1][1]-ray[0][1]

	# SEGMENT in parametric: Point + Delta*T2
	s_px = segment[0][0]
	s_py = segment[0][1]
	s_dx = segment[1][0]-segment[0][0]
	s_dy = segment[1][1]-segment[0][1]

	# Are they parallel? If so, no intersect
	r_mag = math.sqrt(r_dx*r_dx+r_dy*r_dy)
	s_mag = math.sqrt(s_dx*s_dx+s_dy*s_dy)
	if(r_dx/r_mag==s_dx/s_mag) and (r_dy/r_mag==s_dy/s_mag):
		return False # Unit vectors are the same.
	# Are we going to divide by 0 ?
	if((s_dx*r_dy - s_dy*r_dx)==0 or r_dx==0):
		return False

	# SOLVE FOR T1 & T2
	# r_px+r_dx*T1 = s_px+s_dx*T2 && r_py+r_dy*T1 = s_py+s_dy*T2
	# ==> T1 = (s_px+s_dx*T2-r_px)/r_dx = (s_py+s_dy*T2-r_py)/r_dy
	# ==> s_px*r_dy + s_dx*T2*r_dy - r_px*r_dy = s_py*r_dx + s_dy*T2*r_dx - r_py*r_dx
	# ==> T2 = (r_dx*(s_py-r_py) + r_dy*(r_px-s_px))/(s_dx*r_dy - s_dy*r_dx)
	T2 = (r_dx*(s_py-r_py) + r_dy*(r_px-s_px))/(s_dx*r_dy - s_dy*r_dx)
	T1 = (s_px+s_dx*T2-r_px)/r_dx

	# Must be within parametic whatevers for RAY/SEGMENT
	if(T1<0):
		return False
	if(T2<0 or T2>1):
		return False

	# Return the POINT OF INTERSECTION
	return {"point":(r_px+r_dx*T1,r_py+r_dy*T1),"param": T1}

def get_points(collisions,radius):
	points = [radius.topleft, radius.bottomleft, radius.topright, radius.bottomright]
	for collision in collisions:
		if(radius.colliderect(collision.rect)):
			points.extend([collision.rect.topleft,
				collision.rect.topright,
				collision.rect.bottomleft,
				collision.rect.bottomright])
	return points 

def get_segments(collisions,radius):
	segments = [(radius.topleft,radius.topright),
				(radius.bottomleft,radius.bottomright),
				(radius.topleft,radius.bottomleft),
				(radius.topright,radius.bottomright)]
	for collision in collisions:
		if(radius.colliderect(collision.rect)):
			segments.extend([(collision.rect.topleft,collision.rect.topright),
							(collision.rect.bottomleft,collision.rect.bottomright),
							(collision.rect.topleft,collision.rect.bottomleft),
							(collision.rect.topright,collision.rect.bottomright)])
	return segments

def init(sightX,sightY,collisions,radius):
	# Get all unique points
	r = pygame.Rect(sightX-radius/2,sightY-radius/2,radius,radius)
	uniquePoints = get_points(collisions,r)
	segments = get_segments(collisions,r)
	return (uniquePoints,segments)

def getSightPolygon(sightX,sightY,uniquePoints,segments,camera,noCam=False):

	# Get all angles
	uniqueAngles = []
	for uniquePoint in uniquePoints:
		angle = math.atan2(uniquePoint[1]-sightY,uniquePoint[0]-sightX)
		uniquePoint = (uniquePoint[0], uniquePoint[1], angle)
		uniqueAngles.extend([angle-0.00001,angle,angle+0.00001])

	# RAYS IN ALL DIRECTIONS
	intersects = [];
	for angle in uniqueAngles:

		# Calculate dx & dy from angle
		dx = math.cos(angle)
		dy = math.sin(angle)

		# Ray from center of screen to source
		ray = (sightX,sightY),(sightX+dx,sightY+dy)

		# Find CLOSEST intersection
		closestIntersect = False
		for segment in segments:
			intersect = getIntersection(ray,segment)
			if(not intersect):
				continue
			if(not closestIntersect or intersect["param"]<closestIntersect["param"]):
				closestIntersect=intersect

		# Intersect angle
		if(not closestIntersect):
			continue
		closestIntersect["angle"] = angle

		# Add to list of intersects
		intersects.append(closestIntersect)


	# Sort intersects by angle
	intersects = sorted(intersects,key=lambda user: user['angle'])
	sightPoly = []
	for intersect in intersects:
		if noCam == True:
			sightPoly.append((intersect["point"][0],intersect["point"][1]))
		else:
			sightPoly.append((intersect["point"][0]-camera.x,intersect["point"][1]-camera.y))

	# Polygon is intersects, in order of angle
	return sightPoly