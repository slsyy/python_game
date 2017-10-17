__author__ = 'Krystian'
import pygame
from pygame.locals import *  # keyboards keys map
import sys
import math
import random
from enum import Enum


class GameObject(pygame.sprite.Sprite):
    """
        Base class for player class and every object which interact with player/
    """
    def __init__(self, image, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()  # position and size for draw()
        self.rect.move_ip(pos[0], pos[1])
        self.pos = list(pos)
        self.velocity = [0.0, 0.0]
        self.max_velocity = 300.
        self.friction = 3000.
        self.acceleration = 4000.
        self.max_hp = 0
        self.hp = 0
        self.alive = True
        self.mass = 1

    def hurt(self, hurt_hp):
        self.hp -= hurt_hp

    def kill(self):
        self.alive = False

    def is_alive(self):
        return self.alive

    def update(self, dt):
        pass

    def go_left(self, dt):
        if -(self.velocity[0] - self.acceleration * dt) > self.max_velocity:
            if -self.velocity[0] < self.max_velocity:
                self.velocity[0] = - self.max_velocity
        else:
            self.velocity[0] -= self.acceleration * dt

    def go_right(self, dt):
        if self.velocity[0] + self.acceleration * dt > self.max_velocity:
            if self.velocity[0] < self.max_velocity:
                self.velocity[0] = self.max_velocity
        else:
            self.velocity[0] += self.acceleration * dt

    def go_up(self, dt):
        if -(self.velocity[1] - self.acceleration * dt) > self.max_velocity:
            if -self.velocity[1] < self.max_velocity:
                self.velocity[1] = - self.max_velocity
        else:
            self.velocity[1] -= self.acceleration * dt

    def go_down(self, dt):
        if self.velocity[1] + self.acceleration * dt > self.max_velocity:
            if self.velocity[1] < self.max_velocity:
                self.velocity[1] = self.max_velocity
        else:
            self.velocity[1] += self.acceleration * dt


class PopUpLabel(GameObject):
    """
        Pop-up texts labels, which indicate in-game situations
    """
    def __init__(self,image,pos):
        GameObject.__init__(self, image, pos)
        self.velocity =[0,-20.0]
        self.image = self.image.convert_alpha()
        self.live_time = 1.0
        self.remaining_live_time = self.live_time

    def update(self,dt):
        GameObject.update(self, dt)
        self.remaining_live_time -= dt
        self.pos[1] += self.velocity[1] * dt
        self.rect[0] = int(self.pos[0])
        self.rect[1] = int(self.pos[1])
        if  self.remaining_live_time < 0:
            self.kill()#suicade


class Player(GameObject):
    """
        Main character class
    """
    def __init__(self, image, low_hp_image, very_low_hp_image, pos, game_object_group):
        GameObject.__init__(self, image, pos)

        self.game_object_group = game_object_group
        self.low_hp_image = low_hp_image
        self.very_low_hp_image = very_low_hp_image
        self.normal_image = image
        self.max_hp = 30
        self.hp = 30
        self.min_hp = 15
        self.immortal_time_duration = 0.3
        self.immortal_time_counter = 0.0
        self.immortal = False
        self.gold = 0
        self.mass = 1
        self.max_attack_level = 1.0
        self.attack_level = self.max_attack_level
        self.attack_restore_speed = 0.15
        self.new_attack_wave_delay_duration = 0.3
        self.new_attack_wave_delay = self.new_attack_wave_delay_duration

    def restore_attack(self):
        self.attack_level = self.max_attack_level

    def add_gold(self, value):
        self.gold += value

    def attack(self):#new AttackWave
        if (self.attack_level / self.max_attack_level >= 0.5) and self.new_attack_wave_delay < 0.0:
            self.game_object_group.add(AttackWave(self))
            self.new_attack_wave_delay = self.new_attack_wave_delay_duration
            self.attack_level -= self.max_attack_level * 0.5

    def add_hp(self, value):
        self.hp += value
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def is_immortal(self):
        return self.immortal

    def update(self, dt):
        GameObject.update(self, dt)
        self.new_attack_wave_delay -= dt
        self.attack_level += dt * self.attack_restore_speed
        if self.attack_level > self.max_attack_level:
            self.attack_level = self.max_attack_level

        if self.immortal:
            self.immortal_time_counter += dt
            if self.immortal_time_counter > self.immortal_time_duration:
                self.immortal = False

        if self.hp == self.min_hp:
            self.image = self.very_low_hp_image
        elif (self.max_hp - self.min_hp) / 2 + self.min_hp > self.hp:
            self.image = self.low_hp_image
        else:
            self.image = self.normal_image

    def hurt(self, hurt_hp):
        if not self.immortal:
            GameObject.hurt(self, hurt_hp)
            self.immortal_time_counter = 0.0
            self.immortal = True
            if self.hp < self.min_hp:#then game over
                self.alive = False
                self.game_object_group.app.game_mode = App.GameMode.GAME_END


class AttackWave(GameObject):
    """
        Circle created by player.It can hurt and bounce enemy.
    """
    def __init__(self, player):
        GameObject.__init__(self, pygame.Surface((1, 1)), [0, 0])
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.player = player
        self.pos = [0, 0]
        self.r = 0.0
        self.max_r = 120.0
        self.attacked_by_self = []#list of enemys who has hit by wave
        self.damage = 1.25

    def attack(self, game_object):#deal damage to game_object
        game_object.hurt(self.get_current_damage())
        self.attacked_by_self.append(game_object)

    def get_current_damage(self):
        return self.damage * (1.0 - (self.r / self.max_r))

    def update(self, dt):
        GameObject.update(self, dt)
        self.r += self.max_r * 2. * dt
        if self.r > self.max_r:
            self.r = self.max_r
            self.kill()

        # creating circle
        INT_2R = int(2 * self.r)
        self.image = pygame.Surface((INT_2R, INT_2R))
        COLOR = (40, 70, 255)
        TRANSPARENT = (255, 0, 255)
        self.image.fill(TRANSPARENT)
        self.image.set_colorkey(TRANSPARENT)
        pygame.draw.circle(self.image, COLOR, (int(self.r), int(self.r)), int(self.r))
        pygame.draw.circle(self.image, (40, 40, 128), (int(self.r), int(self.r)), int(self.r)
                           , int(self.r) > 3 if 3 else 0)#throw exception if border > r
        self.image.set_alpha(100 * (1.1 - (self.r / self.max_r)))
        self.rect = pygame.Rect([self.player.rect[x] + self.player.rect[x + 2] / 2 - self.r
                                 for x in range(len(self.player.pos))],
                                (INT_2R, INT_2R))#rect for draw and circle_colission
        self.radius = int(self.r)#for cicle_collision

    def bounce(self, object):
        direction_vec = [0.0, 0.0]
        vec_length = lambda vec: (vec[0] ** 2 + vec[1] ** 2) ** 0.5
        normalize = lambda vec: [vec[0] / vec_length(vec), vec[1] / vec_length(vec)]
        for x in range(len(self.player.pos)):
            direction_vec[x] = object.pos[x] - self.player.pos[x]
            direction_vec = normalize(direction_vec)
            object.velocity[x] += (1 - (self.r / self.max_r)) * 1500 *\
                                  direction_vec[x] / object.attack_wave_bounce_mass


class Enemy(GameObject):
    """
        Base class for character, which deal damage to player
    """
    def __init__(self, image, pos, game_system_group):
        GameObject.__init__(self, image, pos)
        self.game_system_group = game_system_group
        self.move_cycle_timer = 0.0
        self.damage = 1
        self.attack_wave_bounce_mass = 1
        self.min_hp = 1

    def update(self, dt):
        GameObject.update(self, dt)
        if self.hp < self.min_hp:
            self.kill()

    def deal_damage(self, game_object):
        game_object.hurt(self.damage)


class EnemyWeak(Enemy):
    """
        Enemy type with seperate AI.
    """
    class EnemyWeakMoveCycle(Enum):#Move cycle, which change after move_cycle_duration time
        NONE_X = 0
        LEFT = 1
        RIGHT = 2
        NONE_Y = 3
        UP = 4
        DOWN = 5

    def __init__(self, image, pos, game_system_group):
        Enemy.__init__(self, image, pos, game_system_group)
        self.max_hp = 2
        self.hp = self.max_hp
        self.mass = 0.25
        self.move_cycle_duration = 0.55
        self.damage = 1
        self.current_move_cycle_x = EnemyWeak.EnemyWeakMoveCycle.NONE_X
        self.current_move_cycle_y = EnemyWeak.EnemyWeakMoveCycle.NONE_Y

    def update(self, dt):
        Enemy.update(self, dt)
        self.move_cycle_timer += dt
        if self.move_cycle_timer > self.move_cycle_duration:#choose by randomizer direction where enemy will go
            self.move_cycle_timer = 0
            self.current_move_cycle_x = EnemyWeak.EnemyWeakMoveCycle(random.randint(0, 2))
            self.current_move_cycle_y = EnemyWeak.EnemyWeakMoveCycle(random.randint(3, 5))
        if self.current_move_cycle_x == EnemyWeak.EnemyWeakMoveCycle.LEFT:
            self.go_left(dt)
        elif self.current_move_cycle_x == EnemyWeak.EnemyWeakMoveCycle.RIGHT:
            self.go_right(dt)
        if self.current_move_cycle_y == EnemyWeak.EnemyWeakMoveCycle.UP:
            self.go_up(dt)
        elif self.current_move_cycle_y == EnemyWeak.EnemyWeakMoveCycle.DOWN:
            self.go_down(dt)


class EnemyStrong(Enemy):
    """
        Enemy type with seperate AI.
    """
    def __init__(self, image, pos, game_system_group):
        Enemy.__init__(self, image, pos, game_system_group)
        self.max_hp = 4
        self.hp = self.max_hp
        self.mass = 10
        self.max_velocity = 100.
        self.move_cycle_duration = 3.
        self.target_pos = [0.0, 0.0]
        self.damage = 2
        self.attack_wave_bounce_mass = 1

    def update(self, dt):
        Enemy.update(self, dt)
        self.move_cycle_timer += dt
        if self.move_cycle_timer > self.move_cycle_duration:
            self.move_cycle_timer = 0
            if random.randint(1, 1) == 1:
                self.target_pos = self.game_system_group.player.pos

        if self.game_system_group.player.pos[0] < self.pos[0]:#follow player
            self.go_left(dt)
        else:
            self.go_right(dt)
        if self.game_system_group.player.pos[1] < self.pos[1]:
            self.go_up(dt)
        else:
            self.go_down(dt)


class Bonus(GameObject):
    """
        Base class for all bonus object which can by take by player.
    """
    def __init__(self, image, pos):
        GameObject.__init__(self, image, pos)

    def use(self, player):
        pass


class Gold(Bonus):
    """
        Gold bonus which increase player gold.
    """
    def __init__(self, image, pos, value):
        Bonus.__init__(self, image, pos)
        self.time_to_live = 3.0 + random.random() * 5.0
        self.value = value

    def update(self, dt):
        GameObject.update(self, dt)
        self.time_to_live -= dt
        if self.time_to_live < 0:
            self.alive = False

    def use(self, player):
        player.add_gold(self.value)

    def __str__(self):
        return str(self.value)+" Gold"


class HpBonus(Bonus):
    """
        HP bonus which increase player HP.
    """
    def __init__(self, image, pos, value):
        Bonus.__init__(self, image, pos)
        self.time_to_live = 1.0 + random.random() * 4.0
        self.value = value

    def update(self, dt):
        GameObject.update(self, dt)
        self.time_to_live -= dt
        if self.time_to_live < 0:
            self.alive = False

    def use(self, player):
        player.add_hp(self.value)

    def __str__(self):
        return str(self.value)+" HP"


class AttackBonus(Bonus):
    """
        AttackBonus bonus which increase player Attack to max value.
    """
    def __init__(self, image, pos):
        Bonus.__init__(self, image, pos)
        self.time_to_live = 2.0 + random.random() * 3.0

    def update(self, dt):
        GameObject.update(self, dt)
        self.time_to_live -= dt
        if self.time_to_live < 0:
            self.alive = False

    def use(self, player):
        player.restore_attack()

    def __str__(self):
        return "attack full restore"


class GameObjectsGroup(pygame.sprite.Group):
    """
        Container for storing,drawing and updating GameObjects.
    """
    class SpawnEngine():
        """
            It spawn objects like Enemyof Bonus on play_area
        """
        def __init__(self, game_object_group):
            self.game_objects_group = game_object_group
            self.EnemyWeak_spawn_delay = 0.0
            self.gold_spawn_delay = 0.0
            self.hp_spawn_delay = 0.0
            self.attack_bonus_spawn_delay = 0.0

        def spawn(self, dt):
            # Enemy spawn
            self.EnemyWeak_spawn_delay -= dt
            if self.EnemyWeak_spawn_delay <= 0.0:
                self.EnemyWeak_spawn_delay += random.random() * 5 + 3.0
                enemy_position = self.game_objects_group.get_random_pos_on_game_arena();

                rand_result = random.randint(0, 20)
                if rand_result < 3:
                    speed_enemy = EnemyWeak(self.game_objects_group.app.get_resource("enemy3"), enemy_position,
                                            self.game_objects_group)
                    speed_enemy.max_velocity *= 1.3#differences between normal and speed enemy
                    speed_enemy.move_cycle_duration /= 5.0
                    speed_enemy.mass /= 1.2
                    speed_enemy.acceleration *= 2.
                    self.game_objects_group.add(speed_enemy)
                elif rand_result < 6:
                    self.game_objects_group.add(
                        EnemyStrong(self.game_objects_group.app.get_resource("enemy2"), enemy_position,
                                    self.game_objects_group))
                else:
                    self.game_objects_group.add(
                        EnemyWeak(self.game_objects_group.app.get_resource("enemy1"), enemy_position,
                                  self.game_objects_group))
            # Gold spawn
            self.gold_spawn_delay -= dt
            if self.gold_spawn_delay <= 0.0:
                self.gold_spawn_delay += 0.25 + random.random() * 2.0
                gold_position = self.game_objects_group.get_random_pos_on_game_arena();
                if random.randint(1, 10) == 1:#random amount of gold
                    if random.randint(1, 10) == 1:
                        gold_value = random.randint(80, 100)
                    else:
                        gold_value = random.randint(40, 80)
                else:
                    gold_value = random.randint(10, 30)
                self.game_objects_group.add(
                    Gold(self.game_objects_group.app.get_resource("gold"), gold_position, gold_value))
            # bonus HpPoints spawn
            self.hp_spawn_delay -= dt
            if self.hp_spawn_delay <= 0.0:
                self.hp_spawn_delay += 2.5 + random.random() * 10.0
                hp_position = self.game_objects_group.get_random_pos_on_game_arena();
                self.game_objects_group.add(
                    HpBonus(self.game_objects_group.app.get_resource("hp"), hp_position, 1))
            # bonus AttackBonus spawn
            self.attack_bonus_spawn_delay -= dt
            if self.attack_bonus_spawn_delay <= 0.0:
                self.attack_bonus_spawn_delay += 2. + random.random() * 10.0
                attack_bonus_position = self.game_objects_group.get_random_pos_on_game_arena();
                self.game_objects_group.add(
                    AttackBonus(self.game_objects_group.app.get_resource("attack"), attack_bonus_position))

    def __init__(self, play_area, app):
        self.play_area = play_area
        pygame.sprite.Group.__init__(self)
        self.spawn_engine = GameObjectsGroup.SpawnEngine(self)
        self.pop_up_label_group = pygame.sprite.Group()
        self.app = app

    def add_pop_up_label(self,pop_up_label):
        self.pop_up_label_group.add(pop_up_label)

    def add_player(self, player):
        self.add(player)
        self.player = player

    def bounce(self, a, b):
        """
            Bounce GameObject a from b by using conservation of momentum
        """
        momentum = [0.0, 0.0]
        direction_vec = [0.0, 0.0]
        vec_length = lambda vec: (vec[0] ** 2 + vec[1] ** 2) ** 0.5
        normalize = lambda vec: [vec[0] / vec_length(vec), vec[1] / vec_length(vec)]
        for x in range(len(a.pos)):
            momentum[x] = a.velocity[x] * a.mass + b.velocity[x] * b.mass
            direction_vec[x] = b.pos[x] - a.pos[x]
            direction_vec = normalize(direction_vec)
            momentum_length = vec_length(momentum)
            for x in range(len(a.pos)):
                a.velocity[x] = -direction_vec[x] * momentum_length / a.mass
                b.velocity[x] = direction_vec[x] * momentum_length / b.mass

    def draw(self,surface):
        pygame.sprite.Group.draw(self,surface)
        self.pop_up_label_group.draw(surface)

    def update(self, dt):
        """
            Call update(dt) for every GameObject, and use relations between them.
        """
        self.spawn_engine.spawn(dt)
        to_remove = []
        for object in pygame.sprite.Group.sprites(self):
            object.update(dt)  # update object
            if not object.is_alive():
                to_remove.append(object)  # remove if  isn't  alive
                continue
            for x in range(len(object.velocity)):  # friction
                if object.velocity[x] > 0.0:
                    object.velocity[x] -= object.friction * dt
                    if object.velocity[x] < 0.0:
                        object.velocity[x] = 0.0
                elif object.velocity[x] < 0.0:
                    object.velocity[x] += object.friction * dt
                    if object.velocity[x] > 0.0:
                        object.velocity[x] = 0.0

            border_hit = False
            for i in range(len(object.pos)):  # if object hit border of play_area
                if object.pos[i] < self.play_area[i]:  # play_area = [point_x,point_y,w,h]
                    object.pos[i] = self.play_area[i]
                    object.velocity[i] = -1.0 * object.velocity[i]
                    border_hit = True
                # i+1,i+2 -> 3,4 -> right and down wall
                elif object.pos[i] + object.rect[i + 2] > self.play_area[i + 2]:
                    object.pos[i] = self.play_area[i + 2] - object.rect[i + 2]
                    object.velocity[i] = -1.0 * object.velocity[i]
                    border_hit = True
            if border_hit and isinstance(object, Enemy):
                object.move_cycle_timer = object.move_cycle_duration + dt

            # calculation new position -> pos = velocity * dt
            object.pos = [object.pos[0] + object.velocity[0] * dt, object.pos[1] + object.velocity[1] * dt]
            if not isinstance(object, AttackWave):
                object.rect[0] = int(object.pos[0])
                object.rect[1] = int(object.pos[1])

        # player<->enemy
        if not self.player.is_immortal():
            for object in pygame.sprite.Group.sprites(self):
                if isinstance(object, Enemy):
                    if pygame.sprite.collide_rect(self.player, object):
                        object.deal_damage(self.player)
                        dmg = app.get_resource("small_font").render(
                        "-"+str(object.damage)+" HP", True, (255, 25, 25))
                        self.add_pop_up_label(PopUpLabel(dmg,self.player.pos))
                        self.bounce(self.player, object)

        # attack_wave <-> enemy
        for attack_wave in pygame.sprite.Group.sprites(self):
            if not isinstance(attack_wave, AttackWave):
                continue
            for enemy in pygame.sprite.Group.sprites(self):
                if not isinstance(enemy, Enemy):
                    continue
                if pygame.sprite.collide_circle(attack_wave, enemy) and \
                        not enemy in attack_wave.attacked_by_self:
                    attack_wave.attack(enemy)
                    dmg = app.get_resource("small_font").render(
                        "-"+str(round(attack_wave.get_current_damage(), 2))+" dmg", True, (239, 75, 117))
                    self.add_pop_up_label(PopUpLabel(dmg,enemy.pos))
                    attack_wave.bounce(enemy)
        #player <-> bonus
        for object in pygame.sprite.Group.sprites(self):
            if isinstance(object, Bonus) and pygame.sprite.collide_circle(self.player, object):
                object.use(self.player)
                bonus = app.get_resource("small_font").render(
                        "+"+str(object), True, (100, 255, 100))
                self.add_pop_up_label(PopUpLabel(bonus,object.pos))
                to_remove.append(object)

        for object in to_remove:
            object.remove(self)

        pop_up_label_to_remove = []
        for pop_up_label in pygame.sprite.Group(self.pop_up_label_group):
            pop_up_label.update(dt)
            if not pop_up_label.is_alive():
                pop_up_label_to_remove.append(pop_up_label)
        for x in pop_up_label_to_remove:
            x.remove(self.pop_up_label_group)

    def get_random_pos_on_game_arena(self):
        return [random.randint(self.play_area[0], self.play_area[2]),
                random.randint(self.play_area[1], self.play_area[3])]


class App:
    """
        Main application class.
        It is responsible for pygame initialization,resource loading,events handling,drawing and updating
    """
    class GameMode(Enum):
        GAME_BEGIN = 0
        GAME_MAIN = 1
        GAME_END = 2

    def __init__(self, window_size):
        pygame.init()
        self.window = pygame.display.set_mode(window_size)  # create game display and init video mode
        self.resource = dict()
        try:  # load resources
            self.load_resource("background", "png")
            self.load_resource("ects_info", "png")
            self.load_resource("attack_info", "png")
            self.load_resource("ects_bar_full", "png")
            self.load_resource("ects_bar_empty", "png")
            self.load_resource("gold_info", "png")
            self.load_resource(file_name="font", extension="ttf", size=23, name="big_font")
            self.load_resource(file_name="font", extension="ttf", size=15, name="medium_font")
            self.load_resource(file_name="font", extension="ttf", size=14, name="small_font")
            self.load_resource(file_name="font", extension="ttf", size=32, name="huge_font")
            self.load_resource("player", "png")
            self.load_resource("player_low_hp", "png")
            self.load_resource("player_very_low_hp", "png")
            self.load_resource("enemy1", "png")
            self.load_resource("enemy2", "png")
            self.load_resource("enemy3", "png")
            self.load_resource("gold", "png")
            self.load_resource("hp", "png")
            self.load_resource("attack", "png")
            self.load_resource("wasd", "png")
            self.load_resource("space", "png")
        except Exception as exception:
            print("fail.")
            print(exception)
            sys.exit(0)

        self.done = False#for main loop
        self.draw_surface = pygame.display.get_surface()
        pygame.display.set_caption("ECTS", "")  # setting display name
        self.clock = pygame.time.Clock()#time system
        self.black_filter = pygame.Surface((self.window.get_width(), self.window.get_height()))
        self.black_filter.fill((0, 0, 0))
        self.black_filter.set_alpha(180)
        self.init_game()
        self.game_mode = App.GameMode.GAME_BEGIN

    def init_game(self):
        self.game_objects_group = GameObjectsGroup(
            [0, 100, self.window.get_width(), self.window.get_height()], self)
        play_area_center = (self.game_objects_group.play_area[2] / 2, self.game_objects_group.play_area[3] / 2)
        self.player = Player(self.get_resource("player"), self.get_resource("player_low_hp"),
                             self.get_resource("player_very_low_hp"),
                             play_area_center,
                             self.game_objects_group)

        self.game_objects_group.add_player(self.player)
        self.gold_goal = 2000 #game goal

    def load_resource(self, file_name, extension, name="", size=10):
        if name == "":
            name = file_name
        print("Loading " + file_name + "." + extension + " and.... ", end="")
        if (extension.upper() == "PNG"):
            # convert_alpha convert loaded surface into surface with mode like display_surface
            # it's huge fps increase
            self.resource[name] = pygame.image.load(file_name + "." + extension).convert_alpha()
        elif (extension.upper() == "TTF"):
            self.resource[name] = pygame.font.Font(file_name + "." + extension, size)
        print("success.")

    def get_resource(self, name):
        try:
            return self.resource[name]
        except Exception as exception:
            print("Cannot get resource " + str(exception) + ".")
            sys.exit(0)

    def events_loop(self, events):
        for event in events:
            if event.type == QUIT:
                self.done = True

    def draw(self):
        """
            Main draw function.
        :return: None
        """
        # background
        self.draw_surface.blit(self.get_resource("background"), (0, self.game_objects_group.play_area[1]))

        # info bar fill
        self.draw_surface.fill((35, 9, 9),
                               pygame.Rect(0, 0, self.game_objects_group.play_area[2],
                                           self.game_objects_group.play_area[1]))
        # info bar border
        pygame.draw.rect(self.draw_surface, (0, 0, 0),
                         pygame.Rect(0, 0,self.game_objects_group.play_area[2],
                                     self.game_objects_group.play_area[1]),
                         2)
        # display  border
        pygame.draw.rect(self.draw_surface, (0, 0, 0),
                         pygame.Rect(0, 0,
                                     self.draw_surface.get_width(), self.draw_surface.get_height()),
                         5)

        # hp points information
        self.draw_surface.blit(self.get_resource("ects_info"), (0, 0))
        hp_bar = self.get_resource("ects_bar_full")
        gap = hp_bar.get_width() + 1;#gap beetween bars
        bar_placement = self.get_resource("ects_info").get_width() + gap
        for hp_point in range(self.player.max_hp):
            if self.player.hp <= hp_point:
                hp_bar = self.get_resource("ects_bar_empty")
            self.draw_surface.blit(hp_bar, (bar_placement, 0))
            bar_placement += gap

        # Attack percentage information
        attack_pos_y = self.get_resource("ects_info").get_height() + 5
        self.draw_surface.blit(self.get_resource("attack_info"), (0, attack_pos_y))
        attack_bar = self.get_resource("ects_bar_full")
        bar_placement = self.get_resource("ects_info").get_width() + gap
        for attack_point in range(self.player.max_hp):
            if self.player.max_hp * self.player.attack_level / self.player.max_attack_level <= attack_point:
                attack_bar = self.get_resource("ects_bar_empty")
            self.draw_surface.blit(attack_bar, (bar_placement, attack_pos_y))
            bar_placement += gap

        # gold points information
        gold_pos_y = self.get_resource("attack_info").get_height() + attack_pos_y + 5
        self.draw_surface.blit(self.get_resource("gold_info"), (0, gold_pos_y))
        self.draw_surface.blit(self.get_resource("big_font").render(
            str(self.player.gold), True, (255, 255, 255)),
            (self.get_resource("gold_info").get_width() + 10, gold_pos_y - 6))

        #fps counter
        fps_counter = self.get_resource("small_font").render(
            "FPS:" + str(round(self.clock.get_fps(), 1)), True, (255, 255, 255))
        self.draw_surface.blit(fps_counter, (self.draw_surface.get_width() - fps_counter.get_width() - 5, 0))

        # draw every GameObjects
        self.game_objects_group.draw(self.draw_surface)

        if self.game_mode == App.GameMode.GAME_BEGIN:#for GAME_BEGIN information
            self.draw_surface.blit(self.black_filter, (0, 0))#black filter
            info_width = self.draw_surface.get_width() * 0.55#calculatin information window size
            info_height = self.draw_surface.get_height() * 0.95
            info_rect = pygame.Rect((self.draw_surface.get_width() - info_width) / 2,
                                    (self.draw_surface.get_height() - info_height) / 2,
                                    info_width,
                                    info_height)
            self.draw_surface.fill((44, 22, 4), info_rect)#draw information window
            pos = [info_rect[0], info_rect[1]]
            pos[1] += 3
            #description label
            description = self.get_resource("big_font").render(
                "Collect enough gold to buy \"warunek\".", True, (255, 255, 255))
            self.draw_surface.blit(description, ((self.draw_surface.get_width() - description.get_width()) / 2,
                                                 pos[1]))

            pos[1] += description.get_height() + 10
            #goal label
            goal = self.get_resource("medium_font").render("Goal: " + str(self.gold_goal), True, (255, 255, 0))
            self.draw_surface.blit(goal, ((self.draw_surface.get_width() - goal.get_width()) / 2,
                                          pos[1]))
            self.draw_surface.blit(self.get_resource("gold"), (
                (self.draw_surface.get_width()-goal.get_width()) / 2 + goal.get_width() + 3,
                pos[1]))
            pos[1] += goal.get_height() + 5
            segment_size = [info_rect[2] / 2, 70]
            #information about game content
            self.draw_game_object_information(self.get_resource("gold_info"), "your gold", pos,
                                              segment_size, (0, 0))
            self.draw_game_object_information(self.get_resource("ects_info"), "your hp", pos, segment_size,
                                              (1, 0))
            self.draw_game_object_information(self.get_resource("attack_info"), "your attack power",
                                              pos, segment_size, (0, 1))
            self.draw_game_object_information(self.get_resource("player"), "you", pos, segment_size, (0, 2))
            self.draw_game_object_information(self.get_resource("attack"), "attack restore", pos,
                                              segment_size, (1, 2))
            self.draw_game_object_information(self.get_resource("gold"), "gold", pos, segment_size, (0, 3))
            self.draw_game_object_information(self.get_resource("hp"), "hp", pos, segment_size, (1, 3))
            self.draw_game_object_information(self.get_resource("enemy1"), "MA ghost", pos,
                                              segment_size, (0, 4))
            self.draw_game_object_information(self.get_resource("enemy2"), "professor ghost",
                                              pos, segment_size, (1, 4))
            self.draw_game_object_information(self.get_resource("enemy3"), "PhD ghost", pos,
                                              segment_size,(0, 5))
            #line beetween game content and information about control
            pygame.draw.line(self.draw_surface, (34, 12, 0),
                             (pos[0]+10,pos[1]+segment_size[1]*6),
                             (pos[0]-10+info_rect[2],pos[1]+segment_size[1]*6),
                             5)
            self.draw_game_object_information(self.get_resource("wasd"), "to move", pos, segment_size, (0, 6))
            self.draw_game_object_information(self.get_resource("space"), "to attack", pos, segment_size,
                                              (1, 6))
            #press space to continue
            press_space_to_continue = self.get_resource("medium_font").render("Press [SPACE] to continue.",
                                                                              True, (255, 255, 255))
            self.draw_surface.blit(press_space_to_continue,
                                   ((self.draw_surface.get_width() - press_space_to_continue.get_width()) / 2,
                                    info_rect[1] + info_rect[3] - press_space_to_continue.get_height() * 1.5))
            #info window border
            pygame.draw.rect(self.draw_surface, (0, 0, 0), info_rect, 4)

        if self.game_mode == App.GameMode.GAME_END:#information window for GAME_END
            self.draw_surface.blit(self.black_filter, (0, 0))
            info_width = self.draw_surface.get_width() * 0.60#calculatin info window size
            info_height = self.draw_surface.get_height() * 0.25
            info_rect = pygame.Rect((self.draw_surface.get_width() - info_width) / 2,
                                    (self.draw_surface.get_height() - info_height) / 2,
                                    info_width,
                                    info_height)
            self.draw_surface.fill((44, 22, 4), info_rect)
            pos = [x for x in info_rect]
            pos[1] += 2.0
            #game over
            game_over = self.get_resource("huge_font").render("Game Over", True, (255, 255, 255))
            self.draw_surface.blit(game_over, ((self.draw_surface.get_width() - game_over.get_width()) / 2,
                                               pos[1]))
            percentage_score = (100 * self.player.gold / self.gold_goal)
            pos[1] += game_over.get_height()
            #calculating approximate length of "You Score:..." line
            approximate_line_length_string = "Your    score:K/K=   %"+str(self.player.gold)+\
            str(self.gold_goal)+str(int(percentage_score))
            pos[0] += (info_width -
                       self.get_resource("big_font").render(approximate_line_length_string
                                                            , False, (255, 255, 255)).get_width())/2
            big_font = self.get_resource("big_font")
            #Your Score:
            your_score = big_font.render("Your score:", True, (255, 255, 255))
            self.draw_surface.blit(your_score, (pos[0] + 5, pos[1]))
            pos[0] += your_score.get_width() + 10;
            pos[1] += 2
            #player gold
            score = big_font.render(str(self.player.gold), True, (255, 255, 0))
            self.draw_surface.blit(score, (pos[0], pos[1]))
            pos[0] += score.get_width() + 3
            #gold icon
            gold = self.get_resource("gold")
            self.draw_surface.blit(gold, (pos[0], pos[1] + abs(gold.get_height() - score.get_height()) / 2))
            pos[0] += gold.get_width() + 3
            #/
            divided = big_font.render("/", True, (255, 255, 255))
            self.draw_surface.blit(divided, (pos[0], pos[1]))
            pos[0] += divided.get_width() + 3
            goal = big_font.render(str(self.gold_goal), True, (255, 255, 0))
            self.draw_surface.blit(goal, (pos[0], pos[1]))
            pos[0] += goal.get_width() + 3
            #gold icon
            self.draw_surface.blit(gold, (pos[0], pos[1] + abs(gold.get_height() - goal.get_height()) / 2))
            pos[0] += gold.get_width() + 3
            #=
            equal = big_font.render("= ", True, (255, 255, 255))
            self.draw_surface.blit(equal, (pos[0], pos[1]))
            pos[0] += equal.get_width() + 3
            #red collor for % < 100, green for >= 100
            percentage_score_color = (205, 238, 106) if (percentage_score >= 100.0) else (249, 85, 85)
            #SCORE%
            percentage_score_label = big_font.render(str(int(percentage_score)) + "%", True,
                                                     percentage_score_color)
            self.draw_surface.blit(percentage_score_label, (pos[0], pos[1]))
            #press space to continue
            press_space_to_continue = self.get_resource("medium_font").render("Press [SPACE] to continue.",
                                                                              True, (255, 255, 255))
            self.draw_surface.blit(press_space_to_continue,
                                   ((self.draw_surface.get_width() - press_space_to_continue.get_width()) / 2,
                                    info_rect[1] + info_rect[3] - press_space_to_continue.get_height() * 2.5))
            #press esc to continue
            press_esc_to_quit = self.get_resource("medium_font").render("Press [ESC] to quit.",
                                                                        True, (255, 255, 255))
            self.draw_surface.blit(press_esc_to_quit,
                                   ((self.draw_surface.get_width() - press_esc_to_quit.get_width()) / 2,
                                    info_rect[1] + info_rect[3] - press_esc_to_quit.get_height() * 1.5))

            pygame.draw.rect(self.draw_surface, (0, 0, 0), info_rect, 4)#border
        pygame.display.flip()  # update display

    def draw_game_object_information(self, image, description, pos, segment_size, segment):
        """
            Draw infomation about game in a segment
        :param image:
        :param description:
        :param pos:
        :param segment_size:
        :param segment:
        :return:
        """
        label = self.get_resource("medium_font").render(" -> " + description, True, (255, 255, 255))
        size = [image.get_width() + label.get_width(), image.get_height() + label.get_height()]
        image_pos = [pos[i] + segment[i] * segment_size[i] + (segment_size[i] - size[i]) / 2
                     for i in range(len(pos))]
        image_pos[0] = pos[0] + segment[0] * segment_size[0] + 20
        self.draw_surface.blit(image, image_pos)
        self.draw_surface.blit(label, [image_pos[0] + image.get_width(),
                                       image_pos[1] + (image.get_height() - label.get_height()) / 2])

    def update(self, dt):
        """
            Handle keyboard events and use update(dt) on GameObjectsGroup object.
        :param dt: float
        :return:None
        """
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pygame.event.post(pygame.event.Event(QUIT))

        if self.game_mode == App.GameMode.GAME_BEGIN:
            if keys[pygame.K_SPACE]:
                self.game_mode = App.GameMode.GAME_MAIN

        elif self.game_mode == App.GameMode.GAME_MAIN:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.player.go_left(dt)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.player.go_right(dt)
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.player.go_up(dt)
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.player.go_down(dt)
            if keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]:
                self.player.attack()
            self.game_objects_group.update(dt)
        elif self.game_mode == App.GameMode.GAME_END:
            if keys[pygame.K_SPACE]:
                self.init_game()
                self.game_mode = App.GameMode.GAME_MAIN

    def run(self):
        """
        Main application procedure
        :return: None
        """
        while not self.done:  # main loop
            self.clock.tick(70)  # time system update
            self.events_loop(pygame.event.get())  # event handling
            self.update(self.clock.get_time() / 1000.0)  #
            self.draw()


if __name__ == "__main__":
    app = App((800, 600))
    app.run()
    sys.exit(0)
