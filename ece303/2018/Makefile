INPUT ?= ./file_1MB.txt
OUTPUT ?= ./output.txt


test: receiver.o sender.o

sender.o: receiver.o
	time python2 sender.py < $(INPUT) &
receiver.o:
	python2 receiver.py > $(OUTPUT) & 
diff:
	diff $(INPUT) $(OUTPUT)
kill:
	pkill python2
clean:
	rm *.log $(OUTPUT) *.pyc
