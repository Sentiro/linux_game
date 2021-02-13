#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/epoll.h>
#include <string.h>

#define MAX_EVENTS 10

//arguments for game
#define MAX_ROOMS 10
#define MAX_PLAYERS 5
int gravity= 0.15;

int bird_movement=0;
//int rooms[MAX_ROOMS][MAX_PLAYERS+1]={0};
int next_player_id=0;




struct user{
	int fd;
    int ID;
    int score;
    int posx;
    int posy;
	int bird_movement;
    int die;
    int heart;
};

struct room
{
	int room_id;
	struct user players[MAX_PLAYERS];
	
}rooms[MAX_ROOMS];

void init_struct(){
	int i=0;
	int j = 0; 
	for(i=0;i<MAX_ROOMS;i++){
		rooms[i].room_id=0;
		for (j = 0; j < MAX_PLAYERS; j++)
		{
			rooms[i].players[j].ID=-1;
			rooms[i].players[j].fd=-1;
			rooms[i].players[j].die=0;
			rooms[i].players[j].heart=3;
			rooms[i].players[j].posx=0;
			rooms[i].players[j].posy=0;
			rooms[i].players[j].score=0;
			rooms[i].players[j].bird_movement=0;
		}
		
	}
}

void create_room(int fd,char *buf){
	int i;
	int userID;
	char str[6];
	char buff[1024];
	if(strlen(buf)<6)
		return;
	sscanf(buf, "%d %d",&i,&userID);
	// find available room
	i=0;
	for(i=0;i<MAX_ROOMS;i++){
        if(rooms[i].room_id==0){
			//add owner to room
			rooms[i].room_id=1;
			rooms[i].players[0].fd=fd;
			printf("create room player.fd: %d fd:%d\n",rooms[i].players[0].fd,fd);
			rooms[i].players[0].ID=userID;
			strcpy(str,"1 ");
			sprintf(buff,"%d|#|",i+2000); //room_id 2005
			strcpy(str+2,buff);
			write(fd, str, sizeof(str));
            break;
        } 
    }
}

void get_player_list(int fd,char*buf){
	int room=0;
	int user=0;
	int cmd=0;
	char res[100]={0};
	memset(res,0,100);
	if(strlen(buf)<10)
		return;
	printf("in player list:%s\n",buf);
	sscanf(buf, "%d %d %d",&cmd,&user,&room);
	if(room==-1){
		write(fd, "haven't joint a room\n", strlen("haven't joint a room\n"));
		return;
	}
	room=room-2000;
	sprintf(res,"%d %d %d %d %d %d|#|",6, 
								rooms[room].players[0].ID,
								rooms[room].players[1].ID,
								rooms[room].players[2].ID,
								rooms[room].players[3].ID,
								rooms[room].players[4].ID);
	write(fd, res, strlen(res));	
}

void handle_join_room(int fd,char* buf){
	int roomid;
	int userID;
	int cmd;
	char res[100];
	char res2[100];

	if(strlen(buf)<10)
		return;

	sscanf(buf, "%d %d %d",&cmd,&userID,&roomid);
	sprintf(res,"%d %d|#|",cmd, roomid);
	sprintf(res2,"%d %d|#|",5, userID);
	printf("%d: join room\n",userID);
	roomid=roomid-2000;
	if(roomid<0||roomid>4){
		write(fd, "room not exist|#|", sizeof("room not exist|#|"));
		return;
	}
	if(rooms[roomid].room_id==0){
		write(fd, "room not exist|#|", sizeof("room not exist|#|"));
		return;
	}else{
		int j=0;
		for(j=0;j<MAX_PLAYERS;j++){
			
			if(rooms[roomid].players[j].fd==-1){//get avaliable sit
				rooms[roomid].players[j].fd=fd;
				rooms[roomid].players[j].ID=userID;
				write(fd, res, strlen(res));
				return;
			}else//conform others
			{
				printf("sending joining info to %d fd:%d: %s\n",rooms[roomid].players[j].ID,rooms[roomid].players[j].fd,res2);
				write(rooms[roomid].players[j].fd, res2, strlen(res2));	
			}
		}
		write(fd, "2 no place in this room \r\n\r\n|#|", sizeof("2 no place in this room \r\n\r\n|#|"));
	}
}
void die(int fd, char *buf){
	int roomid;
	int userID;
	int cmd;
	int max_score=0;
	int max_client=0;
	int flag=0;//no one live
	if(strlen(buf)<10)
		return;
	sscanf(buf, "%d %d %d",&cmd,&userID,&roomid);
	//update player state
	printf("%d\n",roomid);
	roomid=roomid-2000;
	int j=0;
	for(j=0;j<MAX_PLAYERS;j++){	
			if(rooms[roomid].players[j].fd==fd){//get avaliable sit
				rooms[roomid].players[j].die=1;
				printf("update die\n");
			}
		}
	int i;
		for(i=0;i<MAX_PLAYERS;i++){
			if(rooms[roomid].players[i].fd!=-1&&rooms[roomid].players[i].die==0){
				flag=1;//some alive
				break;
			}
		}

	if(flag==0&&rooms[roomid].players[1].fd>-1){//inform all clients
		printf("in send\n");
		printf("cur ID:%d,%d\n",rooms[roomid].players[0].ID,rooms[roomid].players[1].ID);
		printf("cur score:%d,%d\n",rooms[roomid].players[0].score,rooms[roomid].players[1].score);
			if(rooms[roomid].players[0].score>rooms[roomid].players[1].score){
				write(rooms[roomid].players[0].fd, "7 WIN|#|", strlen("7 WIN|#|"));
				write(rooms[roomid].players[1].fd, "7 LOSE|#|", strlen("7 LOSE|#|"));
			}else if(rooms[roomid].players[0].score<rooms[roomid].players[1].score){
				write(rooms[roomid].players[1].fd, "7 WIN|#|", strlen("7 WIN|#|"));
				write(rooms[roomid].players[0].fd, "7 LOSE|#|", strlen("7 LOSE|#|"));
			}else
			{
				write(rooms[roomid].players[0].fd, "7 DRAW GAME|#|", strlen("7 DRAW GAME|#|"));
				write(rooms[roomid].players[1].fd, "7 DRAW GAME|#|", strlen("7 DRAW GAME|#|"));
			}
			
	}else{
		write(rooms[roomid].players[0].fd, "7 SPACE FOR NEXT GAME|#|", strlen("7 SPACE FOR NEXT GAME|#|"));
	}
		
	
		
}

void game_start(int fd, char *buf){
	
	int roomid;
	int userID;
	int cmd;
	int max_score=0;
	int max_client=0;
	int flag=0;//no one live
	if(strlen(buf)<10)
		return;
	sscanf(buf, "%d %d %d",&cmd,&userID,&roomid);
	//update player state
	printf("%d\n",roomid);
	roomid=roomid-2000;
	int j=0;
	for(j=0;j<MAX_PLAYERS;j++){	
			if(rooms[roomid].players[j].fd==fd){//get avaliable sit
				rooms[roomid].players[j].die=0;
				printf("update start\n");
			}
		}
}

void delete_room(int fd,int roomid){
	int id=roomid-1000;
	rooms[id].room_id=0;
	write(fd, "OK|#|", sizeof("OK|#|"));
}

void create_player_id(int fd){
	char str[10]={0};
	char buff[1024];
	strcpy(str,"0 ");
	sprintf(buff,"%d|#|",next_player_id+1000); //available_player_id 1005
	strcpy(str+2,buff);
    write(fd, str, strlen(str));
	next_player_id+=1;

}


void update_pos(int fd,char* buf){
	int roomid;
	int playerid;
	int score;
	int cmd;
	int x=0;
	int y=0;
	int i=0;
	int move=0;
	int action=-1;
	char res[100];
	memset(res,0,100);
	strcpy(res,buf);
	printf("in update_pos:%s\n",res);
	if(strlen(res)<20)
		return;

	sscanf(res, "%d %d %d %d %d %d",&cmd,&playerid,&roomid,&x,&y,&action);

	memset(res,0,100);
	snprintf(res,25,"%d %d %d %d %d %d|#|",cmd, playerid, roomid,x,y,action);
	// modify 
	roomid=roomid-2000;
	if(roomid<0||roomid>4){
		write(fd, res, strlen(res));
		return;
	}

	for(i=0;i<MAX_PLAYERS;i++){
		printf("sending pos to %d fd:%d: %s\n",rooms[roomid].players[i].ID,rooms[roomid].players[i].fd,res);
		if(rooms[roomid].players[i].fd!=-1){
			write(rooms[roomid].players[i].fd, res, strlen(res));	
		}
	}
	
}

void update_score(int fd,char* buf){
	int roomid;
	int playerid;
	int score;
	int cmd;
	int i=0;
	char res[100];
	memset(res,0,100);
	strcpy(res,buf);
	printf("in update_score:%s\n",res);
	if(strlen(res)<12)
		return;
	sscanf(res, "%d %d %d %d",&cmd,&playerid,&roomid, &score);

	snprintf(res,16,"%d %d %d %d|#|",cmd, playerid, roomid,score);
	
	// modify 
	roomid=roomid-2000;
	if(roomid<0||roomid>4){
		write(fd, res, strlen(res));
		return;	
	}
	

	for(i=0;i<MAX_PLAYERS;i++){
		printf("sending score to %d fd:%d: %s\n",rooms[roomid].players[i].ID,rooms[roomid].players[i].fd,res);
		if(rooms[roomid].players[i].fd!=-1){
			write(rooms[roomid].players[i].fd, res, strlen(res));	
			if(rooms[roomid].players[i].fd==fd){
			//int j=rooms[roomid][i];
			rooms[roomid].players[i].score==score;
		}
		}
		


	}
	
}

void send_mes(int fd, char *buf){
	int roomid;
	int playerid;
	int score;
	int cmd;
	int i=0;
	char mes[100];
	char res[100];
	memset(res,0,100);
	strcpy(res,buf);
	printf("in send_mes:%s\n",res);
	if(strlen(res)<12)
		return;
	sscanf(res, "%d %d %d %s",&cmd,&playerid,&roomid, mes);

	snprintf(res,25,"%d %d %d %s|#|",cmd, playerid, roomid,mes);
	
	// modify 
	roomid=roomid-2000;
	if(roomid<0||roomid>4){
		return;	
	}
	for(i=0;i<MAX_PLAYERS;i++){
		printf("sending mes to %d fd:%d: %s\n",rooms[roomid].players[i].ID,rooms[roomid].players[i].fd,res);
		if(rooms[roomid].players[i].fd!=fd){
			write(rooms[roomid].players[i].fd, res, strlen(res));	
		}
	}
}

void handle_get(int fd, char path[]){
	char buf[1024];
	int n;
	int filefd;
	if((filefd=open(path+1, O_RDONLY))==-1){
		write(fd, "HTTP/1.0 404 Not Found\r\n\r\n|#|", 26);
		return;
	}
	write(fd, "HTTP/1.0 200 OK\r\n\r\n|#|", 19);
	while((n=read(filefd, buf, sizeof(buf)))>0){
		write(fd, buf, n);
	}	
	close(filefd);
}

void setnonblocking(int fd) {
        int opts;
        opts=fcntl(fd, F_GETFL);
        if(opts<0) {
                perror("fcntl(sock,GETFL)");
                exit(1);
        }
        opts = opts|O_NONBLOCK;
        if(fcntl(fd, F_SETFL, opts)<0) {
                perror("fcntl(sock,SETFL,opts)");
                exit(1);
        }
}



int main(int ac, char *av[]){
	struct sockaddr_in addr;
	char buf[1024];
	int n;
	char cmd[512];
	char path[512];
	int sockfd;
	//char *command[100];
	char *p[100];
	int m;

	struct epoll_event ev, events[MAX_EVENTS];
	int listen_sock, conn_sock, nfds, epollfd;

	init_struct();

	signal(SIGPIPE, SIG_IGN);

    chdir("/var/www/html");

	if(ac<2){
		printf("type in PORT as a argument\n");
		exit(1);
	}

	listen_sock  =  socket(AF_INET,  SOCK_STREAM, 0);

	addr.sin_family = AF_INET;
	addr.sin_port = htons(atoi(av[1]));
	addr.sin_addr.s_addr = INADDR_ANY;

	if(bind(listen_sock, (const struct sockaddr *)&addr, sizeof(struct sockaddr_in))==-1){
		perror("cannot bind");
		exit(1);
	}	

	listen(listen_sock, 1);

	epollfd = epoll_create(10);
	if (epollfd == -1) {
		perror("epoll_create");
		exit(EXIT_FAILURE);
	}

	ev.events = EPOLLIN;
	ev.data.fd = listen_sock;
	if (epoll_ctl(epollfd, EPOLL_CTL_ADD, listen_sock, &ev) == -1) {
		perror("epoll_ctl: listen_sock");
		exit(EXIT_FAILURE);
	}


	while(1){
		nfds = epoll_wait(epollfd, events, MAX_EVENTS, -1);
		if (nfds == -1) {
			perror("epoll_pwait");
			exit(EXIT_FAILURE);
		}
		for (n = 0; n < nfds; ++n) {
			if (events[n].data.fd == listen_sock) {
				conn_sock = accept(listen_sock, NULL, NULL);
				if (conn_sock == -1) {
					perror("accept");
					exit(EXIT_FAILURE);
				}
				setnonblocking(conn_sock);
				ev.events = EPOLLIN | EPOLLET;
				ev.data.fd = conn_sock;
				if (epoll_ctl(epollfd, EPOLL_CTL_ADD, conn_sock,
							&ev) == -1) {
					perror("epoll_ctl: conn_sock");
					exit(EXIT_FAILURE);
				}
			} else {
				memset(buf,0,512);
				sockfd=events[n].data.fd;
				if ((n = read(sockfd, buf, sizeof(buf))) <= 0) {
					/*4connection closed by client */
					close(sockfd);
				} else {
					int in,k=0;
					char *temp=buf;
					char *outer_ptr = NULL;
  					char *inner_ptr = NULL;
					printf("%s\n",buf);
					printf("before i:%d\n",in);
					while ((p[in] = strtok_r(temp, "$$", &outer_ptr)) != NULL)
					{
						temp = p[in];
						while ((p[in] = strtok_r(temp, "|#|", &inner_ptr)) != NULL)
						{
						in++;
						temp = NULL;
						}
						temp = NULL;
					}
					printf("after i:%d\n",in);     
					for (k = 0; k < in; k++)
					{
						char buftemp[100];
					    memset(buftemp,0,100);
						strcpy(buftemp,p[k]);
						printf(">%s<\n", buftemp);
						sscanf(buftemp, "%s%s", cmd, path);
						if(strcmp(cmd, "GET")==0){
							handle_get(sockfd, path);
						}else if(strcmp(cmd,"GETID")==0){
							//create_player_id(sockfd);
							char str[6];
							char buff[1024];
							int a=next_player_id+1000;
							next_player_id+=1;
							strcpy(str,"0 ");
							sprintf(buff,"%d",a);
							strcpy(str+2,buff);
							write(sockfd, str, sizeof(str));
						}else if(strcmp(cmd,"BYE")==0){	
							int i=0;
							int j;
							for(i=0;i<MAX_ROOMS;i++){
								for(j=0;j<MAX_PLAYERS;j++){
									if(rooms[i].players[j].fd==sockfd){
										rooms[i].players[j].fd=-1;
										rooms[i].players[j].ID=-1;
									}
								}
							}
							close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"1")==0){
							create_room(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"2")==0){
							get_player_list(sockfd,buftemp);
							handle_join_room(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"3")==0){
							update_score(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"4")==0){
							update_pos(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"6")==0){
							//printf("out of player list");
							get_player_list(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"7")==0){
							printf("out of die\n");
							die(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"8")==0){
							//printf("out of player list");
							get_player_list(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}else if(strcmp(cmd,"9")==0){
							//printf("out of player list");
							send_mes(sockfd,buftemp);
							// close(sockfd);	/*close the sockfd*/
						}
						else{
							write(sockfd, "HTTP/1.0 ? 400 Bad Request\r\n\r\n|#|", sizeof("HTTP/1.0 400 Bad Request\r\n\r\n|#|"));
						}
					} 
					in=0;
					
					
				}

			}
		}
	}
	return 0;
}

