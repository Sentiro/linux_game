import pygame, sys, random,socket

# web connect variables

class Client:

    s = socket.socket() 

    def __init__(self,addr,port):
        self.host=addr  
        self.port=port
        # self.s.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,True)
        # self.s.ioctl(socket.SIO_KEEPALIVE_VALS,
        #            (1,
        #            60*1000,
        #            30*1000)
        #)
        self.create_connect()
        self.id=self.get_client_ID()
        self.room_id=-1
        print(self.id)
        
        #self.get_connect(addr="192.168.235.132")

    def close_connect(self):
        info="BYE"+"|#|"
        info=info.encode("utf-8")
        self.s.send(info)
        self.s.close()

    def create_connect(self):
        self.s.connect((self.host, self.port)) 

    def get_client_ID(self):
        info="GETID"+"|#|"
        # self.create_connect()
        self.s.send(info.encode("utf-8"))
        #self.id=str[:2]
        str=self.s.recv(1024)
        print("getid:"+str.decode('utf-8'))
        if(str[0]==48):
            return str[2:].decode('utf-8')
        # self.close_connect()

    def get_room(self): #return room id
        info="1 "+self.id+"|#|"
        #self.create_connect()
        self.s.send(info.encode("utf-8"))
        #res=self.s.recv(1024)
        #self.room_id=res.decode('utf-8')[2:6]
        #return self.room_id
        #self.close_connect()

    def join_room(self,id):
        info="2 "+self.id+" "+str(id)+"|#|"
        #self.create_connect()
        self.s.send(info.encode("utf-8"))
        #self.close_connect()
    
    def get_players(self,id):
        info=self.id+"3 "+id+"|#|"
        #self.create_connect()
        self.s.send(info.encode("utf-8"))
        while(True):
            if(self.s.recv(1024)=="success"):
                break
            else:
                self.s.send(info.encode("utf-8"))

    def get_player_list(self,id):
        info="6 "+self.id+" "+str(id)+"|#|"
        self.s.send(info.encode("utf-8"))

    def update_player(self,x,y,action):
        #(x,y) shows position of this player
        #for action: 1.jump 0.not jump
        info="4 "+str(self.id)+" "+str(self.room_id)+" "+str(x)+" "+str(y)+" "+str(action)+"|#|"
        #if self.s.
        #self.create_connect()
        self.s.send(info.encode("utf-8"))
        
        

    def send_score(self,score):
        info="3 "+self.id+" "+str(self.room_id)+" "+str(score)+"|#|"
        #if self.s.
        #self.create_connect()

        self.s.send(info.encode("utf-8"))
    
    def send_ready(self):
        info="8 "+self.id+" "+str(self.room_id)+"|#|"
        #if self.s.
        #self.create_connect()

        self.s.send(info.encode("utf-8"))
    def send_die(self):
        print("send die!!!!!")
        if self.room_id==-1:
            return
        info="7 "+self.id+" "+str(self.room_id)+"|#|"
        print("send info:",info)
        #if self.s.
        #self.create_connect()
        self.s.send(info.encode("utf-8"))

    def send_mes(self,mes):
        info="9 "+self.id+" "+str(self.room_id)+" "+mes+"|#|"
        #if self.s.
        #self.create_connect()

        self.s.send(info.encode("utf-8"))

   


#pygame.mixer.pre_init(frequency = 44100, size = 16, channels = 2, buffer = 1024)

if __name__ == "__main__":
    client=Client("192.168.235.132",8080)
