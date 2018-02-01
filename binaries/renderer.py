#import pygame module and other usefull modules
import os, pygame, sys, random, math

from pygame.locals import *

#import tmx file reader
from pytmx import *
from pytmx.util_pygame import load_pygame

from sightandlight import *
from sprites import *
from Astar import a_star_search

#Colors
black = (0,0,0)
white = (255,255,255)
red = (255,0,0)
green = (0,255,0)

All_collision_list = pygame.sprite.Group()

"""
__________________________________________________________________________________________________________

THIS FILE CONTAIN THE CLASSES LISTED BELOW:
-Screen 
-Camera
-Bbox
-TiledRenderer
-Renderer
___________________________________________________________________________________________________________
"""

"""
Initialise screen object
"""
class Screen ():
	def __init__ (self):
		self.width = 1920 # width of the program's window, in pixels
		self.height = 1080 # height in pixels
		
		self.minZoom = 0.8
		self.maxZoom = 1
		self.zoom = 1
		self.zoomIndex = 10
		self.xzoom = (self.width - (self.width*self.zoom))/2
		self.yzoom = (self.width - (self.width*self.zoom))/2
		self.half_width = int(self.width / 2)
		self.half_height = int(self.height / 2)

	def update (self):
		self.xzoom = (self.width - (self.width*self.zoom))/2
		self.yzoom = (self.width - (self.width*self.zoom))/2

	def display (self):
		#Set up the windows
		self.gameArea = pygame.display.set_mode((self.width,self.height),FULLSCREEN)
		pygame.display.set_caption('WORK IN PROGRESS')

"""
Initialise and update camera object
"""
class Camera ():

	def __init__ (self):
		
		# movement propreties
		self.movement = {'left': False,'right': False, 'up': False, 'down': False}
		self.movements = False

		self.x = 0
		self.y = 0
		self.oldPos = (0,0)
		self.normalSpeed = 10
		self.speed = self.normalSpeed
		self.on_border = False
		self.target = None
		self.oldZoom = 1

	def update (self,screen,delay,grid):
		
		if self.movement['left'] or self.movement['right'] or self.movement['up'] or self.movement['down']:
			self.movements = True
			self.target = None
			self.speed = self.normalSpeed
		else:
			self.movements = False

		self.oldPos = (self.x,self.y)
		if self.target == None or self.movements:
			self.move(screen,delay,grid)		
		else:
			self.lock_on_target(screen,delay,grid)



	def move (self,screen,delay,grid):
		# handle movement and call bbox handling 
		for i in range(self.speed + int((self.speed*delay))):
			if self.movement['left']:
				self.x -= 1
			if self.movement['right']:
				self.x += 1

			if self.movement['up']:
				self.y -= 1
			if self.movement['down']:
				self.y += 1

		self.adjust_to_limits(screen,grid)

	def lock_on_target(self,screen,delay,grid):

		for i in range(self.speed + int((self.speed*delay))):
			camCenter = (self.x+screen.width/2,self.y+screen.height/2)
			(dx,dy) = (self.target.center[0]-camCenter[0],self.target.center[1]-camCenter[1])
			
			if abs(dx) <= 0 and abs(dy) <= 0 and self.target.old_pos == self.target.center:
				self.target = None
				self.speed = self.normalSpeed
				return

			if abs(dx) <= 0 and abs(dy) <= 0 and self.target.old_pos != self.target.center:
				self.speed = self.target.speed-(self.target.speed//4)
			else:
				if dx < 0:
					self.x -= 1
				if dx > 0:
					self.x += 1
				if dy < 0:
					self.y -= 1
				if dy > 0:
					self.y += 1

		camCenter = (self.x+screen.width/2,self.y+screen.height/2)
		(dx,dy) = (self.target.center[0]-camCenter[0],self.target.center[1]-camCenter[1])

		self.on_border = self.adjust_to_limits(screen,grid)
		if ((self.on_border == 3) or (self.on_border == 1 and abs(dy) <= 0) or (self.on_border == 2 and abs(dx) <= 0)) and self.target.old_pos == self.target.center:
			self.target = None
			self.speed = self.normalSpeed
			return
		if ((self.on_border == 3) or (self.on_border == 1 and abs(dy) <= 0) or (self.on_border == 2 and abs(dx) <= 0)) and self.target.old_pos != self.target.center:
			self.speed = self.target.speed-(self.target.speed//4)

	def adjust_to_limits(self,screen,grid):
		r1 = None
		r2 = None
		if self.x <= -screen.xzoom:
			self.x = -screen.xzoom
			r1 = 1
		if self.y <= -screen.yzoom:
			self.y = -screen.yzoom
			r2 = 2

		lowerLimit = (grid.width*grid.nodeSize*(abs(2 - screen.zoom)),grid.height*grid.nodeSize*(abs(2 - screen.zoom)))
		if self.x + screen.width >= lowerLimit[0] - screen.xzoom:
			self.x = lowerLimit[0] - screen.width - screen.xzoom
			r1 = 1
		if self.y + screen.height >= lowerLimit[1] - screen.yzoom:
			self.y = lowerLimit[1] - screen.height - screen.yzoom
			r2 = 2
		if r1!=None and r2!=None:
			return 3
		elif r1!=None:
			return r1
		else:
			return r2

"""
Handle men colisions and movements
"""
class Bbox():
	#def __init__(self):
	def load(self,r):
		for layer in r.renderer.tmx_data.layers:
			if isinstance(layer, TiledObjectGroup):
				if layer.properties['Boundaries'] == 'True':
					for obj in layer:
						from sprites import Collision
						collision = Collision(obj.width*2,obj.height*2,obj.x*2,obj.y*2)
						All_collision_list.add(collision)

"""
Map renderer tools from Tiled
"""
class TiledRenderer(object):
	"""
	Super simple way to render a tiled map
	"""
	def __init__(self, filename):
		tm = load_pygame(filename)

		# self.size will be the pixel size of the map
		# this value is used later to render the entire map to a pygame image
		self.pixel_size = tm.width * tm.tilewidth*2, tm.height * tm.tileheight*2
		self.tmx_data = tm

	def render_tile_layer(self, image, layer):
		# deref these heavily used references for speed
		tw = self.tmx_data.tilewidth
		th = self.tmx_data.tileheight
		image_blit = image.blit

		# iterate over the tiles in the layer
		for x, y, image in layer.tiles():
			#if ((x * tw*2 >= camera.x-tw*2) and (y * th*2 >= camera.y-th*2)) and ((x * tw*2 <= camera.x+screen.width)and(y * th*2 <= camera.y+screen.height)):
			image = image.convert()
			image_blit(pygame.transform.scale2x(image), (x * tw*2, y * th*2))

	def render_object_layer(self, image, layer):
		# deref these heavily used references for speed
		draw_rect = pygame.draw.rect
		draw_lines = pygame.draw.lines
		tw = self.tmx_data.tilewidth
		th = self.tmx_data.tileheight
		image_blit = image.blit

		# these colors are used to draw vector shapes,
		# like polygon and box shapes
		rect_color = (255, 0, 0)
		poly_color = (0, 255, 0)

		# iterate over all the objects in the layer
		for obj in layer:
			#logger.info(obj)
			# objects with points are polygons or lines
			if hasattr(obj, 'points'):
				draw_lines(image, poly_color, obj.closed, obj.points, 3)

			# some objects have an image
			# Tiled calls them "GID Objects"
			elif obj.image:
				obj.image.convert()
				if hasattr(obj, 'rotation'):
					centerY = th / 2
					centerX = tw /2
					rotation = obj.rotation
					cosRotation = math.cos(math.radians(rotation))
					sinRotation = math.sin(math.radians(rotation))
					rotatedCenterX = centerX * cosRotation + centerY * sinRotation
					rotatedCenterY = centerX * sinRotation - centerY * cosRotation
					x = obj.x + rotatedCenterX - th/2 
					y = obj.y + rotatedCenterY + tw/2
					#if ((x*2 + obj.width*2 >= camera.x) and (y*2 + obj.height*2 >= camera.y)) and ((x*2 <= camera.x+screen.width)and(y*2 <= camera.y+screen.height)):
					image_blit(pygame.transform.rotate(pygame.transform.scale2x(obj.image), - obj.rotation ), (int(x*2), int(y*2)))
				else:
					#if ((obj.x*2 + obj.width*2 >= camera.x) and (obj.y*2 + obj.height*2 >= camera.y)) and ((obj.x*2 <= camera.x+screen.width)and(obj.y*2 <= camera.y+screen.height)):
					image_blit(pygame.transform.scale2x(obj.image), (obj.x*2, obj.y*2))


			# draw a rect for everything else
			# Mostly, I am lazy, but you could check if it is circle/oval
			# and use pygame to draw an oval here...I just do a rect.
			#else:
				#if ((obj.x*2 + obj.width*2 >= camera.x) and (obj.y*2 + obj.height*2 >= camera.y)) and ((obj.x*2 <= camera.x+screen.width)and(obj.y*2 <= camera.y+screen.height)):
				#draw_rect(image, rect_color, (obj.x*2, obj.y*2, obj.width*2, obj.height*2), 3)

	def render_image_layer(self, image, layer):
		if layer.image:
			layer.image = layer.image.convert()
			image.blit(layer.image, (0, 0))

"""
Map renderer including background/forgound
handling for the men and camera application
"""
class Renderer(object):

	def load_map(self,filename):
			self.renderer = TiledRenderer(filename)

	"""
	Load objects from the tmx map create an instance of the correct type for each 
	"""
	def load_objects (self):
		tw = self.renderer.tmx_data.tilewidth
		th = self.renderer.tmx_data.tileheight
		for layer in self.renderer.tmx_data.layers:
			if isinstance(layer, TiledTileLayer) and layer.properties['Object'] == 'True':
				for x, y, image in layer.tiles():
					# Plant.__name__ give the name of the Plant class as a string
					object_type = getattr(object_class,layer.name)
					obj = object_type(image)
					obj.rect.x = x * tw
					obj.rect.y = y * th
					list_name = layer.name + "_list"
					eval(list_name).add(obj)
					All_sprites_list.add(obj)

	"""
	Render every layer that has Background proprety set to True
	"""
	def load_background (self,screen,camera,grid):
			self.background = pygame.Surface([grid.width*grid.nodeSize,grid.height*grid.nodeSize]).convert_alpha()
			self.background.fill((0,0,0,0))
			self.zoomed_backgrounds = []
			
			self.Bzoom = -1

			for layer in self.renderer.tmx_data.visible_layers:
				if layer.properties['Position'] == 'Background':
					if isinstance(layer, TiledTileLayer):
						self.renderer.render_tile_layer(self.background, layer)
					if isinstance(layer,TiledObjectGroup):
						self.renderer.render_object_layer(self.background, layer)

			i = screen.minZoom
			while i <= screen.maxZoom + 0.02:
				self.zoomed_backgrounds.append(pygame.transform.scale(self.background,(int(math.ceil(self.background.get_rect().width*(abs(2 - i)))),int(math.ceil(self.background.get_rect().height*(abs(2 - i)))))).convert_alpha())
				i += 0.02

	"""
	Render every layer that has Forground proprety set to True
	"""
	def load_forground (self,screen,camera,grid):
			self.forgound = pygame.Surface([grid.width*grid.nodeSize,grid.height*grid.nodeSize]).convert_alpha()
			self.forgound.fill((0,0,0,0))
			self.zoomed_forgrounds = []
			
			self.Fzoom = -1

			for layer in self.renderer.tmx_data.visible_layers:
				if layer.properties['Position'] == 'Forground':
					if isinstance(layer, TiledTileLayer):
						self.renderer.render_tile_layer(self.forgound, layer)
					if isinstance(layer,TiledObjectGroup):
						self.renderer.render_object_layer(self.forgound, layer)

			i = screen.minZoom
			while i <= screen.maxZoom + 0.02:
				self.zoomed_forgrounds.append(pygame.transform.scale(self.forgound,(int(math.ceil(self.forgound.get_rect().width*(abs(2 - i)))),int(math.ceil(self.forgound.get_rect().height*(abs(2 - i)))))).convert_alpha())
				i += 0.02

	def draw_background(self,screen,camera):

		cut = self.zoomed_backgrounds[screen.zoomIndex].subsurface((camera.x+screen.xzoom,camera.y+screen.yzoom,screen.width,screen.height))
		screen.gameArea.blit(cut,(0,0))

	def draw_forground(self,screen,camera):

		cut = self.zoomed_forgrounds[screen.zoomIndex].subsurface((camera.x+screen.xzoom,camera.y+screen.yzoom,screen.width,screen.height))
		screen.gameArea.blit(cut,(0,0))

	def define_map_grid (self):

		from Astar import SquareGrid
		map_grid = SquareGrid((self.renderer.pixel_size[0]//64)-1,(self.renderer.pixel_size[1]//64)-1,64)
		for wall in All_collision_list:
			map_grid.walls.append(wall.rect)
		return map_grid

"""
Class for the squad
"""
class Squad (object):

	def __init__(self,screen,squad_member_list,grid):
		self.members = squad_member_list
		self.size = len(self.members)
		self.spriteGroup = pygame.sprite.Group()
		for member in self.members:
			self.spriteGroup.add(member)

		self.blitSurface = pygame.Surface([grid.width*grid.nodeSize,grid.height*grid.nodeSize]).convert_alpha()
		self.blitSurface.fill((0,0,0,0))
		
		self.blitSurfaces = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.blitSurfaces.append(pygame.transform.scale(self.blitSurface,(int(math.ceil(self.blitSurface.get_rect().width*(abs(2 - i)))),int(math.ceil(self.blitSurface.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.eraseSurface = pygame.Surface([self.members[0].rect.width,self.members[0].rect.height]).convert_alpha()
		self.eraseSurface.fill((0,0,0,0))

		self.eraseSurfaces = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.eraseSurfaces.append(pygame.transform.scale(self.eraseSurface,(int(math.ceil(self.eraseSurface.get_rect().width*(abs(2 - i)))),int(math.ceil(self.eraseSurface.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02
		
		self.zoom = -1

	def draw (self,screen,camera):
		for member in self.members:
			screen.gameArea.blit(pygame.transform.scale(member.image,(int(math.ceil(member.image.get_rect().width*(abs(2 - screen.zoom)))),int(math.ceil(member.image.get_rect().height*(abs(2 - screen.zoom)))))).convert_alpha(), (member.rect.x*(abs(2 - screen.zoom))-camera.x-screen.xzoom, member.rect.y*(abs(2 - screen.zoom))-camera.y-screen.yzoom))


class MHUD(object):

	def __init__ (self,screen,grid):
		self.mHUD = pygame.Surface([grid.width*grid.nodeSize,grid.height*grid.nodeSize]).convert_alpha()
		self.mHUD.fill((0,0,0,0))
		
		self.mHUDs = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.mHUDs.append(pygame.transform.scale(self.mHUD,(int(math.ceil(self.mHUD.get_rect().width*(abs(2 - i)))),int(math.ceil(self.mHUD.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.walkTileImage = pygame.image.load(os.path.abspath('spritesheets/mHUD/moving_range_walk.png')).convert_alpha()
		self.walkTile = pygame.Surface ((64,64),pygame.SRCALPHA).convert_alpha()
		self.walkTile.blit(pygame.transform.scale2x(self.walkTileImage),(0,0))

		self.walkTiles = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.walkTiles.append(pygame.transform.scale(self.walkTile,(int(math.ceil(self.walkTile.get_rect().width*(abs(2 - i)))),int(math.ceil(self.walkTile.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02
		
		self.runTileImage = pygame.image.load(os.path.abspath('spritesheets/mHUD/moving_range_run.png')).convert_alpha()
		self.runTile = pygame.Surface ((64,64),pygame.SRCALPHA).convert_alpha()
		self.runTile.blit(pygame.transform.scale2x(self.runTileImage),(0,0))

		self.runTiles = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.runTiles.append(pygame.transform.scale(self.runTile,(int(math.ceil(self.runTile.get_rect().width*(abs(2 - i)))),int(math.ceil(self.runTile.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.cursorValidImg = pygame.image.load(os.path.abspath('spritesheets/mHUD/cursor_valid.png')).convert_alpha()
		self.cursorValid = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.cursorValid.blit(self.cursorValidImg,(0,0))

		self.cursorValids = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.cursorValids.append(pygame.transform.scale(self.cursorValid,(int(math.ceil(self.cursorValid.get_rect().width*(abs(2 - i)))),int(math.ceil(self.cursorValid.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.cursorInvalidImg = pygame.image.load(os.path.abspath('spritesheets/mHUD/cursor_invalid.png')).convert_alpha()
		self.cursorInvalid = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.cursorInvalid.blit(self.cursorInvalidImg,(0,0))
	
		self.cursorInvalids = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.cursorInvalids.append(pygame.transform.scale(self.cursorInvalid,(int(math.ceil(self.cursorInvalid.get_rect().width*(abs(2 - i)))),int(math.ceil(self.cursorInvalid.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.selectedImg = pygame.image.load(os.path.abspath('spritesheets/mHUD/selected.png')).convert_alpha()
		self.selected = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.selected.blit(self.selectedImg,(0,0,))

		self.selecteds = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.selecteds.append(pygame.transform.scale(self.selected,(int(math.ceil(self.selected.get_rect().width*(abs(2 - i)))),int(math.ceil(self.selected.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.shield_fullImg = pygame.image.load(os.path.abspath('spritesheets/mHUD/shield_2.png')).convert_alpha()
		self.shield_full = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.shield_full.blit(self.shield_fullImg,(0,0))

		self.shield_fulls = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.shield_fulls.append(pygame.transform.scale(self.shield_full,(int(math.ceil(self.shield_full.get_rect().width*(abs(2 - i)))),int(math.ceil(self.shield_full.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.shield_halfImg = pygame.image.load(os.path.abspath('spritesheets/mHUD/shield_1.png')).convert_alpha()
		self.shield_half = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.shield_half.blit(self.shield_halfImg,(0,0))

		self.shield_halfs = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.shield_halfs.append(pygame.transform.scale(self.shield_half,(int(math.ceil(self.shield_half.get_rect().width*(abs(2 - i)))),int(math.ceil(self.shield_half.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.shield_emptyImg = pygame.image.load(os.path.abspath('spritesheets/mHUD/shield_0.png')).convert_alpha()
		self.shield_empty = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.shield_empty.blit(self.shield_emptyImg,(0,0))

		self.shield_emptys = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.shield_emptys.append(pygame.transform.scale(self.shield_empty,(int(math.ceil(self.shield_empty.get_rect().width*(abs(2 - i)))),int(math.ceil(self.shield_empty.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.tileCleaningSurf = pygame.Surface([grid.nodeSize,grid.nodeSize]).convert_alpha()
		self.tileCleaningSurf.fill((0,0,0,0))

		self.tileCleaningSurfs = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.tileCleaningSurfs.append(pygame.transform.scale(self.tileCleaningSurf,(int(math.ceil(self.tileCleaningSurf.get_rect().width*(abs(2 - i)))),int(math.ceil(self.tileCleaningSurf.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02


		self.errase_cover = []

		self.old_tiles = []
		self.oldMousePos = (-1,-1)
		self.old_memberPos = (-1,-1)

		self.zoom = -1

	def update(self,screen,camera,mousePos,grid,AP1tiles,AP2tiles,memberPos,memberMoving,memberAbility):
		id = (((mousePos[0]+camera.x+screen.xzoom)//(grid.nodeSize*(abs(2 - screen.zoom)))),((mousePos[1]+camera.y+screen.yzoom)//(grid.nodeSize*(abs(2 - screen.zoom)))))
		memberPos = (memberPos[0]//grid.nodeSize,memberPos[1]//grid.nodeSize)

		if screen.zoom != self.zoom:
			self.mHUDs[screen.zoomIndex].fill((0,0,0,0))
			self.errase_cover = []
			self.old_tiles = []
			self.oldMousePos = (-1,-1)
			self.old_memberPos = (-1,-1)
			self.zoom = screen.zoom

		if ( memberMoving != None ) or memberAbility :
			self.mHUDs[screen.zoomIndex].fill((0,0,0,0))
			self.old_tiles = []
			self.old_memberPos = (-1,-1)
			self.dirty = True

		else :
			if self.oldMousePos != id:
				if self.oldMousePos in AP1tiles:
					self.errase_tiles(screen,grid,[self.oldMousePos])
					self.draw_walk_tiles(screen,grid,[self.oldMousePos])
				elif self.oldMousePos in AP2tiles:
					self.errase_tiles(screen,grid,[self.oldMousePos])
					self.draw_run_tiles(screen,grid,[self.oldMousePos])
				else:
					self.errase_tiles(screen,grid,[self.oldMousePos])

				if self.oldMousePos == memberPos:
					self.draw_selected_memberTile(screen,memberPos,grid)
				
				self.errase_tiles(screen,grid,self.errase_cover)
				self.draw_selected_tile(screen,id,grid,AP2tiles,memberPos,camera)

				self.oldMousePos = id
				self.dirty = True

			if self.old_tiles != AP2tiles :
				self.errase_tiles(screen,grid,self.old_tiles)
				self.errase_tiles(screen,grid,self.errase_cover)
				self.draw_walk_tiles(screen,grid,AP1tiles)
				self.draw_run_tiles(screen,grid,[tile for tile in AP2tiles if tile not in set(AP1tiles)])
				self.draw_selected_tile(screen,id,grid,AP2tiles,memberPos,camera)
				self.old_tiles = AP2tiles
				self.dirty = True
			
			if self.old_memberPos != memberPos and memberMoving == None:
				self.draw_selected_memberTile(screen,memberPos,grid)
				self.old_memberPos = memberPos
				self.dirty = True


	def draw(self,screen,camera):

		screen.gameArea.blit(self.mHUDs[screen.zoomIndex].subsurface((camera.x+screen.xzoom,camera.y+screen.yzoom,screen.width,screen.height)),(0,0))

	def errase_tiles(self,screen,grid,tiles):
		size = grid.nodeSize*(abs(2 - screen.zoom))
		for tile in tiles:
			(x,y) = tile
			self.mHUDs[screen.zoomIndex].blit(self.tileCleaningSurfs[screen.zoomIndex],(x*size,y*size,size,size),None,BLEND_RGBA_MIN)

	def draw_selected_memberTile(self,screen,id,grid):
		size = grid.nodeSize*(abs(2 - screen.zoom))
		(x,y) = (id[0]*size,id[1]*size)
		self.mHUDs[screen.zoomIndex].blit(self.selecteds[screen.zoomIndex],(x,y),None)

	def draw_selected_tile(self,screen,id,grid,tiles,memberPos,camera):
		size = grid.nodeSize*(abs(2 - screen.zoom))
		(x,y) = (id[0]*size,id[1]*size)
		if grid.passable(id) and id in tiles:
			self.mHUDs[screen.zoomIndex].blit(self.cursorValids[screen.zoomIndex],(x,y))
			self.draw_cover_quality(screen,grid,id)
			#self.draw_path(grid,memberPos,id,camera)
		else:
			self.mHUDs[screen.zoomIndex].blit(self.cursorInvalids[screen.zoomIndex],(x,y))

	def draw_walk_tiles(self,screen,grid,tiles):
		for tile in tiles:
			(x,y) = tile
			size = grid.nodeSize*(abs(2 - screen.zoom))
			self.mHUDs[screen.zoomIndex].blit(self.walkTiles[screen.zoomIndex],(x*size,y*size))
	
	def draw_run_tiles(self,screen,grid,tiles):
		for tile in tiles:
			(x,y) = tile
			size = grid.nodeSize*(abs(2 - screen.zoom))
			self.mHUDs[screen.zoomIndex].blit(self.runTiles[screen.zoomIndex],(x*size,y*size))

	def draw_path(self,screen,grid,start,goal,camera):
		path = a_star_search(grid,start,goal)
		for i in range(len(path)-1):
			pygame.draw.line(self.mHUDs[screen.zoomIndex],black,((path[i][0]*64+32)-camera.x,(path[i][1]*64+32)-camera.y),((path[i+1][0]*64+32)-camera.x,(path[i+1][1]*64+32)-camera.y))
		
	def draw_cover_quality(self,screen,grid,fromtile):
		self.errase_cover = []
		angle = 180
		(x,y) = fromtile
		size = grid.nodeSize*(abs(2 - screen.zoom))
		for tile in [(x,y+1),(x+1,y),(x,y-1),(x-1,y)]:
			if not grid.passable(tile):
				self.mHUDs[screen.zoomIndex].blit(pygame.transform.rotate(self.shield_fulls[screen.zoomIndex],angle),(tile[0]*size,tile[1]*size),None)
				self.errase_cover.append(tile)
			angle += 90

# to optimize
class Abilities_HUD(object):

	def __init__(self,screen,grid):
		self.abilities_HUD = pygame.Surface([grid.width*grid.nodeSize,grid.height*grid.nodeSize]).convert_alpha()
		self.abilities_HUD.fill((0,0,0,0))
		self.abilities_HUDs = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.abilities_HUDs.append(pygame.transform.scale(self.abilities_HUD,(int(math.ceil(self.abilities_HUD.get_rect().width*(abs(2 - i)))),int(math.ceil(self.abilities_HUD.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.current = None
		self.targets = []
		self.mousePos = (-1,-1)
		self.rotate_point = (0,0)
		self.image = pygame.image.load('spritesheets/mHUD/target.png').convert_alpha()
		self.image = pygame.transform.scale(self.image,(64,64)).convert_alpha()
		self.images = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.images.append(pygame.transform.scale(self.image,(int(math.ceil(self.image.get_rect().width*(abs(2 - i)))),int(math.ceil(self.image.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.cleaningSurf = pygame.Surface((64,64)).convert_alpha()
		self.cleaningSurf.fill((0,0,0,0))
		self.cleaningSurfs = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.cleaningSurfs.append(pygame.transform.scale(self.cleaningSurf,(int(math.ceil(self.cleaningSurf.get_rect().width*(abs(2 - i)))),int(math.ceil(self.cleaningSurf.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.zoom = -1
		self.dirty = False

	def update(self,camera,ability,mousePos,squad_sight,enemies,man,screen,grid):
		mousePos = (((mousePos[0]+camera.x+screen.xzoom)),((mousePos[1]+camera.y+screen.yzoom)))
		if self.current != ability:
			self.current = ability
			self.dirty = True
		if self.zoom != screen.zoom:
			self.dirty = True
			self.zoom = screen.zoom
		if self.current.select and self.dirty:
			if self.current.type == 1:
				
				targets = squad_sight.scan_all(man,enemies,camera,screen)
				size = (abs(2 - screen.zoom))

				if self.targets != targets or self.dirty:
					for dirty in self.targets:
						self.abilities_HUDs[screen.zoomIndex].blit(self.cleaningSurfs[screen.zoomIndex],((dirty[0]-32)*size,(dirty[1]-32)*size),None,BLEND_RGBA_MIN)
					self.targets = targets
					self.dirty = True

					for target in targets:
						self.rotate_point = mousePos
						self.abilities_HUDs[screen.zoomIndex].blit(self.images[screen.zoomIndex],((target[0]-32)*size,(target[1]-32)*size))
						self.mousePos = mousePos
			self.dirty = False


	def mouse_on_target (self,screen,camera,mousePos,grid):
		for target in self.targets:
			tileArea = pygame.Rect(((target[0]-grid.nodeSize/2)*(abs(2 - screen.zoom))-camera.x-screen.xzoom,(target[1]-grid.nodeSize/2)*(abs(2 - screen.zoom))-camera.y-screen.yzoom,grid.nodeSize*(abs(2 - screen.zoom)),grid.nodeSize*(abs(2 - screen.zoom))))
			if tileArea.collidepoint(mousePos):
				return target
		return None

	def draw(self,screen,camera):
		screen.gameArea.blit(self.abilities_HUDs[screen.zoomIndex].subsurface((camera.x+screen.xzoom,camera.y+screen.yzoom,screen.width,screen.height)),(0,0))

class Squad_sight(object):

	def __init__(self,screen,camera,squad):
		self.pos = []
		for member in squad.members:
			self.pos.append((member.center,member.sight_radius,member.id,member.light_source))
		self.polygones = []
		for member in squad.members:
				SegsnPoints = init(member.center[0],member.center[1],All_collision_list,member.sight_radius)
				self.polygones.append(([getSightPolygon(member.center[0],member.center[1],SegsnPoints[0],SegsnPoints[1],camera)],member.id))
		self.zoom = -1
		self.dirty = False

	def update(self,screen,camera,squad):

		if self.zoom != screen.zoom:
			self.dirty = True
			self.zoom = screen.zoom
		for member in squad.members:
			if member.center[0] != member.old_pos[0] or member.center[1] != member.old_pos[1] or self.dirty:

				supp = [p for p in self.polygones if p[1]==member.id]
				for s in supp :
					self.polygones.remove(s)
				SegsnPoints = init(member.center[0],member.center[1],All_collision_list,member.sight_radius)
				self.polygones.append(([getSightPolygon(member.center[0],member.center[1],SegsnPoints[0],SegsnPoints[1],camera)],member.id))
				member.light_source.move(member.center,screen,camera)
		self.dirty = False

	def scan_all(self,man,targets,camera,screen):
		res = []
		supp = [p for p in self.polygones if p[1]==man.id]
		for target in targets:
			curr = False
			dist = math.sqrt(((target[0]-man.center[0])*(target[0]-man.center[0]))+((target[1]-man.center[1])*(target[1]-man.center[1])))
			for polygone in self.polygones:
				curr = curr or (self.scan((man.center[0],man.center[1]),target,supp[0][0][0],camera,screen))
			if curr and (dist <= 500):
				res.append(target)
		return res

	def scan(self,from_point,target,polygones,camera,screen):
		p = (target[0]-camera.x,target[1]-camera.y)
		for i in range(len(polygones)-1):
			t = [(from_point[0]-camera.x,from_point[1]-camera.y),(polygones[i][0],polygones[i][1]),(polygones[i+1][0],polygones[i+1][1])]

			if ((t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1])) != 0:
				a = ((t[1][1]-t[2][1])*(p[0]-t[2][0])+(t[2][0]-t[1][0])*(p[1]-t[2][1]))/((t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1])) 
				b = ((t[2][1]-t[0][1])*(p[0]-t[2][0])+(t[0][0]-t[2][0])*(p[1]-t[2][1]))/((t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1])) 
				c = 1-a-b
			else :
				a = 2
				b = 2
				c = 2
			
			if (0<=a and a<=1) and (0<=b and b<=1) and (0<=c and c<=1):
				return True

		t = [(from_point[0]-camera.x,from_point[1]-camera.y),(polygones[0][0],polygones[0][1]),(polygones[len(polygones)-1][0],polygones[len(polygones)-1][1])]

		if ((t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1])) != 0:
			a = ((t[1][1]-t[2][1])*(p[0]-t[2][0])+(t[2][0]-t[1][0])*(p[1]-t[2][1]))/((t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1])) 
			b = ((t[2][1]-t[0][1])*(p[0]-t[2][0])+(t[0][0]-t[2][0])*(p[1]-t[2][1]))/((t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1])) 
			c = 1-a-b
		else :
			a = ((t[1][1]-t[2][1])*(p[0]-t[2][0])+(t[2][0]-t[1][0])*(p[1]-t[2][1]))
			b = ((t[2][1]-t[0][1])*(p[0]-t[2][0])+(t[0][0]-t[2][0])*(p[1]-t[2][1]))
			c = 1-a-b

		if (0<=a and a<=1) and (0<=b and b<=1) and (0<=c and c<=1):
			return True

		return False


class light_source(object):

	def __init__ (self,screen,camera,position,radius):
		#light sources create shadows
		self.old_pos = position
		self.pos = position
		self.radius = radius
		self.SegsnPoints = init(self.pos[0],self.pos[1],All_collision_list,2*self.radius)
		p = getSightPolygon(self.pos[0],self.pos[1],self.SegsnPoints[0],self.SegsnPoints[1],camera,True)
		self.lightPoly = []
		for point in p:
			self.lightPoly.append((point[0]-self.pos[0]+self.radius/2,point[1]-self.pos[1]+self.radius/2))

		self.alpha = 0

		self.drawSurface = pygame.Surface([self.radius,self.radius]).convert_alpha()
		self.drawSurface.fill((0,0,0,100))
		self.drawSurfaces = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.drawSurfaces.append(pygame.transform.scale(self.drawSurface,(int(math.ceil(self.drawSurface.get_rect().width*(abs(2 - i)))),int(math.ceil(self.drawSurface.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.radiusImg = pygame.image.load(os.path.abspath('spritesheets/light640.png')).convert_alpha()
		self.radiusSurface = pygame.Surface([self.radius,self.radius]).convert_alpha()
		self.radiusSurface.fill((0,0,0,0))
		self.radiusSurface.blit(pygame.transform.scale2x(self.radiusImg),(0,0))
		self.radiusSurfaces = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.radiusSurfaces.append(pygame.transform.scale(self.radiusSurface,(int(math.ceil(self.radiusSurface.get_rect().width*(abs(2 - i)))),int(math.ceil(self.radiusSurface.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.erraseSurface = pygame.Surface([self.radius,self.radius]).convert_alpha()
		self.erraseSurface.fill((0,0,0,self.alpha))
		pygame.draw.circle(self.erraseSurface,(0,0,0,100),(self.radius,self.radius),self.radius)
		self.erraseSurfaces = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.erraseSurfaces.append(pygame.transform.scale(self.erraseSurface,(int(math.ceil(self.erraseSurface.get_rect().width*(abs(2 - i)))),int(math.ceil(self.erraseSurface.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02


	def move(self,pos,screen,camera):
		self.old_pos = self.pos
		self.pos = pos
		self.SegsnPoints = init(self.pos[0],self.pos[1],All_collision_list,2*self.radius-5)
		p = getSightPolygon(self.pos[0],self.pos[1],self.SegsnPoints[0],self.SegsnPoints[1],camera,True)
		self.lightPoly = []
		for point in p:
			self.lightPoly.append(((point[0]-self.pos[0]+self.radius/2)*(abs(2 - screen.zoom)),(point[1]-self.pos[1]+self.radius/2)*(abs(2 - screen.zoom))))

	def errase(self,screen,camera,mask):

		self.drawSurfaces[screen.zoomIndex].fill((0,0,0,100))
		mask.blit(self.drawSurfaces[screen.zoomIndex],((self.old_pos[0]-self.radius/2)*(abs(2 - screen.zoom)),(self.old_pos[1]-self.radius/2)*(abs(2 - screen.zoom))),None,BLEND_RGBA_MAX)

	def update(self,screen,camera):

		pygame.draw.polygon(self.drawSurfaces[screen.zoomIndex],(0,0,0,self.alpha),self.lightPoly)
		self.drawSurfaces[screen.zoomIndex].blit(self.radiusSurfaces[screen.zoomIndex],(0,0),None,BLEND_RGBA_MAX)
		self.old_pos = self.pos

	def apply (self,screen,camera,mask):
		mask.blit(self.drawSurfaces[screen.zoomIndex],((self.pos[0]-self.radius/2)*(abs(2 - screen.zoom)),(self.pos[1]-self.radius/2)*(abs(2 - screen.zoom))),None,BLEND_RGBA_MIN)



class light (object):

	def __init__ (self,screen,grid,alpha):

		#ambient light cover the entire map
		self.alpha = alpha
		self.ambient = pygame.Surface([grid.width*grid.nodeSize,grid.height*grid.nodeSize]).convert_alpha()
		self.ambient.fill((0,0,0,self.alpha))
		self.ambients = []
		i = screen.minZoom
		while i <= screen.maxZoom + 0.02:
			self.ambients.append(pygame.transform.scale(self.ambient,(int(math.ceil(self.ambient.get_rect().width*(abs(2 - i)))),int(math.ceil(self.ambient.get_rect().height*(abs(2 - i)))))).convert_alpha())
			i += 0.02

		self.rect = pygame.Rect(0,0,grid.width*grid.nodeSize,grid.height*grid.nodeSize)
		self.dirty = []
		self.zoom = -1
		self.current = None

	def update (self,screen,camera,light_sources,init=False):
		#apply shadows from light source on the mask
		for light_source in light_sources:
			if light_source.old_pos[0]//64 != light_source.pos[0]//64 or light_source.old_pos[1]//64 != light_source.pos[1]//64 or init or screen.zoom != self.zoom:
				self.dirty.append(light_source)
				self.ambients[screen.zoomIndex].fill((0,0,0,self.alpha))
		self.zoom = screen.zoom

		if self.dirty != []:
			for light_source in light_sources:
				light_source.errase(screen,camera,self.ambients[screen.zoomIndex])
				light_source.update(screen,camera)
			
			for light_source in light_sources:
				light_source.apply(screen,camera,self.ambients[screen.zoomIndex])
		self.dirty = []

	def draw (self,screen,camera):

		screen.gameArea.blit(self.ambients[screen.zoomIndex].subsurface((camera.x+screen.xzoom,camera.y+screen.yzoom,screen.width,screen.height)),(0,0))