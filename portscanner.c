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
		fprintf(stderr,"Error- invalid input arguments\n");
		exit(-1);
	}
	strncpy(hostname, argv[1], sizeof(hostname));
	
	//initialize the port numbers
	if (argc == 4){
		start = atoi(argv[2]);
		end = atoi(argv[3]);
	}
	else {
		start = 1;
		end = 1024;
	}
	
	//initialize the sock_addr_in structure
	strncpy((char*)&sa , "", sizeof sa);
	sa.sin_family = AF_INET;
	printf("sin_family: %d\n", sa.sin_family);

	//hostname to ip address
	if((host = gethostbyname(argv[1])) != 0){
		strncpy((char*)&sa.sin_addr, (char*)host->h_addr, sizeof sa.sin_addr);
	}

	else{
		herror(argv[1]);
		exit(-1);
	}

	printf("h_name is:%s\n", host->h_name);
	printf("h_addrtype is:%d\n", host->h_addrtype);
	printf("h_length is: %d\n", host->h_length);
	printf("h_aliases is: %s\n", host->h_aliases[0]);


	printf("starting the for loop\n");
	
	for (ii = start; ii <= end; ii++){
		//give the port number to check 
		sa.sin_port = htons(ii);
		printf("sin_port: %d\n", sa.sin_port);
		sock = socket(AF_INET, SOCK_STREAM, 0);

		if (sock < 0){
			perror("\nSocket");
			exit(1);
		}
		err = connect(sock, (struct sockaddr*)&sa, sizeof sa);

		if (err < 0){
			fflush(stdout);
		}
		//connected
		else{
			printf("%-5d open\n",ii);
		}
		printf("3\n");
		close(sock);
	}
	printf("\r");
	fflush(stdout);
	return(0);
}

