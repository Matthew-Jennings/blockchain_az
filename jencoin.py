import datetime
import hashlib
from http import HTTPStatus
import json
import logging
from uuid import uuid4
from urllib.parse import urlparse

from flask import Flask, jsonify, request
import requests


class Blockchain:
    def __init__(self):
        self.chain = []
        self.txs = []
        self.nodes = set()

        self.create_block(proof=1, previous_hash="0")

    def create_block(self, proof, previous_hash):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": str(datetime.datetime.now()),
            "proof": proof,
            "previous_hash": previous_hash,
            "txs": self.txs,
        }
        self.txs = []
        self.chain.append(block)
        return block

    def hash_operation(self, current_proof, previous_proof):

        # This can be any NON-SYMMETRIC function. It shouldn't give the
        # same result if current and previous proofs are reversed.
        func = current_proof**2 - previous_proof**2

        return hashlib.sha256(str(func).encode()).hexdigest()

    def previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 0
        check_proof = False

        while not check_proof:
            hash_op = self.hash_operation(new_proof, previous_proof)
            if hash_op[:4] == "0000":
                check_proof = True
            else:
                new_proof += 1

        return new_proof

    def hash(self, block):
        block_as_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_as_str).hexdigest()

    def is_chain_valid(self, chain):

        for i, block in enumerate(chain[1:], start=1):
            prev_block = chain[i - 1]

            logging.debug("previous block index: %i", prev_block["index"])
            logging.debug("current block index: %i", block["index"])

            if block["index"] != (prev_block["index"] + 1):
                raise ValueError("Chain indicies non-sequential")

            regenerated_prev_block_hash = self.hash(prev_block)

            logging.debug("recorded previous block hash: %s", block["previous_hash"])
            logging.debug(
                "regenerated previous block hash: %s", regenerated_prev_block_hash
            )

            if block["previous_hash"] != regenerated_prev_block_hash:
                # must check for falsehood, since any single failure
                # means chain is not valid
                return False

            hash_op = self.hash_operation(block["proof"], prev_block["proof"])
            logging.debug("hash_op result: %s", hash_op)

            if hash_op[:4] != "0000":
                return False

        return True

    def add_tx(self, sender, receiver, amount):
        self.txs.append({"sender": sender, "receiver": receiver, "amount": amount})

        previous_block = self.previous_block()
        return previous_block["index"] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)

        for node in network:
            response = requests.get(f"http://{node}/get_chain")

            if response.status_code == HTTPStatus.OK:
                length = response.json()["length":]
                chain = response.json()["chain"]

                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain

        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    app = Flask(__name__)

    node_address = str(uuid4()).replace("_", "")

    blockchain = Blockchain()

    @app.route("/mine_block", methods=["GET"])
    def mine_block():
        previous_block = blockchain.previous_block()

        proof = blockchain.proof_of_work(previous_block["proof"])

        previous_hash = blockchain.hash(previous_block)

        txs = blockchain.add_tx(sender=node_address, receiver="Matthew", amount=6.25)

        block = blockchain.create_block(proof, previous_hash)

        response = {
            "message": "Congratulations, you just mined a block!",
            "index": block["index"],
            "timestamp": block["timestamp"],
            "proof": block["proof"],
            "previous_hash": block["previous_hash"],
            "txs": block["txs"],
        }

        return jsonify(response), HTTPStatus.OK

    @app.route("/get_chain", methods=["GET"])
    def get_chain():

        response = {"chain": blockchain.chain, "length": len(blockchain.chain)}

        return jsonify(response), HTTPStatus.OK

    @app.route("/is_chain_valid", methods=["GET"])
    def is_chain_valid():

        if blockchain.is_chain_valid(blockchain.chain):
            response = {"message": "The blockchain is valid! :)"}
        else:
            response = {"message": "The blockchain is NOT valid! :("}

        return jsonify(response), HTTPStatus.OK

    # Must come after decorators above
    app.run(host="0.0.0.0", port=5000)

    @app.route("/add_tx", methods=["POST"])
    def add_tx():
        json = requests.get_json()

        tx_keys = ["sender", "receiver", "amount"]

        if not all(key in json for key in tx_keys):
            return "Some elements of the tx are missing", HTTPStatus.BAD_REQUEST

        idx = blockchain.add_tx(json["sender"], json["receiver"], json["amount"])

        response = {"message": f"This tx will be added to block #{idx}"}

        return response, HTTPStatus.CREATED
