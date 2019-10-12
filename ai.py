from colorfight import Colorfight, Position
import time
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST



class Agent:
    def __init__(self):
        self.cdw = -1.0
        self.cgw = 1.0
        self.dpw = 1.0
        self.oew = 1.0
        self.ogw = 1.0
        self.g_threshold = 0
        self.e_threshold0 = 0
        self.e_threshold = 0

    def e_weight(self):
        return 400.0 - game.turn

    def g_weight(self):
        return game.turn


    def cell_danger(self, cell):
        # cell_danger = 0
        # for dx in range(-5, 5):
        #     for dy in range(-5, 5):
        #         cell_danger += 1.0 / (abs(dx) + abs(dy)) if cell.map[cell.position + Position(dx, dy)] else 0

        # return cell_danger
        return 0

    def home_dist(self, cell):
        return 0
        #for h in self.game.home



    def cell_gain(self, cell):
        return max(cell.gold * self.g_weight(), cell.energy * self.e_weight())

    def delta_perim(self, cell):
        rtn = 0
        for pos in cell.position.get_surrounding_cardinals():
            c = self.game.game_map[pos]
            if c.owner == game.uid:
                rtn += 1

        return rtn

    def opp_value(self, cell):
        if cell.owner != game.uid:
            if cell.building == BLD_GOLD_MINE:
                return self.ogw * cell.building.level
            if cell.building == BLD_ENERGY_WELL:
                return self.oew * cell.building.level

        return 0

    def build_weight(self, cell):
        return (cell.gold * self.g_weight(), cell.energy * self.e_weight())


    def cell_desire(self, cell):
      cell_danger = self.cdw * self.cell_danger(cell), 
      cell_gain = self.cgw * self.cell_gain(cell), 
      delta_perim = self.dpw * self.delta_perim(cell),
      opp_value = self.opp_value(cell), 

      #home_dist, hdw = self.home_dist(cell), 

      return (cell_danger, cell_gain, delta_perim, opp_value)

    def play_game(self, game, room='xD', username='SmallBrain', password='abcde'):

        self.game = game
        game.connect(room = room)
        if not game.register(username = username, \
                password = password):
            return
        while True:
            # The command list we will send to the server
            cmd_list = []
            # The list of cells that we want to attack
            attack_list = []
            build_list = []
            # update_turn() is required to get the latest information from the
            # server. This will halt the program until it receives the updated
            # information.
            # After update_turn(), game object will be updated.
            # update_turn() returns a Boolean value indicating if it's still
            # the same game. If it's not, break out
            if not self.game.update_turn():
                break

            # Check if you exist in the game. If not, wait for the next round.
            # You may not appear immediately after you join. But you should be
            # in the game after one round.
            if self.game.me == None:
                continue

            me = self.game.me

            # game.me.cells is a dict, where the keys are Position and the values
            # are MapCell. Get all my cells.
            for cell in game.me.cells.values():
                # Check the surrounding position

                for pos in cell.position.get_surrounding_cardinals():
                    # Get the MapCell object of that position
                    c = game.game_map[pos]
                    # Attack if the cost is less than what I have, and the owner
                    # is not mine, and I have not attacked it in this round already
                    # We also try to keep our cell number under 100 to avoid tax
                    if c.owner != game.uid:
                        attack_list.append( (self.cell_desire(cell), cell) )
                    



                # If we can upgrade the building, upgrade it.
                # Notice can_update only checks for upper bound. You need to check
                # tech_level by yourself.
                if cell.building.can_upgrade and \
                        (cell.building.is_home or cell.building.level < me.tech_level):
                    
                    weight = 0
                    if cell.building.name == BLD_ENERGY_WELL:
                        weight = self.g_weight() * cell.gold
                    elif cell.building.name == BLD_GOLD_MINE:
                        weight = self.e_weight() * cell.energy
                        
                    build_list.append((None, 1, weight, cell))

                if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]:

                    # Find the more preferable between gold mine and energy well
                    weights = self.build_weight(cell)
                    pref_building = BLD_ENERGY_WELL
                    pref_weight = weights[1]
                    if weights[0] > weights[1]:
                        pref_building = BLD_GOLD_MINE
                        pref_weight = weights[0]

                    build_list.append((pref_building, 0, pref_weight, cell))
                
            sortAttacks = lambda a: a[0]
            attack_list.sort(key=sortAttacks)

            for i in attack_list:
                temp_e = me.energy - i[1].attack_cost
                if temp_e < self.e_threshold0:
                    cmd_list.append(game.attack(pos, c.attack_cost))
                    me.energy = temp_e
                    print("We are attacking ({}, {}) with {} energy".format(
                        pos.x, pos.y, c.attack_cost))
                else:
                    break    
            sortBuildOps = lambda buildOp: buildOp[2]

            build_list.sort(key = sortBuildOps)
            for i in build_list:
                if me.gold < self.g_threshold or me.energy < self.e_threshold:
                    break

                if i[1]:
                    cmd_list.append(game.upgrade(i[3].position))

                    temp_g = me.gold - cell.building.upgrade_gold
                    temp_e = me.energy - cell.building.upgrade_energy
                    if temp_g >= self.g_threshold:
                        me.gold = temp_g
                    else:
                        break
                    if temp_e >= self.e_threshold:
                        me.energy = temp_e
                    else:
                        break

                    print("We upgraded ({}, {})".format(
                        cell.position.x, cell.position.y))
                else:
                    temp_g = me.gold - 100
                    if temp_g >= self.g_threshold:
                        me.gold = temp_g
                    cmd_list.append(game.build(i[3].position, i[0]))
                    me.gold -= 100
                    print("We build {} on ({}, {})".format(
                        i[0], cell.position.x, cell.position.y))

            # Send the command list to the server
            result = game.send_cmd(cmd_list)
            print(result)

if __name__ == '__main__':
    # Create a Colorfight Instance. This will be the object that you interact
    # with.
    game = Colorfight()

    # ================== Find a random non-full rank room ==================
    #room_list = game.get_gameroom_list()
    #rank_room = [room for room in room_list if room["rank"] and room["player_number"] < room["max_player"]]
    #room = random.choice(rank_room)["name"]
    # ======================================================================
    room = 'xD'  # Delete this line if you have a room from above

    # ==========================  Play game once ===========================
    a = Agent()
    a.play_game(
        game
    )
    # ======================================================================

    # ========================= Run my bot forever =========================
    # while True:
    #    try:
    #        play_game(
    #            game     = game, \
    #            room     = room, \
    #            username = 'ExampleAI' + str(random.randint(1, 100)), \
    #            password = str(int(time.time()))
    #        )
    #    except Exception as e:
    #        print(e)
    #        time.sleep(2)
