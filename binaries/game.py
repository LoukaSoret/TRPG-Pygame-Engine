#import pygame module and other usefull modules
import os,pygame, sys, random, math, time
import sprites,renderer

from pygame.locals import *

#import tmx file reader
from pytmx import *
from pytmx.util_pygame import load_pygame

#init pygame
pygame.init()

#Colors
black = (0,0,0)
white = (255,255,255)

#FPS
target_fps = 60

filename = os.path.abspath('map_V1.tmx')

"""
Set up everything
"""
def init_game ():
	# set up global variables and import medias

	#import classes from render.py
	from renderer import Screen,Camera,Renderer,Bbox,light,light_source,Squad_sight,MHUD, Abilities_HUD, Squad
	from sprites import Man,HUD

	global screen, renderer, camera,HUD, map_grid, mHUD, abilities_HUD
	global squad, All_sprites_list, all_squads, ennemies
	global lightsource, light, squad_sight

	All_sprites_list = sprites.All_sprites_list
	All_speakable_npcs = sprites.All_speakable_npcs

	#display the screen
	screen = Screen()
	screen.display()

	#init the camera
	camera = Camera()

	#init the HUD
	HUD = HUD(screen)

	#load the map
	renderer = Renderer()
	renderer.load_map(filename)

	#init bboxs
	bbox = Bbox()
	bbox.load(renderer)

	#define the grid for Astar
	map_grid = renderer.define_map_grid()

	mHUD = MHUD(screen,map_grid)
	abilities_HUD = Abilities_HUD(screen,map_grid)

	#load light
	light = light(screen,map_grid,100)

	#init the squad
	squad = Squad(screen,[Man(screen,camera,map_grid,"spritesheets/player/","Ham",(0,64)),Man(screen,camera,map_grid,"spritesheets/player/","Philip",(64,0)),Man(screen,camera,map_grid,"spritesheets/player/","Lebowsky",(64,64)),Man(screen,camera,map_grid,"spritesheets/player/","Theman",(0,0))],map_grid)
	ennemies = Squad(screen,[Man(screen,camera,map_grid,"spritesheets/player/","bad_boi",(512,576))],map_grid)
	all_squads = [squad,ennemies]
	squad_sight = Squad_sight(screen,camera,squad)
	#renderer.load_objects()

	renderer.load_background(screen,camera,map_grid)
	renderer.load_forground(screen,camera,map_grid)

	for s in all_squads:
		s.spriteGroup.update(screen,camera,0,0,map_grid)

	light.update(screen,camera,[member.light_source for member in squad.members],True)


	#enter the main game loop
	game_loop()

"""
Main game loop 
"""
def game_loop():
	gameExit = False
		
	prev_time = time.time()
	seconds = 0
	delay = 0
	fps = 0
	ratio = 0
	current_squad = squad
	select_s = 0
	select_e = 0
	selected_ennemy  = ennemies.members[0]
	selected_squad_member = current_squad.members[0]
	nb_turns = 1

	while not gameExit:

		"""
		______________________________________________________________________________________________

		EVENT PROCESSING
		______________________________________________________________________________________________
		
		"""

		mouse_position = pygame.mouse.get_pos()

		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()

			if event.type  == pygame.KEYDOWN:
				if event.key == K_ESCAPE:
					pygame.quit()
					sys.exit()
				if event.key in (K_LEFT, K_q):
					camera.movement['left'] = True
					camera.movement['right'] = False
				if event.key in (K_RIGHT, K_d):
					camera.movement['right'] = True
					camera.movement['left'] = False
				if event.key in (K_UP, K_z):
					camera.movement['up'] = True
					camera.movement['down'] = False
				if event.key in (K_DOWN, K_s):
					camera.movement['down'] = True
					camera.movement['up'] = False

				if event.key == K_l:
					selected_squad_member.life -= 1
					if selected_squad_member.life < 0:
						selected_squad_member.life = 3
				
				if event.key == K_r:
					selected_squad_member.bullets = 6
				
				if event.key in (K_AMPERSAND,K_1):
					if selected_squad_member.abilities[0].select:
						selected_squad_member.abilities[0].select = False
					else :
						selected_squad_member.abilities[0].select = True

				if event.key == K_LSHIFT :
					if selected_squad_member.target == None and not selected_squad_member.abilities[0].play:
						selected_squad_member.abilities[0].select = False
						select_s += 1
						selected_squad_member = current_squad.members[(select_s%len(current_squad.members))-1]
						selected_squad_member.range_need_refresh = True
						camera.target = selected_squad_member
						while selected_squad_member.current_AP <= 0 and selected_squad_member.target == None: 
							select_s += 1
							selected_squad_member = current_squad.members[(select_s%len(current_squad.members))-1]
							selected_squad_member.range_need_refresh = True
							camera.target = selected_squad_member

			if event.type == pygame.KEYUP:
				if event.key in (K_LEFT, K_q):
					camera.movement['left'] = False
				if event.key in (K_RIGHT, K_d):
					camera.movement['right'] = False
				if event.key in (K_UP, K_z):
					camera.movement['up'] = False
				if event.key in (K_DOWN, K_s):
					camera.movement['down'] = False

			if event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 1:
					if selected_squad_member.abilities[0].select:
						selected = abilities_HUD.mouse_on_target(screen,camera,mouse_position,map_grid)
						if selected != None:
							selected_squad_member.abilities[0].play = True
							selected_squad_member.abilities[0].select = False
							selected_squad_member.rotate_point = selected
					else:
						selected_squad_member.target = (((mouse_position[0]+camera.x+screen.xzoom)//(map_grid.nodeSize*(abs(2 - screen.zoom)))),((mouse_position[1]+camera.y+screen.yzoom)//(map_grid.nodeSize*(abs(2 - screen.zoom)))))
				elif event.button == 4 and screen.zoom > screen.minZoom:
					screen.zoom -= 0.02
					screen.zoomIndex -= 1
				elif event.button == 5 and screen.zoom < screen.maxZoom:
					screen.zoom += 0.02
					screen.zoomIndex += 1



		"""
		______________________________________________________________________________________________

		UPDATE EVERYTHING
		______________________________________________________________________________________________
		
		"""
		
		screen.update()
		camera.update(screen,ratio,map_grid)
		current_squad.spriteGroup.update(screen,camera,ratio,seconds,map_grid)
		squad_sight.update(screen,camera,current_squad)
		All_sprites_list.update(screen,camera,delay)

		light.update(screen,camera,[member.light_source for member in current_squad.members])
		HUD.update(seconds, screen, selected_squad_member.life, selected_squad_member.bullets,fps)
		if selected_squad_member.abilities[0].select:
			abilities_HUD.update(camera,selected_squad_member.abilities[0],mouse_position,squad_sight,[ ennemie.center for ennemie in ennemies.members],selected_squad_member,screen,map_grid)
		else:
			mHUD.update(screen,camera,mouse_position,map_grid,selected_squad_member.walk_range,selected_squad_member.run_range,selected_squad_member.center,selected_squad_member.target,selected_squad_member.abilities[0].select)


		"""
		______________________________________________________________________________________________

		DRAW EVERYTHING
		______________________________________________________________________________________________
		"""
		renderer.draw_background(screen,camera)
		if not selected_squad_member.abilities[0].select:
			mHUD.draw(screen,camera)

		for s in all_squads:
			s.draw(screen,camera)

		if selected_squad_member.abilities[0].select:
			abilities_HUD.draw(screen,camera)

		#renderer.draw_list(screen,All_sprites_list,camera,map_grid)

		renderer.draw_forground(screen,camera)
		light.draw(screen,camera)
		HUD.draw(screen)
		
		pygame.display.flip()


		"""
		______________________________________________________________________________________________

		GAME MECHANICS
		______________________________________________________________________________________________
		
		"""
		if selected_squad_member.current_AP <= 0 and selected_squad_member.target == None: 
			select_s += 1
			selected_squad_member = current_squad.members[(select_s%len(current_squad.members))-1]
			selected_squad_member.range_need_refresh = True
			camera.target = selected_squad_member

		if all((member.current_AP==0 and member.target==None) for member in current_squad.members):
			nb_turns += 1

			current_squad = squad

			for member in current_squad.members:
				member.current_AP = member.total_AP
				member.can_spend = True

		#TIME
		curr_time = time.time()#so now we have time after processing
		diff = curr_time - prev_time #frame took this much time to process and render
		seconds = diff
		delay = max((1.0/target_fps) - diff, 0)#if we finished early, wait the remaining time to desired fps, else wait 0 ms!
		ratio = abs(min((1.0/target_fps) - diff, 0.000000001))/(1.0/target_fps)#if we are late apply this ratio to every speed 
		time.sleep(delay)
		fps = 1.0/(delay + diff)#fps is based on total time ("processing" diff time + "wasted" delay time)
		
		prev_time = curr_time

init_game()

pygame.quit()
sys.exit()