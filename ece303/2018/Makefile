INPUT ?= ./test_files/file_1MB.txt
OUTPUT ?= ./output.txt


test: sender

sender: receiver
	time python2 sender.py < $(INPUT) &
receiver:
	python2 receiver.py > $(OUTPUT) & 
diff:
	diff $(INPUT) $(OUTPUT)
kill:
	pkill python2
clean:
	rm *.log $(OUTPUT) *.pyc
