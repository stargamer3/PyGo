import numpy as np
from copy import deepcopy
class Board():
    def __init__(self, shape):
        self.shape = shape
        self.state = [[0]*shape[1] for i in range(shape[0])]
        self.previous_states = []
    def play(self, player, move, superko):
        assert self.state[move[0]][move[1]]==0
        self.state[move[0]][move[1]] = player.color
        black_captured, white_captured = self.capture(player)
        rule_broken = False
        if(self.state[move[0]][move[1]]==0):
            rule_broken = True
            self.state = deepcopy(self.previous_states[-1])
            black_captured = 0
            white_captured = 0
        elif(self.state in self.previous_states):
            rule_broken = True
            self.state = deepcopy(self.previous_states[-1])
            black_captured = 0
            white_captured = 0
        else:
            self.previous_states.append(deepcopy(self.state))
            if(not superko):
                self.previous_states = self.previous_states[-2:]
        return black_captured, white_captured, rule_broken
    def fix(self, coord, axis):
        if(coord<0):
            return 0
        if(coord>=self.shape[axis]):
            return self.shape[axis]-1
        return coord
    def capture(self, lastplayer):
        remove_color = -1*lastplayer.color
        for _ in range(2):
            chains = []
            num = 0
            for i in range(len(self.state)):
                for j in range(len(self.state[i])):
                    if(self.state[i][j]==remove_color):
                        in_existing_chain = False
                        for ind, k in enumerate(chains):
                            if((i-1, j) in k or (i, j-1) in k or (i+1, j) in k or (i, j+1) in k):
                                chains[ind].append((i, j))
                                in_existing_chain = True
                        if(not in_existing_chain):
                            chains.append([(i, j)])
            for i in chains:
                captured = True
                for j in i:
                    if(0 in [self.state[self.fix(j[0]-1, 0)][self.fix(j[1], 1)], self.state[self.fix(j[0]+1, 0)][self.fix(j[1], 1)], self.state[self.fix(j[0], 0)][self.fix(j[1]-1, 1)], self.state[self.fix(j[0], 0)][self.fix(j[1]+1, 1)]]):
                        captured = False
                if(captured):
                    num+=len(i)
                    for j in i:
                        self.state[j[0]][j[1]] = 0
            if(remove_color==-1):
                black_captured = num
            else:
                white_captured = num
            remove_color*=-1
        return black_captured, white_captured
    def count(self):
        black_pieces = 0
        white_pieces = 0
        for i in self.state:
            black_pieces+=i.count(1)
            white_pieces+=i.count(-1)
        return black_pieces, white_pieces
class Player():
    def __init__(self, color):
        self.color = color
class Go():
    def __init__(self, shape=(19, 19), komi=7.5, scoring="TERRITORY", superko=True, forced_connections=False, seki_territory=True):
        self.board = Board(shape)
        self.black = Player(1)
        self.white = Player(-1)
        self.players = (self.black, self.white)
        self.turn = 0
        self.prisoners = [0, 0]
        self.finished = False
        self.winner = 0
        self.names = (None, "BLACK", "WHITE")
        self.passed_previous_move = False
        self.komi = komi
        self.scoring = scoring
        self.superko = superko
    def dilate(self, board):
        dboard = deepcopy(board)
        for i in range(len(board)):
            for j in range(len(board[i])):
                if(board[i][j]>=0 and board[self.board.fix(i-1, 0)][self.board.fix(j, 1)]>=0 and board[self.board.fix(i+1, 0)][self.board.fix(j, 1)]>=0 and board[self.board.fix(i, 0)][self.board.fix(j-1, 1)]>=0 and board[self.board.fix(i, 0)][self.board.fix(j+1, 1)]>=0):
                    for k in range(-1, 2):
                        for l in range(-1, 2):
                            if((self.board.fix(i+k, 0), self.board.fix(j+l, 1))!=(i, j) and (k==0 or l==0) and board[self.board.fix(i+k, 0)][self.board.fix(j+l, 1)]>0):
                                dboard[i][j]+=1
                elif(board[i][j]<=0 and board[self.board.fix(i-1, 0)][self.board.fix(j, 1)]<=0 and board[self.board.fix(i+1, 0)][self.board.fix(j, 1)]<=0 and board[self.board.fix(i, 0)][self.board.fix(j-1, 1)]<=0 and board[self.board.fix(i, 0)][self.board.fix(j+1, 1)]<=0):
                    for k in range(-1, 2):
                        for l in range(-1, 2):
                            if((self.board.fix(i+k, 0), self.board.fix(j+l, 1))!=(i, j) and (k==0 or l==0) and board[self.board.fix(i+k, 0)][self.board.fix(j+l, 1)]<0):
                                dboard[i][j]-=1
        return dboard
    def erode(self, board):
        dboard = deepcopy(board)
        for i in range(len(board)):
            for j in range(len(board[i])):
                if(board[i][j]>0):
                    for k in range(-1, 2):
                        for l in range(-1, 2):
                            if((self.board.fix(i+k, 0), self.board.fix(j+l, 1))!=(i, j) and (k==0 or l==0) and board[self.board.fix(i+k, 0)][self.board.fix(j+l, 1)]<=0):
                                dboard[i][j]-=1
                                if(dboard[i][j]<0):
                                    dboard[i][j] = 0
                elif(board[i][j]<0):
                    for k in range(-1, 2):
                        for l in range(-1, 2):
                            if((self.board.fix(i+k, 0), self.board.fix(j+l, 1))!=(i, j) and (k==0 or l==0) and board[self.board.fix(i+k, 0)][self.board.fix(j+l, 1)]>=0):
                                dboard[i][j]+=1
                                if(dboard[i][j]>0):
                                    dboard[i][j] = 0
        return dboard
    def bouzy(self, dilations=5, erosions=21):
        board = (128*np.array(deepcopy(self.board.state))).tolist()
        for i in range(dilations):
            board = self.dilate(board)
        for i in range(erosions):
            board = self.erode(board)
        return board
    def remove_dead(self, board):
        black_chains = []
        white_chains = []
        chains = []
        for i in range(len(board)):
            for j in range(len(board)):
                if(self.board.state[i][j]!=0):
                    in_existing_chain = False
                    for ind, k in enumerate(chains):
                        if((i-1, j) in k or (i, j-1) in k or (i+1, j) in k or (i, j+1) in k):
                            if(board[i][j]==1):
                                black_chains[ind].append((i, j))
                            else:
                                white_chains[ind].append((i, j))
                            in_existing_chain = True
                    if(not in_existing_chain):
                        if(board[i][j]==1):
                            black_chains.append([(i, j)])
                        else:
                            white_chains.append([(i, j)])
                    chains = black_chains+white_chains
        del chains
        black_eyes = []
        white_eyes = []
        for i in range(len(self.board.state)):
            for j in range(len(self.board.state[i])):
                pass #finish this function
        return board
    def score(self):
        self.board.state = remove_dead(deepcopy(self.board.state)) #add extra stuff for seki points and forced connections
        territory = self.bouzy()
        black_score = 0
        white_Score = 0
        for i in range(len(self.board.state)):
            for j in range(len(self.board.state[i])):
                if(self.board.state[i][j]==0):
                    if(territory[i][j]>0):
                        black_score+=1
                    if(territory[i][j]<0):
                        white_Score+=1
        if(self.scoring=="TERRITORY"):
            black_score+=self.prisoners[0]
            white_score+=self.prisoners[1]
        else:
            count = self.board.count()
            black_score+=count[0]
            white_score+=count[1]
        white_score+=self.komi
        winner = 1 if black_score>white_score else -1
        return black_score, white_score, winner
    def play(self, move):
        scores = {"black": None, "white": None}
        if(move=="PASS"):
            self.prisoners[(self.turn+1)%2]+=1
            if(self.passed_previous_move):
                self.finished = True
                result = score()
                self.winner = result[2]
                scores["black"] = result[0]
                scores["white"] = result[1]
            else:
                self.passed_previous_move = True
        elif(move=="RESIGN"):
            self.finished = True
            self.winner = players[(self.turn+1)%2].color
            self.passed_previous_move = False
        else:
            self.finished = False
            self.passed_previous_move = False
            captured = self.board.play(self.players[self.turn], move, self.superko)
            self.prisoners[0]+=captured[0]
            self.prisoners[1]+=captured[1]
            if(captured[2]):
                self.prisoners[(self.turn+1)%2]+=1
                if(self.passed_previous_move):
                    self.finished = True
                    result = score()
                    self.winner = result[2]
                    scores["black"] = result[0]
                    scores["white"] = result[1]
                else:
                    self.passed_previous_move = True
        self.turn+=1
        self.turn%=2
        return {"finished": self.finished, "winner": self.names[self.winner], "scores": scores}
testgame = Go()
