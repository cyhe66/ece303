#include <stdio.h> //fprintf
#include <stdlib.h> //exit
#include <netdb.h> //network stuff
#include <string.h> //strcpy
#include <unistd.h> //close
#include <ctype.h> //isdigit
//socket stuff
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int main(int argc, char **argv)
{
	struct hostent *host;
	int err,ii, sock, start, end, ttl, saddr_size, datasize;
	char hostname[100];
	struct sockaddr_in sa;
	struct sockaddr saddr;

	if (argc < 2 || argc > 4) {
		fprintf(stderr,"Usage: %s <hostname> [start] [end]\n", argv[0]);
		exit(-1);
	}
	strncpy(hostname, argv[1], sizeof(hostname));
	
	/*
	 * DEFAULT PORTSCAN
	 * START -> 1
	 * END   -> 1024
	 */
	if (argc == 4){
		start = strtol(argv[2], NULL, 10);
		end = strtol(argv[3], NULL, 10);
	}
	else {
		start = 1;
		end = 1024;
	}
	
	//initialize the sock_addr_in structure
	memset((char*)&sa , 0, sizeof sa);
	sa.sin_family = AF_INET;

	//hostname to ip address
	if (isdigit(argv[1][0])){
		sa.sin_addr.s_addr = inet_addr(argv[1]);
	}	
	else if((host = gethostbyname(argv[1])) != 0){
		strncpy((char*)&sa.sin_addr, (char*)host->h_addr, sizeof sa.sin_addr);
	}
	else{
		herror(argv[1]);
		exit(-1);
	}

	for (ii = start; ii <= end; ii++){
		sa.sin_port = htons(ii);
		sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

		if (sock < 0){
			perror("\nSocket");
			exit(1);
		}

		struct timeval timeout;
		timeout.tv_sec = 0;
		timeout.tv_usec = 1500;

		if (setsockopt (sock, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout, sizeof(timeout)) < 0)
			fprintf(stderr,"setsockopt failed\n");

		if (setsockopt (sock, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout, sizeof(timeout)) < 0)
			fprintf(stderr,"setsockopt failed\n");

		err = connect(sock, (struct sockaddr*)&sa, sizeof sa);

		if (err < 0){
			//printf("%-5d closed/blocked\n",ii);
		}
		//connected
		else{
			printf("%-5d open\n",ii);
		}
		close(sock);
	}
	printf("\r");
	fflush(stdout);
	return(0);
}

