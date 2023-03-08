import datetime
import hashlib
import json
import requests

from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse


# Part 1 - Building a Blockchain

class Blockchain:

    def __init__(self):
        # chain is a list of blocks
        self.chain = []
        self.transactions = []
        # create the genesis block / we put previous_hash in quotes because we will use SHA256 function from hashlib
        # library which can only accept encoded strings
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()

    # since it's right after the mining of a block we will need to add the proof and previous_hash
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        # we are going to reset the list of transactions after we add them to the block because we don't want to add the
        # same transactions to the next block
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]  # -1 is the last element in the list

    def proof_of_work(self, previous_proof):
        # we are going to create a new proof of work
        new_proof = 1
        # we are going to check if the new proof is valid
        check_proof = False
        # we are going to create a while loop that will run until we find a valid proof
        while check_proof is False:
            # Q: purpose of this line?
            # A: we are going to create a hash of the new proof and the previous proof

            # Q: why do we need to encode the string?
            # A: because the hash function only accepts encoded strings

            hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    # takes the block as an argument and returns the SHA256 hash of the block
    def hash(self, block):
        # we are going to encode the block into a JSON string
        encoded_block = json.dumps(block, sort_keys=True).encode()
        # we are going to return the SHA256 hash of the encoded block
        return hashlib.sha256(encoded_block).hexdigest()

    # takes chain as a parameter because we're going to take the chain and iterate on each block of the chain
    def is_chain_valid(self, chain):
        # previous block is the first block of the chain
        previous_block = chain[0]
        block_index = 1
        # to iterate on each block of the chain
        while block_index < len(chain):
            # get the current block
            block = chain[block_index]
            # we are going to check if the previous hash of the current block is equal to the hash of the previous block
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            # proof of the current block
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            # we are going to check if the first 4 characters of the hash are equal to 0000
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    # add a transaction to the list of transactions
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        # get the previous block to figure out what's the current block in the chain and then add 1 to it
        previous_block = self.get_previous_block()
        # return the index of the previous block + 1
        return previous_block['index'] + 1

    # add a new node to the set of nodes
    def add_node(self, address):
        # ParseResult(scheme='http', netloc='127.0.0.1:5000', path='/', params='', query='', fragment='')
        parsed_url = urlparse(address)
        # parsed_url.netloc = '127.0.0.1:5000'
        self.nodes.add(parsed_url.netloc)

    # replace the chain with the longest chain if needed
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            # we are going to send a GET request to the node to get the chain
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                # get the length of the chain
                length = response.json()['length']
                # get the chain
                chain = response.json()['chain']
                # check if the length is greater than the max length and if the chain is valid
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        # if we found the longest chain then we are going to replace the chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)
# app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockchain = Blockchain()


# Part 2 - Mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    # get the previous block
    previous_block = blockchain.get_previous_block()
    # get the previous proof
    previous_proof = previous_block['proof']
    # get the proof of work
    proof = blockchain.proof_of_work(previous_proof)
    # get the previous hash
    previous_hash = blockchain.hash(previous_block)
    # add a transaction to the blockchain
    blockchain.add_transaction(sender=node_address, receiver='Jamie', amount=1)
    # create a new block
    block = blockchain.create_block(proof, previous_hash)
    # we are going to create a response
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200


# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


# Checking if the Blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is not valid.'}
    return jsonify(response), 200


# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    # get the json object from the request
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    # if all the keys in the transaction_keys list are not in the json object then return an error
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    # get the index of the block where the transaction will be added
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201


# Part 3 - Decentralizing our Blockchain

# Connecting new nodes to the network
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    # get the nodes from the json object
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The VibeCoin Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201


# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200


# Running the app
app.run(host='0.0.0.0', port=5001)
