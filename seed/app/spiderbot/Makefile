
CC = gcc
CFLAGS = -Wall -O2
TARGET = spiderbot_release
SRC = spiderbot_core.c
LIBS = -lsqlite3 -lcurl


all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(SRC) -o $(TARGET) $(CFLAGS) $(LIBS)


clean:
	rm-f $(TARGET)
