#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

int main(int argc, char **argv)
{
	struct hostent *host;
	int err,ii, sock, start, end;
	char hostname[100];
	struct sockaddr_in sa;

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
		start = atoi(argv[2]);
		end = atoi(argv[3]);
	}
	else {
		start = 1;
		end = 1024;
	}
	
	//initialize the sock_addr_in structure
	memset((char*)&sa , 0, sizeof sa);
	sa.sin_family = AF_INET;

	//hostname to ip address
	if((host = gethostbyname(argv[1])) != 0){
		strncpy((char*)&sa.sin_addr, (char*)host->h_addr, sizeof sa.sin_addr);
	}

	else{
		herror(argv[1]);
		exit(-1);
	}

	
	for (ii = start; ii <= end; ii++){
		sa.sin_port = htons(ii);
		sock = socket(AF_INET, SOCK_STREAM, 0);

		if (sock < 0){
			perror("\nSocket");
			exit(1);
		}
		struct timeval timeout;
		timeout.tv_sec = 2;
		timeout.tv_usec = 0;

		if (setsockopt (sock, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout, sizeof(timeout)) < 0)
			fprintf(stderr,"setsockopt failed\n");

		if (setsockopt (sock, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout, sizeof(timeout)) < 0)
			fprintf(stderr,"setsockopt failed\n");

		err = connect(sock, (struct sockaddr*)&sa, sizeof sa);

		if (err < 0){
			printf("%-5d closed/blocked\n",ii);
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

