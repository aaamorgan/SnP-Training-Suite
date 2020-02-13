"""Snake, classic arcade game.
Excercises
1. How do you make the snake faster or slower?
2. How can you make the snake go around the edges?
3. How would you move the food?
4. Change the snake to respond to arrow keys.
"""

from turtle import *
from random import randrange
from freegames import square, vector
import threading
from serial import Serial
import time
from queue import Queue
from SnP_Emulator import SnPState


food = vector(0, 0)
snake = [vector(10, 0)]
aim = vector(0, -10)


def change(x, y):
    "Change snake direction."
    aim.x = x
    aim.y = y


def inside(head):
    "Return True if head inside boundaries."
    return -200 < head.x < 190 and -200 < head.y < 190


def move():
    "Move snake forward one segment."
    curr_state = snp_state.getState()
    if curr_state == 'hard_puff':
        # Up
        change(0, 10)
    elif curr_state == 'soft_puff':
        # Right
        change(10, 0)
    elif curr_state == 'soft_sip':
        # Left
        change(-10, 0)
    elif curr_state == 'hard_sip':
        # Down
        change(0, -10)
    else:
        change(0, 0)
        print('Invalid state')
    head = snake[-1].copy()
    head.move(aim)


    if not inside(head) or head in snake: #game over
        square(head.x, head.y, 9, 'red')
        change(0, -100)
        #head = snake[-1].copy()
        #head.move(aim)
        update()
        #wait a couple of seconds and then reset the snake to origianal position
        #print('game over')
        #time.sleep(2)
        return

    snake.append(head)

    if head == food:
        print('Snake:', len(snake))
        food.x = randrange(-15, 15) * 10
        food.y = randrange(-15, 15) * 10
    else:
        snake.pop(0)

    clear()

    for body in snake:
        square(body.x, body.y, 9, 'black')

    square(food.x, food.y, 9, 'green')
    update()
    ontimer(move, 250)


# snp_state = State(100, 120, 150, 200)
ser = Serial('/dev/ttyACM0',9600,timeout=None)
snp_state = SnPState(ser)
snp_state.start()
time.sleep(0.1)
snp_state.setup()

setup(420, 420, 370, 0)
hideturtle()
tracer(False)
listen()

# onkey(lambda: change(10, 0), 'Right')
# onkey(lambda: change(-10, 0), 'Left')
# onkey(lambda: change(0, 10), 'Up')
# onkey(lambda: change(0, -10), 'Down')
move()
#print('done')
#move()
done()
#time.sleep(2)

#############################################
#New code, trying to get the program to run again after game over
############################################
#food = vector(0, 0)
#snake = [vector(10,0)]
#aim = vector(0,-10)

#print('test')
#thread = threading.Thread(target=read_from_port, args=(serial_port,))
#thread.start()

#snp_state = State(100,120,150,200)

#setup(420, 420, 370, 0)
#hideturtle()
#tracer(False)
#listen()

#move()
#done()
