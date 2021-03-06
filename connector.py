import os, sys, subprocess
import random
import numpy as np
import threading

import signal
import time

import pickle

from cv2 import imshow, waitKey

max_turns = {32:400,40:425,48:450,56:475,64:500}

class player:
    def __init__(self,pipe_id,map_size,process):
        self.pipe_id = pipe_id
        self.max_turn = 500
        self.process = process
        self.map_size = map_size
        self.money = 5000
        self.money_delta = 0
        #print("launching")
        self.pipe_out = open("/tmp/halite_commands"+pipe_id, 'wb')
        self.pipe_in = open("/tmp/halite_data"+pipe_id, 'rb')
    
    def get_game_state(self):
        
        if not self.process.isAlive() or self.pipe_in.closed:
            self.clear()
            return None        
        
        #while True:
        #    print(self.pipe_in.read())
        try:
            status, ships, board = pickle.load(self.pipe_in)
        except EOFError:
            self.clear()
            return None
        self.money_delta = int(status[1]) - self.money
        self.money = int(status[1])
        
        game_progress = float(status[0])/max_turns[self.map_size]*100
        
        pad = np.zeros([self.map_size,self.map_size,1]) + game_progress
        board = np.concatenate([board,pad],2)
            
        return ships, board
    
    def get_hopeful_positions(self):
        
        if not self.process.isAlive() or self.pipe_in.closed:
            #self.clear()
            return None, -1
        
        try:
            ship_dropped,ships = pickle.load(self.pipe_in)
        except EOFError:
            return None, -1
        return ships, ship_dropped
        
        
    def send_orders(self, orders_list):
        #self.pipe_out.flush()
        
        pickle.dump(orders_list,self.pipe_out)
        
        self.pipe_out.flush()
        
    def clear(self):
        self.pipe_out.close()
        self.pipe_in.close()
        os.unlink("/tmp/halite_commands"+self.pipe_id)
        os.unlink("/tmp/halite_data"+self.pipe_id)

def launch(map_size, players_count, save_replay = False):
    
    pipe_ids = []
    
    for i in range(players_count):
        pipe_ids.append(str(random.randrange(0,2**31)))

    

    for pipe_id in pipe_ids:
        try:
            os.mkfifo("/tmp/halite_data"+pipe_id)
            os.mkfifo("/tmp/halite_commands"+pipe_id)
        except:
            pass
    
    command_str = "./halite --no-logs --no-timeout --width "+str(map_size)+" --height "+str(map_size)
    if save_replay:
        command_str += " --replay-directory ./run_replays"
    else:
        command_str += " --no-replay"
    for pipe_id in pipe_ids:
        command_str+= " 'python3 PipeBot.py {}'".format(pipe_id)
    
    process = lambda:os.system(command_str)
    
    t = threading.Thread(target = process)
    t.start()
    #process = subprocess.Popen(["./halite","--no-replay","--no-timeout","--width "+str(map_size),"--height "+str(map_size),'"python3 PipeBot.py {}"'.format(pipe_id1),'"python3 PipeBot.py {}"'.format(pipe_id2)])
    
    return [player(pipe_id,map_size,t) for pipe_id in pipe_ids], t

def main():
    while True:
        players, process = launch(64,4)
        
        states = []
        for player in players:
            states.append(player.get_game_state())

        while not states[0] == None:
            
            board = states[0][1]
            board = np.asarray(board)
            #print(np.sum(board[:,:,3]))
            board = board/np.max(board[:,:,3])
            imshow("xd",board[:,:,0:3])
            waitKey(1)
            
            #print(len(x[1]))
            
            for player, state in zip(players,states):
                orders = []
                for s in state[0]:
                    orders.append((s[0],[1,0,0,0,0,0]))
            
                player.send_orders(orders)
            
            states = []
            for player in players:
                states.append(player.get_game_state())

if __name__ == "__main__":
    main()
