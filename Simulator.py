import random
from Elevator import Elevator


class Person(object):
    def __init__(self, id, N, q, r):
        self.id = id        # id to avoid duplicates
        self.elev_num = -1

        if random.random() < q:
            self.start = 0  # storing first floor as 0 for convenience
        else:
            self.start = random.randint(1, N - 1)

        if self.start == 0:
            self.dest = random.randint(1, N - 1)
        else:
            if random.random() < r:
                self.dest = 0
            else:
                self.dest = random.choice(range(1, self.start) + range(self.start + 1, N))

        if self.start < self.dest:
            self.direction = 'U'
        else:
            self.direction = 'D'

class Simulator(object):
    """
    - carries out the simulation as specified in the problem statement
    - method to simulate an action on existing state
    - method to print current state (not equivalent to state representation of elevator in Elevator.py)
    """

    # CONSTANTS
    WAIT_TIME_COST_FACTOR = 2
    UP_DOWN_COST_FACTOR = 1

    def __init__(self, N, K, p, q, r, t_u):
        self.N = N              # number of floors
        self.K = K              # number of elevators
        self.p = p              # probability person arrives at a given time step
        self.q = q              # probability person arrives at first floor
        self.r = r              # probability person wants to get down at first floor
        self.t_u = t_u          # one time unit

        self.elev = Elevator(N, K)
        self.total_cost = 0
        self.total_people_served = 0
        self.people_in_sys = []

    def apply_action(self, action):
        """
        - action is a K length list with actions of the form 'AU', 'AD', 'AOU', 'AOD', 'AS' for each elevator
        - executes the action and simulates the next state
        - returns the new buttons pressed after simulation
        - updates the cost
        """

        # reset lights, will set depending on action
        self.elev.reset_lights()

        # update costs
        self.total_cost += Simulator.WAIT_TIME_COST_FACTOR * len(self.people_in_sys)        # cost for people carried over from last time step
        self.total_cost += Simulator.UP_DOWN_COST_FACTOR * len([x for x in action if x=='AU' or x=='AD'])   # cost for all lifts moved

        new_buttons_pressed = ''

        # move lifts
        for k in range(self.K):
            if action[k] == 'AU':
                self.elev.modify_pos(k, 1)
            if action[k] == 'AD':
                self.elev.modify_pos(k, -1)
            if not 0 <= self.elev.pos[k] < self.N:
                return 'INVALID ACTION'

        # embarkation, disembarkation
        for k in range(self.K):
            if action[k] == 'AOU' or action[k] == 'AOD':    # remove people with this dest, unpress button
                self.people_in_sys = [x for x in self.people_in_sys if x.elev_num == k and x.dest == self.elev.pos[k]]
                self.elev.modify_elevator_button(k, self.elev.pos[k], 0)

                # add people to the elevator who want to go in the direction of lift, press their buttons
                for i in range(self.people_in_sys):
                    if (self.people_in_sys[i].elev_id == -1 and self.people_in_sys[i].start == self.elev.pos[k] and
                            self.people_in_sys[i].direction == action[k][-1]):
                        self.people_in_sys[i].elev_id = k
                        unpressed = self.elev.modify_elevator_button(k, self.people_in_sys[i].dest, 1)

                        if unpressed:   # may have been pressed by someone already in list, or multiple times by people entering => add once
                            new_buttons_pressed += 'B' + str(self.people_in_sys[i].dest + 1) + str(k+1) + ' '

            # set lights
            if action[k] == 'AOU':
                self.elev.modify_lights(k, 'U', 1)
            if action[k] == 'AOD':
                self.elev.modify_lights(k, 'D', 1)

        # person arrival
        if random.random() < self.p:     # person arrives
            self.total_people_served += 1
            new_person = Person(self.total_people_served, self.N, self.q, self.r)
            unpressed = self.elev.modify_floor_button(new_person.start, new_person.direction, 1)
            if unpressed:
                new_buttons_pressed = 'B' + new_person.direction + str(new_person.start+1) + ' ' + new_buttons_pressed

            self.people.append(new_person)
        else:
            new_buttons_pressed = '0 ' + new_buttons_pressed

        return new_buttons_pressed

    def __str__(self):
        """
        - returns a (hopefully pretty) text based representation of the current state
        """

        left_margin = 25
        lift_width = 5

        state = ''
        state += '-'*(left_margin + (lift_width+1)*self.N + 24) + '\n'
        state += 'FLOOR' + ' '*(left_margin-5) + ' '*(lift_width/2 + 1)
        for i in range(self.N):
            state += str(i+1) + ' '*lift_width
        state += '\n'

        # people waiting
        waiting_up = [0]*self.N
        waiting_down = [0] * self.N
        for person in self.people_in_sys:
            if person.elev_num == -1:
                if person.direction == 'U':
                    waiting_up[person.start] += 1
                else:
                    waiting_down[person.start] += 1

        state += 'PEOPLE WAITING UP/DOWN' + ' '*(left_margin-22) + ' '*(lift_width/2)
        for u,d in zip(waiting_up,waiting_down):
            state += str(u) + '/' +str(d) + ' '*(lift_width-len(str(u)+str(d)))
        state += '\n'

        # up and down buttons
        state += 'FLOOR UP BUTTON' +' '*(left_margin + lift_width/2 - 15)
        for i in range(self.N):
            if self.elev.BU[i]:
                state += '-->'
            else:
                state += ' '*3
            state += ' '*(lift_width-2)
        state += '\n'

        state += 'FLOOR DOWN BUTTON' + ' ' * (left_margin + lift_width / 2 - 17)
        for i in range(self.N):
            if self.elev.BD[i]:
                state += '<--'
            else:
                state += ' ' * 3
            state += ' ' * (lift_width - 2)
        state += '\n'

        # lifts
        for i in range(self.K):
            state += '\n'
            state += ' '*left_margin + '-'*((lift_width+1)*self.N + 1) + '\n'
            state += 'LIFT ' + str(i+1) + ' '*(left_margin - 5 - len(str(i+1)))

            for j in range(self.N):
                if self.elev.pos[i] == j:
                    state += '|' + ' '*(lift_width/2) + '.' + ' '*(lift_width/2)
                else:
                    state += '|' + ' '*lift_width
            state += '|' + ' '*5 + 'PEOPLE IN LIFT : ' + str(len([x for x in self.people_in_sys if x.elev_num == i])) + '\n'

            state += ' ' * left_margin + '-' * ((lift_width + 1) * self.N + 1) + '\n'
            state += 'BUTTONS PRESSED' + ' '*(left_margin-15 + lift_width/2 + 1)
            for j in range(self.N):
                if self.elev.BF[i][j]:
                    state += 'o' + ' '*lift_width
                else:
                    state += ' '*(lift_width+1)
            state += '\n'

        return state