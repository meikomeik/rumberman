import gym
import random
import time

from src.bomberman.command.command import Command
from src.env.bomberman import Action

MAX_X = 9
MAX_Y = 9

def stupid_bot(obs, id):
    x = obs['players'][id]['x']
    y = obs['players'][id]['y']
    choices = []
    if x + 1 < MAX_X:
        if obs['field'][x+1][y] == 0:
            choices.append(Command.RIGHT)
    if y + 1 < MAX_Y:
        if obs['field'][x][y+1] == 0:
            choices.append(Command.DOWN)
    if x - 1 >= 0:
        if obs['field'][x-1][y] == 0:
            choices.append(Command.LEFT)
    if y - 1 >= 0:
        if obs['field'][x][y-1] == 0:
            choices.append(Command.UP)

    return random.choice(choices)

def get_neighbour(fields, x, y, seen):
    neighbours = []
    if x + 1 < MAX_X and (x+1, y) not in seen:
        if fields[x+1][y] == 0:
            neighbours.append((x+1, y, Command.RIGHT))
            #print('RIGHT')
    if y + 1 < MAX_Y and (x, y+1) not in seen:
        if fields[x][y+1] == 0:
            neighbours.append((x, y+1, Command.DOWN))
            #print('DOWN')
    if x - 1 >= 0 and (x-1, y) not in seen:
        if fields[x-1][y] == 0:
            neighbours.append((x-1, y, Command.LEFT))
            #print('LEFT')
    if y - 1 >= 0 and (x, y-1) not in seen:
        if fields[x][y-1] == 0:
            neighbours.append((x, y-1, Command.UP))
            #print('UP')
    return neighbours

def get_paths(
        fields, x, y, choices=[], seen=[], level=0, basepath=[], bombs={}):
    seen.append((x, y))
    neighbours = get_neighbour(fields, x, y, seen)
    new_choices = []
    for neighbour in neighbours:
        if 0 <= neighbour[0] <= MAX_X and 0 <= neighbour[1] <= MAX_Y:
            found_bomb = False
            for id, bomb in bombs:
                if bomb['x'] == neighbour[0] and bomb['y'] == neighbour[1]:
                    found_bomb = True
            if fields[neighbour[0]][neighbour[1]] == 0 and not found_bomb:
                if not (neighbour[0], neighbour[1]) in seen:
                    new_choice = basepath + [
                        [neighbour[2], [neighbour[0], neighbour[1]]]]
                    new_choices.append(new_choice)
                    more_choices, seen = get_paths(
                        fields, neighbour[0], neighbour[1], choices, seen,
                        basepath=new_choice, bombs=bombs)
                    new_choices += more_choices

    return choices + new_choices, seen

def get_fires(bombs, fires, field):

    matrix = [[[
        '-' for x in range(MAX_X)] for y in range(MAX_Y)] for z in range(5)]
    for life in range(5):
        if life == 0:
            for id, fire in fires.items():
                matrix[life][fire['x']][fire['y']] = 'X'
        else:
            for id, bomb in bombs.items():
                if bomb['life'] != life:
                    continue
                x = bomb['x']
                y = bomb['y']
                minx = True
                miny = True
                maxx = True
                maxy = True
                for i in range(bomb['blast_strength']):
                    if 0 <= x + i < MAX_X and maxx:
                        if field[x + i][y] in [1, 2]:
                            maxx = False
                        if field[x + i][y] in [0, 2]:
                            matrix[life][x + i][y] = 'X'
                    if 0 <= x - i < MAX_X and minx:
                        if field[x - i][y] in [1, 2]:
                            minx = False
                        if field[x - i][y] in [0, 2]:
                            matrix[life][x - i][y] = 'X'
                    if 0 <= y + i < MAX_Y and maxy:
                        if field[x][y + i] in [1, 2]:
                            maxy = False
                        if field[x][y + i] in [0, 2]:
                            matrix[life][x][y + i] = 'X'
                    if 0 <= y - i < MAX_Y and miny:
                        if field[x][y - i] in [1, 2]:
                            miny = False
                        if field[x][y - i] in [0, 2]:
                            matrix[life][x][y - i] = 'X'
    return matrix

def get_best_spot(field, power_ups, seen, blast_strength):
    best = {}
    for xy in seen:
        x = xy[0]
        y = xy[1]
        for id, power in power_ups.items():
            if power['x'] == x and power['y'] == y:
                best[xy] = 40

        # print(xy)
        f = get_fires({0: {
                'x': xy[0],
                'y': xy[1],
                'blast_strength': blast_strength,
                'life': 1}
            }, {}, field)

        loot = 0
        for _y in range(MAX_Y):
            row = ''
            for _x in range(MAX_X):
                row += ' ' + str(f[1][_x][_y])
                if f[1][_x][_y] == 'X':
                    # print('!!!!!! ', field[_x][_y] == 2, _x, _y)
                    if field[_x][_y] == 2:
                        loot += 10
                        # print('YES')


            #print(row)
        if xy in best:
            best[xy] += loot
        else:
            best[xy] = loot

    return best

def rumberman_bot(obs, id, tasks):
    x = obs['players'][id]['x']
    y = obs['players'][id]['y']

    fires = get_fires(obs['bombs'], obs['fires'], obs['field'])

    print(obs)
    print(obs['field'])
    print('players: ', obs['players'])
    print('bombs: ', obs['bombs'])
    print('fires: ', obs['fires'])
    print('power: ', obs['power_ups'])

    current_ammo = obs['players'][id]['current_ammo']

    bombs = {}
    for _i in obs['bombs'].values():
        bombs[(_i['x'], _i['y'])] = 1

    standing_on_bomb = len([_x for _x in obs['bombs'].values() if
                            _x['x'] == x and _x['y'] == y]) > 0

    for _y in range(MAX_Y):
        row = ''
        for _x in range(MAX_X):
            if _y == y and _x == x:
                row += ' @'
            else:
                row += ' ' + str(obs['field'][_x][_y])
        for life in range(5):
            row += " "
            for _x in range(MAX_X):
                row += ' ' + str(fires[life][_x][_y])
        print(row)

    if len(tasks) == 0 or True:
        choices, seen = get_paths(obs['field'], x, y, [], [], obs['bombs'])
        if not standing_on_bomb and current_ammo > 0:
            choices.append([[Command.BOMB, [x, y]]])
        best_spots = get_best_spot(obs['field'], obs['power_ups'], seen, obs['players'][id]['blast_strength'])
        print('best: ', best_spots)
        max_points = -1
        min_length = 99
        for choice in choices:
            if len(choice) > 5:
                continue
            print('Choice(n): ', choice)
            steps_success = True
            sum_points = 0
            for o, step in enumerate(choice):
                _x = step[1][0]
                _y = step[1][1]
                #if (_x, _y) in best_spots and best_spots[(_x, _y)] >= max_points:
                if (_x, _y) in best_spots:
                    # and best_spots[(_x, _y)] >= max_points:
                    # for i, c in enumerate(choice):
                    # for o in range(len(fires)):
                    sum_points += best_spots[(_x, _y)]
                else:
                    steps_success = False
                    print('LOL DOES THIS HAPPEN?')

                if (_x, _y) in bombs:
                    print('PATH LEADS TO BOMB')
                    steps_success = False

                for _o in range(len(fires)):
                    if _o in fires and fires[o][_x][_y] == 'X':
                        print('BOOM ')
                        steps_success = False
                if steps_success and False:
                    print('{} => {} :: {} => {}'.format(
                        max_points, best_spots[(_x, _y)], len(choice),
                        min_length))

            if steps_success and max_points > sum_points:
                # min_length = len(choice)

                tasks = choice
                # max_points = best_spots[choice[-1][1][0], choice[-1][1][1]] - len(choice)
                max_points = sum_points
                print('CHOOSE: ', max_points, min_length, tasks)
                if max_points < 40:
                    tasks.append([
                        Command.BOMB, [_x, _y]])
                print('YEAHHHH')
        #time.sleep(2)

    if len(tasks) == 0 or False:
        max_len = -1
        for choice in choices:
            # print(x, y, choice, len(choice))
            if len(choice) > max_len:
                reject = False
                for i, c in enumerate(choice):
                    if i+1 >= len(fires):
                        continue
                    if fires[i+1][c[1][0]][c[1][1]] == 'X':
                        print('BOOM')
                        reject = True
                if reject:
                    continue

                tasks = choice
                max_len = len(choice)
                tasks.append([Command.BOMB, [tasks[-1][1][0], tasks[-1][1][1]]])

    if len(tasks) == 0:
        print('NOOP')
        return Command.NOOP, tasks

    task = tasks[0]
    # print(task)
    if fires[0][task[1][0]][task[1][1]] == 'X':
        print('BOOOOOOOOM ->> NOOP')
        return Command.NOOP, tasks
    tasks.pop(0)

    return task[0], tasks


env = gym.make('BombermanRender-v0')
obs = env.reset()

stats = [0, 0]
for rounds in range(1):
    replay1 = []

    env = gym.make('BombermanRender-v0')
    obs = env.reset()
    for y in range(MAX_Y):
        row = ""
        for x in range(MAX_X):
            row += ' ' + str(obs['field'][x][y])
        print(row)

    tasks = []
    done = False
    _done = False
    while not done:
        cmd1, tasks = rumberman_bot2(obs, 0, tasks)
        print('===== {} ====='.format(cmd1.name))
        replay1.append(cmd1)
        # cmd1 = stupid_bot(obs, 1)
        cmd2 = stupid_bot(obs, 1)
        # cmd1 = Command.RIGHT
        # cmd2 = Command.NOOP

        if _done:
            done = True
        act = Action(cmd1, cmd2)

        obs, reward, done, info = env.step(act)

        #print(obs)
        #print(reward, done, info)

        # input('PRESS ENTER')
        time.sleep(0.15)

    print(reward)
    if reward[0] > 0:
        print('WE WON')
        stats[0] += 1
    elif reward[1] > 0:
        print('IDIOT WON')
        stats[1] += 1
    else:
        print('= D R A W =')

    print(stats)
print('FIN')
print(replay1)

