'''
import gamelib


# Our bot
class TutorialBot(gamelib.AlgoCore):

    # Called once - on game start, before first turn, init stage
    def on_game_start(self, config):
        self.config = config

    # Called every turn
    def on_turn(self, turn_state):
        pass

# Run  our bot
if __name__ == "__main__":
    algo = TutorialBot()
    algo.start()
First we have to have some knowledge of units we can use, let's get their objects from config.

        # Get unit types
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER = [config["unitInformation"][index]["shorthand"] for index in range(6)]
Next, fill on_turn() method with some code. We have to acquire game state for current turn first. GameState object expects two things from us - game config object and turn state (passed by game engine into on_turn() method). Returned game_state is our center of operations, because almost all of them are being done by invoking it's methods.

        # Acquire game state for current turn
        game_state = gamelib.GameState(self.config, turn_state)
Next we want to disable warnings. Warnings are going to be printed for example when we call a method that checks IF we can create some unit and we can't for any reason. I'm not sure why, and why not when we call a method THAT ACTUALLY CREATES unit. At the moment there's also a bug - it prints error even if unit can be successfuly created.

        # Warnings have a bug, always prints out "Could not spawn xx at location",
        # also always prinsts additional reason like "Not enough resources" when checkng if we can make an action
        # We don't want that
        # Has to be set every turn, as we have to create new object of GameState every turn
        game_state.enable_warnings = False
Next we are going to call two our two methods - one that builds defenses and the second one for attacks.

        # Build defenses and attack
        self.defense(game_state)
        self.attack(game_state)
And at the end submit turn.

        # Submit turn
        game_state.submit_turn()
Our new methods.

    # Builds defenses
    def defense(self, game_state):
        pass

    # Attacks opponent
    def attack(self, game_state):
        pass
Full code up to this point.

import gamelib


# Our bot
class TutorialBot(gamelib.AlgoCore):

    # Called once - on game start, before first turn, init stage
    def on_game_start(self, config):
        self.config = config

        # Get unit types
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, UNIT_TO_ID
        FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER = [config["unitInformation"][index]["shorthand"] for index in range(6)]

    # Called every turn
    def on_turn(self, turn_state):

        # Acquire game state for current turn
        game_state = gamelib.GameState(self.config, turn_state)

        # Warnings have a bug, always prints out "Could not spawn xx at location",
        # also always prinsts additional reason like "Not enough resources" when checkng if we can make an action
        # We don't want that
        # Has to be set every turn, as we have to create new object of GameState every turn
        game_state.enable_warnings = False

        # Build defenses and attack
        self.defense(game_state)
        self.attack(game_state)

        # Submit turn
        game_state.submit_turn()

    # Builds defenses
    def defense(self, game_state):
        pass

    # Attacks opponent
    def attack(self, game_state):
        pass

# Run  our bot
if __name__ == "__main__":
    algo = TutorialBot()
    algo.start()
You should be able to run that code now. Run below command in PowerShell (in context of our Starter Kit folder) and check. Remember that command, as you are going to be using it a lot.

python scripts/run_match.py tutorial-bot python-algo
Let's start adding some defenses. We are going to add Filters on both edges of playfield first, then some Destructors to help in early stages of the game, then fill gaps with more Filters leaving small openning in a middle (allowing our ofessive units to pass through). When fully built, it should look like this:

python tutorials
Small circle symbolizes Filter and double circle is a Destructor.

First we have to create a method that helps us create new defensive units. We want to be able to pass a list of locations and unit type to be created. Because a lot of units occupy the same row, let's also allow that list to be just a list of x coordinates accompanied by additonal parameter - row (y) number. We'll need game_state as well. Then our new method should create units for us.

    # Builds deffesive units on the playfield
    def build_defenses(self, location_list, firewall_unit, game_state, row=None):
Now we have to iterate over our list of locations.

        # Iterate list of locations and for every location...
        for location in location_list:
At that point, as described above, single location can be either a list like [2, 15] (which is ready to use coordinate) or just an int of x coordinate, but then additional parameter named row (y) has to be set as well. In second case lets combine x and row/y into coordinate.

            # ...check if it's a list [x, y], or a number x (in case of number rebuild coordinate using additional row argument)
            if not type(location) == list:
                location = [location, row]
Next we have to check if we can create unit at given location. To do that we can use can_spawn() method that does couple of checks for us, for example if we can afford unit, if location we want to create it on is not occupied, if position is in bounds of the game arena, etc.

            # can_spawn() checks if units are affordable, location is unoccupied, position is in bounds of play area, etc
            # If we can spawn unit on given location...
            if game_state.can_spawn(firewall_unit, location):
If unit can be created, let's create it and log that information. Game library doesn't handle updating available resources when we attempt to spawn a unit. We have to handle for that by ourselves. One method to do that is just by decrease available resource counter by amount we used to create unit. Of course during next round we're going to have updated amount of resources, it's just a case of current round. Why decreasing is important? It's important for can_spawn() which otherwise will always be returning that unit is affordable if we had enough resources at start of a turn. We could create many units and use up all resources, and method won't let us know about that, because it will see still same amount of resources.

                # ...spawn unit of given type at given location, and log action
                game_state.attempt_spawn(firewall_unit, location)
                gamelib.debug_write(f'Spawning {firewall_unit} at {location}')

                # Starter kit does not descrease amount of resource on unit spawn by unit cost of that resource
                # We have to update it manually, co can_spawn() method will check agains updated amount in next loop iteration
                # 0 - our index, we are always at index 0, opponent at index 1
                game_state._player_resources[0]['cores'] -= game_state.type_cost(firewall_unit)
If we can't create unit it might mean couple of things, for example we can't afford it. In case of that we want to return and do not try to spawn any new units during this turn (to avoid creating cheaper ones when more expensive are already not affordable, we want to create units in order). There's only one exception - we don't want to break our loop in case of location being occupied. That will allow us to execute the same code every turn and rebuild our defenses. If location is occupied - ignore that and continue.

            # can_spawn() is going to return false if location is occupied as well
            # We want to break a loop if we can't spawn unit, but only for other reasons that occupied location
            # That way we can invoke the same action every turn and easly rebuild missing units
            elif not game_state.contains_stationary_unit(location):
                return False
Last thing we need here is to return True if we didn't encounter any problems, like used up all resources. Full code of the method:

    # Builds defesive units on the playfield
    def build_defenses(self, location_list, firewall_unit, game_state, row=None):

        # Iterate list of locations and for every location...
        for location in location_list:

            # ...check if it's a list [x, y], or a number x (in case of number rebuild coordinate using additional row argument)
            if not type(location) == list:
                location = [location, row]

            # can_spawn() checks if units are affordable, location is unoccupied, position is in bounds of play area, etc
            # If we can spawn unit on given location...
            if game_state.can_spawn(firewall_unit, location):

                # ...spawn unit of given type at given location, and log action
                game_state.attempt_spawn(firewall_unit, location)
                gamelib.debug_write(f'Spawning {firewall_unit} at {location}')

                # Starter kit does not descrease amount of resource on unit spawn by unit cost of that resource
                # We have to update it manually, co can_spawn() method will check agains updated amount in next loop iteration
                # 0 - our index, we are always at index 0, opponent at index 1
                game_state._player_resources[0]['cores'] -= game_state.type_cost(firewall_unit)

            # can_spawn() is going to return false if location is occupied as well
            # We want to break a loop if we can't spawn unit, but only for other reasons that occupied location
            # That way we can invoke the same action every turn and easly rebuild missing units
            elif not game_state.contains_stationary_unit(location):
                return False

        return True
Now, we can finally spawn some defenses. We're going to add code into defense() method. Let's add Filters on both sides (that's an example of situation when we are gloing to pass full coordinates to our newly created above method).

        # Side Filters
        filters = [[0, 13], [27, 13], [1, 12], [26, 12]]
        if not self.build_defenses(filters, FILTER, game_state):
            return
Then let's add some more expensive Destructors and fill gaps with more Filters.

        # Line of defense
        row = 11
        destructors = [2, 25, 6, 21, 11, 16]
        if not self.build_defenses(destructors, DESTRUCTOR, game_state, row=row):
            return
        filters = [3, 24, 4, 23, 5, 22, 7, 20, 8, 19, 9, 18, 10, 17, 12, 15]
        if not self.build_defenses(filters, FILTER, game_state, row=row):
            return
We used list of x coordinates here and passing additional row parameter to our method for greater visibility of our code.

Full code of the method:

    # Builds defenses
    def defense(self, game_state):

        # Side Filters
        filters = [[0, 13], [27, 13], [1, 12], [26, 12]]
        if not self.build_defenses(filters, FILTER, game_state):
            return

        # Line of defense
        row = 11
        destructors = [2, 25, 6, 21, 11, 16]
        if not self.build_defenses(destructors, DESTRUCTOR, game_state, row=row):
            return
        filters = [3, 24, 4, 23, 5, 22, 7, 20, 8, 19, 9, 18, 10, 17, 12, 15]
        if not self.build_defenses(filters, FILTER, game_state, row=row):
            return
What we are trying to achive here is to create units in that exact order, and we are trying to create as many of them as we can afford. That means that this code is going to be ran every turn, adding new units as long as there are still some to build. The other purpose is to rebuild units destroyed by opponent.

'''


import gamelib

class TutorialBot(gamelib.AlgoCore):
    def on_game_start(self, config):
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, UNIT_TO_ID
        FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER = [config['unitInformation'][idx]["shorthand"] for idx in range(6)]

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.enable_warnings = False

        self.defense(game_state)
        self.attack(game_state)

        game_state.submit_turn()

    def build_defenses(self, location_list, firewall_unit, game_state, row=None):
        for location in location_list:
            if not type(location) == list:
                location = [location, row]

            if game_state.can_spawn(firewall_unit, location):
                game_state.attempt_spawn(firewall_unit, location)
                gamelib.debug_write(f"{firewall_unit} deployed at {location}")
                game_state._player_resources[0]['cores'] -= game_state.type_cost(firewall_unit)

            elif not game_state.contains_stationary_unit(location):
                return False

        return True


    def defense(self, game_state):
        filters = [[0, 13], [27, 13], [1, 12], [26, 12]]
        if not self.build_defenses(filters, FILTER, game_state):
            return

        row = 11
        destructors = [2, 25, 6, 21, 11, 16]
        if not self.build_defenses(destructors, DESTRUCTOR, game_state, row=row):
            return

        filters = [3, 24, 4, 23, 5, 22, 7, 20, 8, 19, 9, 18, 10, 17, 12, 15]
        if not self.build_defenses(filters, FILTER, game_state, row=row):
            return


    def attack(self, game_state):
        pass


if __name__ == "__main__":
    algo = TutorialBot()
    algo.start()