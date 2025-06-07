#!/bin/env python3
import datetime
import hashlib
import json
import os


class Block:
    def __init__(self, timestamp, data, previous_hash):
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        return hashlib.sha256(
            json.dumps(
                {
                    "timestamp": self.timestamp.isoformat(),
                    "data": self.data,
                    "previous_hash": self.previous_hash,
                },
                indent=4,
            ).encode("utf-8"),
        ).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = []
        self.genesis_block = Block(
            datetime.datetime.now(), "Genesis block", "0"
        )
        self.chain.append(self.genesis_block)

    def add_block(self, data, previous_hash):
        new_block = Block(
            datetime.datetime.now(), data, previous_hash
        )
        self.chain.append(new_block)

    def get_block(self, index):
        return self.chain[index]

    def get_latest_block(self):
        return self.chain[-1]



    # Creamos la blockchain
blockchain = Blockchain()

    # Agregamos un bloque
blockchain.add_block("Hola, mundo!", blockchain.chain[-1].hash)



def main(args):
    global blockchain
    print("Args dentro de blockchain", args)


    # Si se pasan argumentos, los usamos
    if len(args) > 0:
        # El primer argumento debe ser el comando
        command = args[0]
        # Los siguientes argumentos son los parámetros del comando
        params = args[1:]

        # Implementamos algunos comandos básicos
        if command == "add":
            # Agregamos un bloque con los parámetros dados
            
            try:
                blockchain.add_block(*params)
                return
            except Exception as e:
                print("ERROR:",e,*params)
                return
                
                
        if command == "get":
            # Imprimimos el bloque con el índice dado

            try:
                print(blockchain.get_block(int(params[0])))
                return
            except Exception as e:
                print("ERROR:",e,*params)
                return


        if command == "latest":
            # Imprimimos el bloque más reciente
            try:
                print(blockchain.get_latest_block())
                return
            except Exception as e:
                print("ERROR:",e,*params)
                return

        if command == "list":
            try:
            # Imprimimos los bloques
                for block in blockchain.chain:
                    print(block)
                return
            except Exception as e:
                print("ERROR:",e)
                return


        else:
        # Si no se pasan argumentos, imprimimos la ayuda
            print(
                "Uso: blockchain [comando] [parámetros]"
                "\nComandos:"
                "\n    add: Agrega un bloque"
                "\n    get: Imprime un bloque"
                "\n    latest: Imprime el bloque más reciente"
            )




