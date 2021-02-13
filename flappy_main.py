import pygame
import sys
import random
import socket               # 导入 socket 模块
import client
import threading
import time
from text import TextBox

game_active = 4
result = ""


def draw_floor():
    screen.blit(floor_surface, (floor_x_pos, 750))
    screen.blit(floor_surface, (floor_x_pos + 576, 750))


def create_pipe():
    random_pipe_pos = random.choice(pipe_height)
    bottom_pipe = pipe_surface.get_rect(midtop=(700, random_pipe_pos))
    top_pipe = pipe_surface.get_rect(midbottom=(700, random_pipe_pos - 300))
    return bottom_pipe, top_pipe


def move_pipes(pipes):
    for pipe in pipes:
        pipe.centerx -= 5
    visible_pipes = [pipe for pipe in pipes if pipe.right > -50]
    return visible_pipes


def draw_pipes(pipes):
    for pipe in pipes:
        if pipe.bottom >= 1024:
            screen.blit(pipe_surface, pipe)
        else:
            flip_pipe = pygame.transform.flip(pipe_surface, False, True)
            screen.blit(flip_pipe, pipe)


def check_collision(pipes):
    global can_score
    for pipe in pipes:
        if Mybird.bird_rect.colliderect(pipe):
            death_sound.play()
            can_score = True
            myclient.send_die()
            return 2

    if Mybird.bird_rect.top <= -100 or Mybird.bird_rect.bottom >= 900:
        can_score = True
        myclient.send_die()
        return 2

    return 1


def score_display(game_state):
    if game_state == 'main_game':
        i = 0
        for bird in bird_list:
            id_surface = game_font.render(
                str(int(bird.bird_id)), True, (255, 255, 255))
            score_surface = game_font.render(
                str(int(bird.score)), True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(288, 100+i*50))
            id_rect = score_surface.get_rect(center=(200, 100+i*50))
            screen.blit(id_surface, id_rect)
            screen.blit(score_surface, score_rect)
            i += 1
    if game_state == 'game_over':

        high_score_surface = game_font.render(
            f'High score: {int(high_score)}', True, (255, 255, 255))
        high_score_rect = high_score_surface.get_rect(center=(288, 850))
        screen.blit(high_score_surface, high_score_rect)


def update_score(score, high_score):
    if score > high_score:
        high_score = score
    return high_score


def pipe_score_check():
    global score, can_score

    if pipe_list:
        for pipe in pipe_list:
            if 95 < pipe.centerx < 105 and can_score:
                Mybird.score += 1
                score_sound.play()
                can_score = False
                myclient.send_score(Mybird.score)
            if pipe.centerx < 0:
                can_score = True


def reciever(socket):
    while(FLAG):
        data = socket.recv(1024).decode("utf-8").split("|#|")
        print("Get something: %s", data)
        for res in data:
            if len(res) == 0:
                continue
            if(res[0] == "0"):
                myclient.id = res[2:]  # 0 userid
                print("reciver:getID: ", myclient.id)
            elif(res[0] == "1"):
                print(res)
                myclient.room_id = res[2:6]
                print("reciever:get room:", myclient.room_id)
            elif(res[0] == "2"):  # join_room
                print("reciver:join room:"+res)
                myclient.room_id = res[2:]
            elif(res[0] == "3"):  # update score
                update_bird(res)
                print_team_score()
            elif(res[0] == "4"):  # update pos
                update_pos(res)
            elif(res[0] == "5"):  # other players join in
                add_player(res)
            elif(res[0] == "6"):  # get players list
                add_players(res)
                print_team_score()
            elif(res[0] == "7"):  # get win or lose
                show_res(res)
            elif(res[0] == "9"):  # get win or lose
                show_chat(res)
                # game_active=3

chat=[]

def show_chat(res):
    word=res[1].split(" ")
    chat.append(word)

def show_res(res):
    print("change 3")
    if(len(bird_list) > 1):
        if(Mybird.score > bird_list[1].score):
            Mybird.result = "Win"
        elif(Mybird.score < bird_list[1].score):
            Mybird.result = "Lose"
        else:
            Mybird.result = "Draw Game"
    else:
        Mybird.result = res[2:]  # 7 Win, Lose, Draw Game
    print(Mybird.result)


def add_players(res):
    list = res[2:].split(" ")
    for li in list:
        if int(li) == -1:
            continue
        if li not in bird_id_list:
            # print("player list:"+li)
            temp = Bird(bird_kind="redbird")
            temp.bird_id = li
            temp.my_bird = False
            bird_list.append(temp)
            bird_id_list.append(li)


def add_player(res):
    temp_bird = Bird(bird_kind="redbird")
    temp_bird.bird_id = res[2:]
    temp_bird.my_bird = False
    bird_id_list.append(temp_bird.bird_id)
    bird_list.append(temp_bird)


def print_team_score():
    for bird in bird_list:
        print("score list:"+str(bird.bird_id)+" "+str(bird.score))


def update_bird(res):
    print("reciver:update score: "+res)
    list = res.split(" ")
    for bird in bird_list:
        if(bird.bird_id == list[1]):
            if len(list) == 4:
                score = list[-1]
            # print(bird.score)
                bird.score = int(score[0])


def update_pos(res):
    # sprintf(res,"%d %d %d %d %d\n",cmd, playerid, roomid,x,y,action,move);
    print("receiver:update_pos:"+res)
    list = res.split(" ")
    if(len(list) < 5):
        return
    for bird in bird_list:
        if(bird.my_bird):
            continue
        if(bird.bird_id == list[1]):
            # print(bird.score)
            if(len(list[4]) > 0 and len(list[3]) > 0):
                bird.bird_rect.centerx = int(list[3])
                bird.bird_rect.centery = int(list[4])

            # bird.bird_movement=int(list[6])
        # print("score list:"+str(bird.bird_id)+" "+str(bird.score))
# Game Variables
gravity = 0.15


wait_result = 1  # 1 active #2 wait #3 result #4 menu

score = 0
high_score = 0
can_score = True

pygame.init()
screen = pygame.display.set_mode((576, 800))
clock = pygame.time.Clock()
game_font = pygame.font.Font('04B_19.ttf', 40)
info_font = pygame.font.Font('04B_19.ttf', 30)


class Bird():

    def __init__(self, bird_kind):
        self.bird_movement = 0
        self.my_bird = True
        self.bird_id = 0
        self.bird_index = 0
        self.score = 0
        self.heart = 3
        self.result = ""
        self.icon = pygame.image.load(
            'assets/'+bird_kind+'-midflap.png').convert_alpha()

        self.bird_downflap = pygame.transform.scale2x(pygame.image.load(
            'assets/'+bird_kind+'-downflap.png').convert_alpha())
        self.bird_midflap = pygame.transform.scale2x(pygame.image.load(
            'assets/'+bird_kind+'-midflap.png').convert_alpha())
        self.bird_upflap = pygame.transform.scale2x(pygame.image.load(
            'assets/'+bird_kind+'-upflap.png').convert_alpha())
        self.bird_frames = [self.bird_downflap,
                            self.bird_midflap, self.bird_upflap]
        self.bird_surface = self.bird_frames[self.bird_index]
        self.bird_rect = self.bird_surface.get_rect(center=(100, 400))

    def bird_animation(self):
        new_bird = self.bird_frames[self.bird_index]
        new_bird_rect = new_bird.get_rect(center=(100, self.bird_rect.centery))
        return new_bird, new_bird_rect

    def rotate_bird(self):
        new_bird = pygame.transform.rotozoom(
            self.bird_surface, -self.bird_movement * 3, 1)
        return new_bird

    def display(self):
        self.bird_movement += gravity
        rotated_bird = self.rotate_bird()
        self.bird_rect.centery += self.bird_movement
        # myclient.update_player(self.bird_rect.centerx,self.bird_rect.centery,2)
        screen.blit(rotated_bird, self.bird_rect)

    def show(self):
        rotated_bird = self.rotate_bird()
        screen.blit(rotated_bird, self.bird_rect)


def callback(text):
    myclient.send_mes(text)
    print("回车测试", text)

def display_chat():
    for line in chat:
        score_surface = info_font.render(
            f'Chat:{line[3]}', True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(50, 400))
        screen.blit(score_surface, score_rect)

# init local bird
bird_list = []
bird_id_list = []
Mybird = Bird('bluebird')
bird_list.append(Mybird)

# get online birds
# 39.106.82.211
# 192.168.235.132
myclient = client.Client("192.168.235.132", 8080)
Mybird.bird_id = myclient.id
bird_id_list.append(Mybird.bird_id)
random.seed(myclient.room_id)
# print("room: "+myclient.get_room())

FLAG = True
thread = None
try:
    thread = threading.Thread(target=reciever, args=([myclient.s]))
    thread.start()
except:
    print("Error: unable to start thread")


# myclient._room()

bg_surface = pygame.image.load('assets/background-day.png').convert()
bg_surface = pygame.transform.scale2x(bg_surface)

floor_surface = pygame.image.load('assets/base.png').convert()
floor_surface = pygame.transform.scale2x(floor_surface)
floor_x_pos = 0
text_surface=pygame.image.load('assets/base.png').convert()
text_rect = text_surface.get_rect(center=(288, 400))

BIRDFLAP = pygame.USEREVENT + 1
pygame.time.set_timer(BIRDFLAP, 200)

# bird_surface = pygame.image.load('assets/bluebird-midflap.png').convert_alpha()
# bird_surface = pygame.transform.scale2x(bird_surface)
# bird_rect = bird_surface.get_rect(center = (100,512))

over_surface = pygame.image.load('assets/gameover.png').convert_alpha()
over_surface = pygame.transform.scale2x(over_surface)
over_rect = over_surface.get_rect(center=(288, 400))
pipe_surface = pygame.image.load('assets/pipe-green.png')
pipe_surface = pygame.transform.scale2x(pipe_surface)
pipe_list = []
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 2000)
pipe_height = [500, 600, 700]

game_over_surface = pygame.transform.scale2x(
    pygame.image.load('assets/message.png').convert_alpha())
game_over_rect = game_over_surface.get_rect(center=(288, 400))

flap_sound = pygame.mixer.Sound('sound/sfx_wing.wav')
death_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
score_sound = pygame.mixer.Sound('sound/sfx_point.wav')
score_sound_countdown = 100
SCOREEVENT = pygame.USEREVENT + 2
pygame.time.set_timer(SCOREEVENT, 100)
TYPE = False


#ext_box = TextBox(200, 30, 20, 500, callback=callback)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            FLAG = False
            myclient.close_connect()

            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if TYPE:
                #text_box.safe_key_down(event)
                if event.key == pygame.K_ESCAPE:
                    TYPE = False
            else:
                if event.key == pygame.K_SPACE and game_active == 1:
                    # myclient.update_player(Mybird.bird_rect.centerx,Mybird.bird_rect.centery,1)
                    Mybird.bird_movement = 0
                    Mybird.bird_movement -= 8
                    flap_sound.play()
                if event.key == pygame.K_a and game_active == 4:
                    myclient.join_room('2000')
                if event.key == pygame.K_t and game_active == 4:
                    TYPE = True
                if event.key == pygame.K_s and game_active == 4:
                    myclient.get_room()
                if event.key == pygame.K_p and game_active == 4:
                    myclient.get_player_list(myclient.room_id)
                if event.key == pygame.K_ESCAPE:
                    FLAG = False
                    myclient.close_connect()
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE and game_active == 4:
                    myclient.send_ready()
                    myclient.send_score(0)
                    game_active = 1
                    # myclient.create_connect()
                    pipe_list.clear()
                    Mybird.bird_rect.center = (100, 400)
                    Mybird.bird_movement = 0
                    Mybird.score = 0
                if event.key == pygame.K_SPACE and game_active == 3:
                    game_active = 4
                if event.key == pygame.K_SPACE and game_active == 2 and myclient.room_id == -1:
                    game_active = 4
        if event.type == SPAWNPIPE:
            pipe_list.extend(create_pipe())

        if event.type == BIRDFLAP:
            for bird in bird_list:
                if bird.bird_index < 2:
                    bird.bird_index += 1
                else:
                    bird.bird_index = 0

                bird.bird_surface, bird.bird_rect = bird.bird_animation()
        if event.type == SCOREEVENT and game_active == 1:

            myclient.update_player(
                Mybird.bird_rect.centerx, Mybird.bird_rect.centery, 2)

    screen.blit(bg_surface, (0, 0))

    if game_active == 1:  # active
        # other birds
        for bird in bird_list:
            if(bird.my_bird):
                bird.display()
            else:
                bird.show()
        # Bird

        # bird_movement += gravity
        # rotated_bird = rotate_bird(bird_surface)
        # bird_rect.centery += bird_movement
        # screen.blit(rotated_bird,bird_rect)
        game_active = check_collision(pipe_list)

        # Pipes
        pipe_list = move_pipes(pipe_list)
        draw_pipes(pipe_list)

        # Score
        pipe_score_check()
        # score_display('main_game')
    elif game_active == 2:  # wait
        # myclient.close_connect()
        screen.blit(over_surface, over_rect)
        # print(Mybird.result)
        # myclient.send_die()
        if(Mybird.result != ""):
            game_active = 3
            continue

    elif game_active == 3:  # result
        # show win or lose

        screen.blit(bg_surface, (0, 0))
        score_surface = game_font.render(
            f'{Mybird.result}', True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(288, 400))
        screen.blit(score_surface, score_rect)

    else:  # menu	

        screen.blit(game_over_surface, game_over_rect)
        high_score = update_score(score, high_score)
        # score_display('game_over')
        if TYPE:
            pygame.time.delay(33)
            #screen.blit(text_surface, text_rect)
            #text_box.draw(screen)
        display_chat()


    if(myclient.room_id != -1):
        score_surface = info_font.render(
            f'room:{myclient.room_id}', True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(120, 50))
        screen.blit(score_surface, score_rect)
        i = 0
        for bird in bird_list:
            screen.blit(bird.icon, bird.icon.get_rect(center=(50, 100+i*50)))
            id_surface = info_font.render(
                f'score:{bird.score}', True, (255, 255, 255))
            id_rect = id_surface.get_rect(center=(130, 100+i*50))
            screen.blit(id_surface, id_rect)
            i += 1

    # Floor
    floor_x_pos -= 1
    draw_floor()
    if floor_x_pos <= -576:
        floor_x_pos = 0

    pygame.display.update()
    clock.tick(120)
