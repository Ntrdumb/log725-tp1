import pgzero, pgzrun
import math, random
from enum import Enum


########## CONSTANTS
WIDTH = 800
HEIGHT = 480
TITLE = "Boing! TP1"

HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2

PLAYER_SPEED = 6
MAX_AI_SPEED = 6
################################ CONSTANTS END


########## UTILITY
def normalised(x, y):
    length = math.hypot(x, y)
    return (x / length, y / length) if length > 0 else (0, 0)
################################ UTILITY END


########## ENTITY
class Entity:
    def __init__(self):
        self.components = {}

    def add_component(self, component):
        self.components[type(component)] = component

    def get_component(self, component_type):
        return self.components.get(component_type)
################################ ENTITY END


########## COMPONENTS
class Component:
    pass

class Position(Component):
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Velocity(Component):
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

class Renderable(Component):
    def __init__(self, width, height):
        self.width = width
        self.height = height

class Paddle(Component):
    def __init__(self, player, ai=False):
        self.player = player
        self.ai = ai
        self.score = 0

class Ball(Component):
    def __init__(self, speed):
        self.speed = speed

class AI(Component):
    def __init__(self):
        self.offset = 0
        
################################ COMPONENTS END


########## SYSTEM
class System:
    def __init__(self, world):
        self.world = world

class MovementSystem(System):
    def update(self):
        for entity in self.world.entities:
            position = entity.get_component(Position)
            velocity = entity.get_component(Velocity)
            ball = entity.get_component(Ball)
            if position and velocity:
                if ball:
                    position.x += velocity.dx * ball.speed
                    position.y += velocity.dy * ball.speed
                else:
                    position.x += velocity.dx
                    position.y += velocity.dy

class BallSystem(System):
    def update(self):
        for entity in self.world.entities:
            ball = entity.get_component(Ball)
            if ball:
                position = entity.get_component(Position)
                velocity = entity.get_component(Velocity)
                
                if abs(position.y - HALF_HEIGHT) > 220:
                    velocity.dy = -velocity.dy
                    position.y += velocity.dy
                    ball.speed = min(ball.speed + 0.1, 15)  

                if position.x < 0 or position.x > WIDTH:
                    losing_player = 1 if position.x > WIDTH else 0
                    self.reset_ball(entity, losing_player)
                    self.update_score(losing_player)

    def reset_ball(self, ball_entity, losing_player):
        position = ball_entity.get_component(Position)
        velocity = ball_entity.get_component(Velocity)
        ball = ball_entity.get_component(Ball)

        #Reset ball position to center
        position.x, position.y = HALF_WIDTH, HALF_HEIGHT

        #Set initial direction towards the losing player
        direction = -1 if losing_player == 0 else 1
        velocity.dx = direction
        velocity.dy = random.uniform(-0.5, 0.5)

        velocity.dx, velocity.dy = normalised(velocity.dx, velocity.dy)

        ball.speed = 5

    def update_score(self, losing_player):
        winning_player = 1 - losing_player
        for entity in self.world.entities:
            paddle = entity.get_component(Paddle)
            if paddle and paddle.player == winning_player:
                paddle.score += 1
                break

class PaddleSystem(System):
    def update(self):
        ball_entity = next(e for e in self.world.entities if e.get_component(Ball))
        ball_pos = ball_entity.get_component(Position)
        
        for entity in self.world.entities:
            paddle = entity.get_component(Paddle)
            if paddle:
                position = entity.get_component(Position)
                if paddle.ai:
                    self.move_ai_paddle(entity, ball_pos)
                else:
                    self.move_player_paddle(entity)
                
                self.check_ball_collision(entity, ball_entity)

    def move_ai_paddle(self, paddle_entity, ball_pos):
        position = paddle_entity.get_component(Position)
        ai = paddle_entity.get_component(AI)
        
        target_y = HALF_HEIGHT if abs(ball_pos.x - position.x) > HALF_WIDTH else ball_pos.y + ai.offset
        position.y += min(MAX_AI_SPEED, max(-MAX_AI_SPEED, target_y - position.y))
        position.y = min(400, max(80, position.y))

    def move_player_paddle(self, paddle_entity):
        paddle = paddle_entity.get_component(Paddle)
        position = paddle_entity.get_component(Position)
        
        #Player 1 (Left) with WASD because its more logical this way
        if paddle.player == 0:
            if keyboard.s:
                position.y += PLAYER_SPEED
            elif keyboard.w:
                position.y -= PLAYER_SPEED
        else:
            if keyboard.z or keyboard.down:
                position.y += PLAYER_SPEED
            elif keyboard.a or keyboard.up:
                position.y -= PLAYER_SPEED
        
        position.y = min(400, max(80, position.y))

    def check_ball_collision(self, paddle_entity, ball_entity):
        paddle_pos = paddle_entity.get_component(Position)
        ball_pos = ball_entity.get_component(Position)
        ball_vel = ball_entity.get_component(Velocity)
        ball = ball_entity.get_component(Ball)
        
        if abs(ball_pos.x - paddle_pos.x) < 20 and abs(ball_pos.y - paddle_pos.y) < 60:
            ball_vel.dx = -ball_vel.dx
            ball_vel.dy += (ball_pos.y - paddle_pos.y) / 128
            ball_vel.dy = min(max(ball_vel.dy, -1), 1)
            ball_vel.dx, ball_vel.dy = normalised(ball_vel.dx, ball_vel.dy)
            
            ball.speed = min(ball.speed + 0.2, 15) #Vitesse max a 15
################################ SYSTEM END


# INITALISATION 
class World:
    def __init__(self):
        self.entities = []
        self.systems = []

    def create_entity(self):
        entity = Entity()
        self.entities.append(entity)
        return entity

    def add_system(self, system):
        self.systems.append(system)

    def update(self):
        for system in self.systems:
            system.update()

class Game:
    def __init__(self, num_players):
        self.world = World()
        self.setup_world(num_players)

    def setup_world(self, num_players):
        #Create paddles and the components for it
        for i in range(2):
            paddle = self.world.create_entity()
            paddle.add_component(Position(40 if i == 0 else 760, HALF_HEIGHT))
            paddle.add_component(Renderable(20, 100))
            paddle.add_component(Paddle(i, ai=(i == 1 and num_players == 1)))
            if i == 1 and num_players == 1:
                paddle.add_component(AI())

        #Create ball and it's components
        ball = self.world.create_entity()
        ball.add_component(Position(HALF_WIDTH, HALF_HEIGHT))
        ball.add_component(Velocity(-1, 0))
        ball.add_component(Renderable(14, 14))
        ball.add_component(Ball(5))

        #Add systems
        self.world.add_system(MovementSystem(self.world))
        self.world.add_system(BallSystem(self.world))
        self.world.add_system(PaddleSystem(self.world))

    def update(self):
        self.world.update()

    def draw(self):
        screen.clear()
        for entity in self.world.entities:
            position = entity.get_component(Position)
            renderable = entity.get_component(Renderable)
            if position and renderable:
                screen.draw.filled_rect(Rect((position.x - renderable.width // 2, position.y - renderable.height // 2), 
                                             (renderable.width, renderable.height)), 
                                        color="white")
        
        #Draw scores
        for entity in self.world.entities:
            paddle = entity.get_component(Paddle)
            if paddle:
                x = 200 if paddle.player == 0 else WIDTH - 200
                screen.draw.text(str(paddle.score), center=(x, 30), fontsize=60, color="white")


## SET
class State(Enum):
    MENU = 1
    PLAY = 2
    GAME_OVER = 3

state = State.MENU
game = None
num_players = 1


### UPDATE LOOP
def update():
    global state, game, num_players

    if state == State.MENU:
        if keyboard.space:
            state = State.PLAY
            game = Game(num_players)
        elif keyboard.w:
            num_players = 1
        elif keyboard.s:
            num_players = 2

    elif state == State.PLAY:
        game.update()
        #Check for game over condition
        for entity in game.world.entities:
            paddle = entity.get_component(Paddle)
            if paddle and paddle.score > 9:
                state = State.GAME_OVER

    elif state == State.GAME_OVER:
        if keyboard.space:
            state = State.MENU
            num_players = 1

def draw():
    screen.clear()
    if state == State.MENU:
        option1_marker = ">" if num_players == 1 else ""
        option2_marker = ">" if num_players == 2 else ""

        screen.draw.text(f"{option1_marker} Player 1", center=(HALF_WIDTH, HALF_HEIGHT - 20), fontsize=50, color="white")
        screen.draw.text(f"{option2_marker} Player 2", center=(HALF_WIDTH, HALF_HEIGHT + 20), fontsize=50, color="white")
    elif state == State.PLAY:
        game.draw()
    elif state == State.GAME_OVER:
        screen.draw.text("Game Over", center=(HALF_WIDTH, HALF_HEIGHT), fontsize=60, color="white")

pgzrun.go()