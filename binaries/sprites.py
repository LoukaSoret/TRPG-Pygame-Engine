#import pygame module and other usefull modules
import os, pygame, sys, random, math
from operator import itemgetter

from pygame.locals import *
import renderer

#import tmx file reader
from pytmx import *
from pytmx.util_pygame import load_pygame

from Astar import *
from sightandlight import *
from renderer import All_collision_list,light_source

#Colors
black = (0,0,0)
white = (255,255,255)
red = (255,0,0)


All_bullet_list = pygame.sprite.Group()
All_sprites_list = pygame.sprite.Group()

All_speakable_npcs = pygame.sprite.Group()


"""
__________________________________________________________________________________________________________

THIS FILE CONTAIN THE CLASSES LISTED BELOW:
-Spritesheet
-Animation
-Collition
-Man
-Bullet
___________________________________________________________________________________________________________
"""

"""
Load and store sprite sheets for further animation treatment
"""
class Spritesheet(object):
	def __init__(self,filename):
		try:
			self.sheet = pygame.image.load(filename).convert_alpha()
		except pygame.error, message:
			print 'Unable to load spritesheet image:', filename
			raise SystemExit, message
	
	def image_at(self, rectangle, colorkey = None):
		"Loads image from x,y,x+offset,y+offset"
		rect = pygame.Rect(rectangle)
		image = pygame.Surface(rect.size,pygame.SRCALPHA).convert_alpha()
		image.blit(self.sheet, (0, 0), rect)
		if colorkey is not None:
			if colorkey is -1:
				colorkey = image.get_at((0,0))
		image.set_colorkey(colorkey)
		return pygame.transform.scale2x(image)
	# Load a whole bunch of images and return them as a list
	def images_at(self, rects, colorkey = None):
		"Loads multiple images, supply a list of coordinates"
		return [self.image_at(rect, colorkey) for rect in rects]

"""
A class to play animations
"""
class Animation ():
	def __init__(self,interval,images_list):

		self.images_list = images_list
		self.resting_posture = self.images_list[0]
		self.image = self.images_list[0]

		self.counter = 0
		self.cycletime = 0
		self.interval = interval
		self.done = False


	def play_circle (self,seconds):

		self.cycletime += seconds
		if self.cycletime > self.interval:
			self.image = self.images_list[self.counter]
			self.counter = (self.counter +1) % len(self.images_list)
			self.cycletime = 0
		return self.image

	def play_line (self,seconds):
	
		self.cycletime += seconds
		if self.cycletime > self.interval:
			if len(self.images_list) > self.counter:
				self.image = self.images_list[self.counter]
				self.counter = (self.counter +1)
			else:
				self.done = True
			self.cycletime = 0
		return self.image

	def reset (self):
		self.image = self.resting_posture
		self.counter = 0
		self.done = False
		return self.image

"""
Initialise and update the HUD
"""
class HUD():
	
	def __init__(self,screen):
		#life bar images
		self.shot0 = pygame.image.load('spritesheets/HUD/Life_bar_full.png').convert_alpha()
		self.shot1 = pygame.image.load('spritesheets/HUD/Life_bar_shot_1.png').convert_alpha()
		self.shot2 = pygame.image.load('spritesheets/HUD/Life_bar_shot_2.png').convert_alpha()
		self.shot3 = pygame.image.load('spritesheets/HUD/Life_bar_shot_3.png').convert_alpha()


		#barrel images
		self.barrel6 = Animation(.05,[pygame.image.load(os.path.abspath('spritesheets/HUD/barrel6.png')).convert_alpha()])
		self.barrel5 = Animation(.05,(Spritesheet(os.path.abspath('spritesheets/HUD/allbarrelsspritesheet.png')).images_at([(0,0,270,270),(270,0,270,270),(540,0,270,270),(810,0,270,270),(1080,0,270,270)])))
		self.barrel4 = Animation(.05,(Spritesheet(os.path.abspath('spritesheets/HUD/allbarrelsspritesheet.png')).images_at([(0,270,270,270),(270,270,270,270),(540,270,270,270),(810,270,270,270),(1080,270,270,270)])))
		self.barrel3 = Animation(.05,(Spritesheet(os.path.abspath('spritesheets/HUD/allbarrelsspritesheet.png')).images_at([(0,540,270,270),(270,540,270,270),(540,540,270,270),(810,540,270,270),(1080,540,270,270)])))
		self.barrel2 = Animation(.05,(Spritesheet(os.path.abspath('spritesheets/HUD/allbarrelsspritesheet.png')).images_at([(0,810,270,270),(270,810,270,270),(540,810,270,270),(810,810,270,270),(1080,810,270,270)])))
		self.barrel1 = Animation(.05,(Spritesheet(os.path.abspath('spritesheets/HUD/allbarrelsspritesheet.png')).images_at([(0,1080,270,270),(270,1080,270,270),(540,1080,270,270),(810,1080,270,270),(1080,1080,270,270)])))
		self.barrel0 = Animation(.05,(Spritesheet(os.path.abspath('spritesheets/HUD/allbarrelsspritesheet.png')).images_at([(0,1350,270,270),(270,1350,270,270),(540,1350,270,270),(810,1350,270,270),(1080,1350,270,270)])))

		#dialog box images
		self.dialog_box_img = pygame.image.load('spritesheets/HUD/dialog_box.png').convert_alpha()

		#information box
		self.info_box_img = pygame.image.load('spritesheets/HUD/wanted.png').convert_alpha()

		#shot button
		self.shot_button_img = pygame.image.load('spritesheets/HUD/shot.png').convert_alpha()
		self.slice_button_img = pygame.image.load('spritesheets/HUD/slice.png').convert_alpha()

		# Surfaces 
		self.life_bar = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		
		self.lifeBarCleaningSurf = pygame.Surface((220,100),pygame.SRCALPHA).convert_alpha()
		self.lifeBarCleaningSurf.fill((0,0,0,0))
		
		self.life_bar.blit (self.shot0,(0,0),(0,0,64,64))
		self.old_life = 0


		self.barrel = pygame.Surface ((1240,1240),pygame.SRCALPHA).convert_alpha()
		self.old_bullets = 0

		self.dialog_box = pygame.Surface ((190,32),pygame.SRCALPHA).convert_alpha()
		self.dialog_box.blit (self.dialog_box_img,(0,0),(0,0,190,32))

		self.info_box = pygame.Surface((380,128),pygame.SRCALPHA).convert_alpha()
		self.info_box.blit(pygame.transform.scale2x(self.info_box_img),(0,0),(0,0,380,128))

		self.shot_button = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.shot_button.blit(pygame.transform.scale2x(self.shot_button_img),(0,0),(0,0,64,64))

		self.slice_button = pygame.Surface((64,64),pygame.SRCALPHA).convert_alpha()
		self.slice_button.blit(pygame.transform.scale2x(self.slice_button_img),(0,0),(0,0,64,64))

		# dialogs
		self.counter = 0
		self.dialog = False
		self.dialog_text = []

		# fps display
		self.delay = 0.2
		self.curr = 0
		self.fps = 0

		#cleaning surfaces
		self.drawSurface = pygame.Surface([screen.width,screen.height]).convert_alpha()
		self.drawSurface.fill((0,0,0,0))

		self.fpsCleaningSurf = pygame.Surface([70,40]).convert_alpha()
		self.fpsCleaningSurf.fill((0,0,0,0))

		self.barrelCleaningSurf = pygame.Surface([144,144]).convert_alpha()
		self.barrelCleaningSurf.fill((0,0,0,0))

		self.drawSurface.blit(self.info_box,(40,screen.height - 168))
		self.drawSurface.blit(self.shot_button,(700,screen.height - 104))
		self.drawSurface.blit(self.slice_button,(800,screen.height - 104))

	def update(self,seconds,screen,life,bullets,fps):

		if self.old_life != life:
			self.life_bar.fill((0,0,0,0))
			for i in range(4-(life)):
				self.life_bar.blit(eval('self.shot'+str(i)),(0,0),(0,0,64,64))
				self.life_bar_dirty = True
		
		if self.old_bullets != bullets:
			self.barrel = eval('self.barrel'+str(bullets)).play_line(seconds)
		
		"""
		if self.dialog:
			if len(self.dialog_text) <= self.counter:
				self.dialog = False
			else:
				phrase = self.dialog_text[self.counter]

				self.drawSurface.blit(pygame.transform.scale(self.dialog_box,(190*5,32*5)),((screen.width/2)-475,screen.height-155,190,32))
				font = pygame.font.Font(None, 36)
				text = font.render('', 1, black)
				textpos = text.get_rect()
				textpos.centerx = (screen.width/2)-475+100
				textpos.centery = screen.height-155+70

				for line in phrase:
					text = font.render(line, 1, black)
					textpos.centery += 25
					screen.gameArea.blit (text,textpos)
		else:
			self.counter = 0
		"""
		
		self.curr += seconds
		if self.curr >= self.delay:
			self.fps = fps
			self.curr = 0

			font = pygame.font.Font(None, 36)
			text = font.render(str(round(self.fps,2)), 1, black)
			textpos = text.get_rect()
			textpos.centerx = 100
			textpos.centery = 200
			self.drawSurface.blit (self.fpsCleaningSurf,(textpos[0]-6,textpos[1]-5),None,BLEND_RGBA_MIN)
			self.drawSurface.blit (text,textpos)

		if self.old_life != life:
			self.drawSurface.blit(self.lifeBarCleaningSurf,(10,30),None,BLEND_RGBA_MIN)
			self.drawSurface.blit(pygame.transform.scale(self.life_bar,(192,192)),(30,-10,64,64))
			self.old_life = life

		if self.old_bullets != bullets:
			self.drawSurface.blit(self.barrelCleaningSurf,(250,10),None,BLEND_RGBA_MIN)
			self.drawSurface.blit(pygame.transform.scale(self.barrel,(144,144)),(250,10,1240,1240))
			if eval('self.barrel'+str(bullets)).done:
				self.barrel = eval('self.barrel'+str(bullets)).reset()
				self.old_bullets = bullets

	def draw (self,screen):
		screen.gameArea.blit(self.drawSurface,(0,0))

"""
Class for collision sprites
"""
class Collision(pygame.sprite.Sprite):

	def __init__ (self,width,height,x,y):

		super(Collision,self).__init__()
		
		self.image = pygame.Surface((int(width),int(height))).convert_alpha()
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y


"""
Initialise and update man object
"""
class Man (pygame.sprite.DirtySprite):

	def __init__ (self,screen,camera,grid,path,id,spawn_point):

		#call the parent class (Sprite) constructor
		super(Man,self).__init__()

		self.id = id

		# movement propreties
		self.movement = {'left': False,'right': False, 'up': False, 'down': False}
		self.movements = False

		# Load and cut sprites

		self.walk_feet_up = Animation(.05,(Spritesheet(os.path.abspath(path+'Walk_feet.png')).images_at([(0,0,32,32),(32,0,32,32),(64,0,32,32),(96,0,32,32),(128,0,32,32),(160,0,32,32),(192,0,32,32),(224,0,32,32),(256,0,32,32),(288,0,32,32),(320,0,32,32),(352,0,32,32),(384,0,32,32),(416,0,32,32),(448,0,32,32),(480,0,32,32)])))
		self.walk_feet_down = Animation(.05,(Spritesheet(os.path.abspath(path+'Walk_feet.png')).images_at([(0,32,32,32),(32,32,32,32),(64,32,32,32),(96,32,32,32),(128,32,32,32),(160,32,32,32),(192,32,32,32),(224,32,32,32),(256,32,32,32),(288,32,32,32),(320,32,32,32),(352,32,32,32),(384,32,32,32),(416,32,32,32),(448,32,32,32),(480,32,32,32)])))
		self.walk_feet_right = Animation(.05,(Spritesheet(os.path.abspath(path+'Walk_feet.png')).images_at([(0,64,32,32),(32,64,32,32),(64,64,32,32),(96,64,32,32),(128,64,32,32),(160,64,32,32),(192,64,32,32),(224,64,32,32),(256,64,32,32),(288,64,32,32),(320,64,32,32),(352,64,32,32),(384,64,32,32),(416,64,32,32),(448,64,32,32),(480,64,32,32)])))
		self.walk_feet_left = Animation(.05,(Spritesheet(os.path.abspath(path+'Walk_feet.png')).images_at([(0,96,32,32),(32,96,32,32),(64,96,32,32),(96,96,32,32),(128,96,32,32),(160,96,32,32),(192,96,32,32),(224,96,32,32),(256,96,32,32),(288,96,32,32),(320,96,32,32),(352,96,32,32),(384,96,32,32),(416,96,32,32),(448,96,32,32),(480,96,32,32)])))
		self.walk_body = Animation(.2,(Spritesheet(os.path.abspath(path+'Walk_body.png')).images_at([(0,0,32,32),(32,0,32,32),(64,0,32,32),(96,0,32,32)])))

		#init propreties
		self.speed = 4
		self.sight_radius = 1280

		#load images
		self.SourceImage = self.walk_body.images_list[0]
		self.image = self.SourceImage
		self.feet = self.walk_feet_left.images_list[0]

		# rects
		self.rect = self.image.get_rect()
		self.bbox = self.SourceImage.get_rect()

		self.bbox.x = spawn_point[0]
		self.bbox.y = spawn_point[1]
		
		self.center = (self.bbox.x + int(self.bbox.width / 2),self.bbox.y + int(self.bbox.height / 2))

		self.old_pos = (0,0)

		# angle
		self.rotate_point = [0,0]
		self.angle = 0

		if id != "bad_boi":
			self.light_source = light_source(screen,camera,self.center,self.sight_radius)

		self.abilities = [Shot(path)]
		self.curr_ability = self.abilities[0]

		#HUD related
		self.life = 3
		self.bullets = 6

		#Follow vars
		self.path = []
		self.path_step = 0
		self.reached = True
		self.div = grid.nodeSize*(abs(2 - screen.zoom))
		self.init = True
		self.target = None
		self.reached = False

		# Action points
		self.total_AP = 2
		self.current_AP = 2
		self.can_spend = True
		self.range_need_refresh = True
		self.walk_range = []
		self.run_range = []


	def update (self,screen,camera,delay,seconds,grid):


		self.old_pos = self.center
		self.div = grid.nodeSize

		if self.range_need_refresh:
			if self.current_AP >= 1:
				self.walk_range = costs_from_point(grid,(self.center[0]//self.div,self.center[1]//self.div),5)
			else :
				self.walk_range = []
			if self.current_AP >= 2:
				self.run_range = costs_from_point(grid,(self.center[0]//self.div,self.center[1]//self.div),9)
			else :
				self.run_range = self.walk_range
			self.range_need_refresh = False
		
		if self.target != None and self.can_spend:
			if (self.target[0],self.target[1]) in self.walk_range:
				self.current_AP -= 1
				self.can_spend = False
			elif (self.target[0],self.target[1]) in self.run_range:
				self.current_AP -= 2
				self.can_spend = False
			else:
				self.target = None

		if self.abilities[0].select and not self.can_spend:
			self.abilities[0].select = False

		if self.abilities[0].play and self.can_spend:
			self.current_AP -= 1
			self.can_spend = False

		if self.target != None and ((self.target[0],self.target[1]) in self.run_range or (self.target[0],self.target[1]) in self.walk_range):
			self.go_to(grid,self.target,screen,camera,delay)

		# see if there is movement
		if self.movement['left'] or self.movement['right'] or self.movement['up'] or self.movement['down']:
			self.movements = True
		else :
			self.movements = False

		self.animate(seconds,camera)

	def animate (self,seconds,camera):
		#Animate the man, call rotate()
		#FEETS
		if self.movement['up']:
			self.feet = self.walk_feet_up.play_circle(seconds)
		if self.movement['down']:
			self.feet = self.walk_feet_down.play_circle(seconds)
		if self.movement['left']:
			self.feet = self.walk_feet_left.play_circle(seconds)
		if self.movement['right']:
			self.feet = self.walk_feet_right.play_circle(seconds)
		if not self.movements:
			self.feet = self.walk_feet_up.reset()

		#BODY 
		if self.curr_ability.play == True:
				self.curr_ability.animate(seconds,self,camera)
		elif self.movements:
			self.SourceImage = self.walk_body.play_circle(seconds)
		else:
			self.SourceImage = self.walk_body.reset()
				
		self.rotate(camera)

		# Merge FEETS and BODY 
		self.merged = pygame.Surface((self.rect.width*2,self.rect.height*2),pygame.SRCALPHA)
		self.merged.blit(self.feet,((self.rect.width-self.bbox.width) /2 +2,(self.rect.height-self.bbox.height) /2))
		self.merged.blit(self.image,(0,0))
		self.image = self.merged

	def move (self):
		
		if self.movement['left']:
			self.bbox.x -= 1
		if self.movement['right']:
			self.bbox.x += 1

		if self.movement['up']:
			self.bbox.y -= 1
		if self.movement['down']:
			self.bbox.y += 1

		# recalculate the center after moving
		self.center = (self.bbox.x + int(self.bbox.width / 2),self.bbox.y + int(self.bbox.height / 2))

	# Allow a man to go to a given point
	def go_to (self,grid,goal,screen,camera,delay):

		stack = 1

		if self.init:
			start = (self.center[0]//self.div,self.center[1]//self.div)
			self.path = []
			self.path_step = 0
			self.path = a_star_search(grid,start,goal)
			self.init = False
			self.reached = False
			self.rotate_point = ((self.path[-1][0]*self.div)+32,(self.path[-1][1]*self.div)+32)

		#while man as not reached destination
		if not self.reached:
			
			#Check if man as reached destination, if so reinitialize the variables 
			if self.path_step >= len(self.path):
				self.reached = True
				self.init = True
				self.target = None
				self.path = []
				self.path_step = 0
				self.movement = {'left': False,'right': False, 'up': False, 'down': False}
				self.can_spend = True
				self.range_need_refresh = True

			#if man as not reached destination to final goal
			else:
				#for every pixel in speed, move of one pixel and check if IA is on the current goal
				#if so the current goal change to the next
				for pixel in range(self.speed + int((self.speed*delay))):

					#get the current goal and the distance from it
					current_node = self.path[self.path_step]
					(dx,dy) = (current_node[0]*self.div+32 - self.center[0] , current_node[1]*self.div+32 - self.center[1])

					#set movement in fuction of the distance to the current goal
					if dx > stack:
						self.movement['right'] = True
					elif dx < (stack):
						self.movement['right'] = False

					if dx < -(stack):
						self.movement['left'] = True
					elif dx > -(stack):
						self.movement['left'] = False

					if dy > stack:
						self.movement['down'] = True
					elif dy < (stack):
						self.movement['down'] = False

					if dy < -stack:
						self.movement['up'] = True
					elif dy > -(stack):
						self.movement['up'] = False

					#move by one pixel
					self.move()
					(dx,dy) = ((current_node[0]*self.div)+32 - self.center[0] , current_node[1]*self.div+32 - self.center[1])

					#check if man as reached current goal
					if abs(dx) <= stack and abs(dy) <= stack:
						self.path_step += 1
						break
		
	def rotate (self,camera):

		self.angle = 180 + math.atan2(self.center[0] - camera.x - self.rotate_point[0], self.center[1] - camera.y - self.rotate_point[1])*180/math.pi
		self.image = pygame.transform.rotozoom(self.SourceImage,self.angle,1)
		self.rect = self.image.get_rect(center = self.center)

"""
Initialise and update bullets
WORK IN PROGRESS
"""
class Bullet (pygame.sprite.Sprite):

	def __init__(self,camera,man):

		super(Bullet,self).__init__()

		self.image = pygame.Surface([4,4])
		self.image.fill(black)

		self.rect = self.image.get_rect()
		self.margin = 100

		self.speed = 50

		#self.dest = man.rotate_point

		#place the bullet at the end of the gun
		self.rect.x = man.center[0] + math.cos((man.angle-90)* (math.pi / 180.0))*(44)
		self.rect.y = man.center[1] + math.sin(-(man.angle-90)* (math.pi / 180.0))*(44)
		
		#velocity knowing the angle
		self.dx = math.cos((man.angle-90) * (math.pi / 180.0)) * self.speed
		self.dy = math.sin(-(man.angle-90) * (math.pi / 180.0)) * self.speed

	def move (self,delay):
		self.rect.x += self.dx + (self.dx*delay)
		self.rect.y += self.dy + (self.dx*delay)

	def update(self,screen,camera,delay):
		# need to check hits here
		self.move(delay)
		for r in All_speakable_npcs:
			if self.rect.colliderect(r.bbox):
				All_sprites_list.remove(self)
				r.life -= 1
		if self.rect.x-camera.x > screen.width+self.margin or self.rect.y-camera.y > screen.height+self.margin or self.rect.x-camera.x < 0-self.margin or self.rect.y-camera.y < 0-self.margin:
			All_sprites_list.remove(self)
		for coll in All_collision_list:
			if self.rect.colliderect(coll.rect):
				All_sprites_list.remove(self)
		#screen.gameArea.blit(self.image, self.rect)

class Shot(object):
	def __init__(self,path):
		self.gun_get = Animation(.07,(Spritesheet(os.path.abspath(path+'Get_gun.png')).images_at([(0,0,64,64),(64,0,64,64),(128,0,64,64)])))
		self.gun_arm = Animation(.1,(Spritesheet(os.path.abspath(path+'Trigger_gun.png')).images_at([(64,0,64,64)])))	

		self.type = 1

		self.play = False
		self.select = False
		self.max_probability = 50

	def shoot(self):
		#target_bonus = target.get_touch_prob(man.center)
		#target_def_probability = target_bonus[1]
		probability = self.max_probability
		res = random.randrange(1, 100, 1)

		if res <= self.max_probability:
			self.succes = True
		else:
			self.succes = False

	def animate(self,seconds,man,camera):
		if self.play:
			man.SourceImage = self.gun_get.play_line(seconds)
			if self.gun_get.done:
				man.SourceImage = self.gun_arm.play_line(seconds)
				if self.gun_arm.done:
					if man.bullets > 0:
						bullet = Bullet(camera,man)
						All_sprites_list.add(bullet)
						All_bullet_list.add(bullet)
						man.bullets -= 1
						self.shoot()
					self.gun_arm.reset()
					self.gun_get.reset()
					self.play = False
					man.can_spend = True
					man.range_need_refresh = True
			else :
				self.gun_arm.reset()
		else :
			self.gun_get.reset()
			self.arm_gun = False