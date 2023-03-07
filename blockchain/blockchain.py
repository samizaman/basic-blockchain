# Importing the libraries
import datetime
import hashlib
import json

from flask import Flask, jsonify


# Part 1 - Building a Blockchain

class Blockchain:

    def __init__(self):
        # chain is a list of blocks
        self.chain = []
        # create the genesis block / we put previous_hash in quotes because we will use SHA256 function from hashlib
        # library which can only accept encoded strings
        self.create_block(proof=1, previous_hash='0')

    # since it's right after the mining of a block we will need to add the proof and previous_hash
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash}
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


# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)
# app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Creating a Blockchain
blockchain = Blockchain()


# Mining a new block
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
    # create a new block
    block = blockchain.create_block(proof, previous_hash)
    # we are going to create a response
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash']}
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


# Running the app
app.run(host='0.0.0.0', port=5000)
