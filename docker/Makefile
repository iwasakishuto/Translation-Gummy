help:
	@cat Makefile

DATA?="${HOME}/Data"
DOCKER_FILE=docker-compose.yml
DOCKER=docker-compose
TEST=tests/
HOST_PORT=8888
SRC?=$(shell dirname `pwd`)
EXAMPLES_DIR=$(SRC)/examples

build:
	$(DOCKER) build gummy

bash: build
	$(DOCKER) run -v $(SRC):/src/workspace -v $(DATA):/data gummy bash

ipython: build
	$(DOCKER) run -v $(SRC):/src/workspace -v $(DATA):/data gummy ipython

notebook: build
	$(DOCKER) run -p $(HOST_PORT):8888 -v $(SRC):/src/workspace -v $(DATA):/data gummy

examples: build
	$(DOCKER) run -p $(HOST_PORT):8888 -v $(SRC):/src/workspace -v $(EXAMPLES_DIR):/data/gummy_examples gummy
