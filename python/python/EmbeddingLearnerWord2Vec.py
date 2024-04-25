import math
import sys
import time
import json
import tensorflow as tf
import numpy as np
from sklearn.decomposition import PCA
from os import getcwd
from json.decoder import JSONDecodeError
from os.path import join
from transformers import BertTokenizer, TFBertModel

nb_tokens_in_context = 20
name_embedding_size = 200  # Set the desired embedding size

class EncodedSequenceReader(object):
    def __init__(self, data_paths):
        self.data_paths = data_paths

    def __iter__(self):
        for data_path in self.data_paths:
            print("Reading file " + data_path)
            with open(data_path) as file:
                try:
                    token_sequences = json.load(file)
                    for seq in token_sequences:
                        yield seq
                except JSONDecodeError as e:
                    print(f"Warning: Ignoring {data_path} due to JSON decode error")

def tokens_to_input_ids(tokens, tokenizer):
    return tokenizer.convert_tokens_to_ids(tokens)

if __name__ == '__main__':
    # arguments: <token_to_nb_file> <list of .json files with tokens>

    token_to_nb_file = sys.argv[1]
    data_paths = list(map(lambda f: join(getcwd(), f), sys.argv[2:]))
    if len(data_paths) == 0:
        print("Must pass token_to_nb files and at least one data file")
        sys.exit(1)

    # Initialize BERT tokenizer
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    token_seqs = list(EncodedSequenceReader(data_paths))
    total_seqs = len(token_seqs)
    token_to_vector = dict()

    # Initialize BERT model
    model = TFBertModel.from_pretrained('bert-base-uncased')
    pca = PCA(n_components=200)

    chunk_size = 512  # Maximum sequence length BERT can handle
    chunk_embeddings=[]
    for i, token_seq in enumerate(token_seqs):
        num_chunks = math.ceil(len(token_seq) / chunk_size)
        
        for j in range(num_chunks):
            start_idx = j * chunk_size
            end_idx = min((j + 1) * chunk_size, len(token_seq))
            chunk_token_seq = token_seq[start_idx:end_idx]
            
            input_ids = tokens_to_input_ids(chunk_token_seq, tokenizer)
            input_ids = tf.constant([input_ids])
            outputs = model(input_ids)
            token_embeddings = outputs.last_hidden_state
            
            flattened_embeddings = [embedding.numpy().flatten() for embedding in token_embeddings[0]]
            chunk_embeddings.extend(flattened_embeddings) 

        # Print progress
        progress_percent = (i + 1) / total_seqs * 100
        print(f'Progress: {progress_percent:.2f}%', end='\r')

    chunk_reduced_embeddings = pca.fit_transform(chunk_embeddings)
    embedding_index=0

    for token_seq in token_seqs:
        for token in token_seq:
            token_to_vector[token] = chunk_reduced_embeddings[embedding_index].tolist()
            embedding_index += 1
    
    # Clear progress line
    print(' ' * 50, end='\r')

    time_stamp = math.floor(time.time() * 1000)
    token_to_vector_file_name = "token_to_vector_" + str(time_stamp) + ".json"
    print("Writing token-to-vector map to " + token_to_vector_file_name)
    with open(token_to_vector_file_name, "w") as file:
        json.dump(token_to_vector, file, sort_keys=True, indent=4)