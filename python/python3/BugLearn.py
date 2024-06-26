import sys
import os
import json
from os.path import join
from os import getcwd
from collections import namedtuple
import math
from keras.models import Sequential
from keras_self_attention import SeqSelfAttention
from keras.layers import Input, Conv1D, MaxPooling1D, Flatten, GRU,LSTM, Dense, Dropout, concatenate
from keras.models import Model
from tensorflow.keras.layers import GRU, Conv1D, MaxPooling1D, Dense, Dropout, Flatten
import time
import numpy as np

import time
import numpy as np
import Util
import LearningDataSwappedArgs
import LearningDataBinOperator
import LearningDataSwappedBinOperands
import LearningDataIncorrectBinaryOperand
import LearningDataIncorrectAssignment
import argparse


parser = argparse.ArgumentParser()
parser.add_argument(
    "--pattern", help="Kind of data to extract", choices=["SwappedArgs", "BinOperator", "SwappedBinOperands", "IncorrectBinaryOperand", "IncorrectAssignment"], required=True)
parser.add_argument(
    "--token_emb", help="JSON file with token embeddings", required=True)
parser.add_argument(
    "--type_emb", help="JSON file with type embeddings", required=True)
parser.add_argument(
    "--node_emb", help="JSON file with AST node embeddings", required=True)
parser.add_argument(
    "--training_data", help="JSON files with training data", required=True, nargs="+")
parser.add_argument(
    "--out", help="Target directory for trained model")


Anomaly = namedtuple("Anomaly", ["message", "score"])


def prepare_xy_pairs(gen_negatives, data_paths, learning_data):
    xs = []
    ys = []
    # keep calls in addition to encoding as x,y pairs (to report detected anomalies)
    code_pieces = []

    for code_piece in Util.DataReader(data_paths):
        learning_data.code_to_xy_pairs(gen_negatives, code_piece, xs, ys,
                                       name_to_vector, type_to_vector, node_type_to_vector, code_pieces)
    # x_length = len(xs[0])

    # print("Stats: " + str(learning_data.stats))
    # print("Number of x,y pairs: " + str(len(xs)))
    # print("Length of x vectors: " + str(x_length))
    xs = np.array(xs)
    ys = np.array(ys)
    return [xs, ys, code_pieces]


def sample_xy_pairs(xs, ys, number_buggy):
    sampled_xs = []
    sampled_ys = []
    buggy_indices = []
    for i, y in enumerate(ys):
        if y == [1]:
            buggy_indices.append(i)
    sampled_buggy_indices = set(np.random.choice(
        buggy_indices, size=number_buggy, replace=False))
    for i, x in enumerate(xs):
        y = ys[i]
        if y == [0] or i in sampled_buggy_indices:
            sampled_xs.append(x)
            sampled_ys.append(y)
    return sampled_xs, sampled_ys


if __name__ == '__main__':
    print("BugLearn started with " + str(sys.argv))
    time_start = time.time()

    args = parser.parse_args()
    pattern = args.pattern
    name_to_vector_file = args.token_emb
    type_to_vector_file = args.type_emb
    node_type_to_vector_file = args.node_emb
    training_data_paths = args.training_data
    out_dir = args.out
    if out_dir is None:
        time_stamp = math.floor(time.time() * 1000)
        out_dir = "bug_detection_model_" + str(time_stamp)

    with open(name_to_vector_file) as f:
        name_to_vector = json.load(f)
    with open(type_to_vector_file) as f:
        type_to_vector = json.load(f)
    with open(node_type_to_vector_file) as f:
        node_type_to_vector = json.load(f)

    if pattern == "SwappedArgs":
        learning_data = LearningDataSwappedArgs.LearningData()
    elif pattern == "BinOperator":
        learning_data = LearningDataBinOperator.LearningData()
    elif pattern == "SwappedBinOperands":
        learning_data = LearningDataSwappedBinOperands.LearningData()
    elif pattern == "IncorrectBinaryOperand":
        learning_data = LearningDataIncorrectBinaryOperand.LearningData()
    elif pattern == "IncorrectAssignment":
        learning_data = LearningDataIncorrectAssignment.LearningData()
    else:
        raise Exception(f"Unexpected pattern: {pattern}")
    # elif pattern == "MissingArg":
    ##    learning_data = LearningDataMissingArg.LearningData()
    # not yet implemented

    print("Statistics on training data:")
    learning_data.pre_scan(training_data_paths, [])

    # prepare x,y pairs for learning without negative examples
    print("Preparing xy pairs for training data:")
    learning_data.resetStats()
    xs_training, ys_training, _ = prepare_xy_pairs(
        True, training_data_paths, learning_data)
    # x_length = len(xs_training[0])
    # print("Training examples   : " + str(len(xs_training)))
    print(learning_data.stats)

    input_length = len(xs_training[0])
    input_dim = len(xs_training[0][0])
    # conv_input = Input(shape=(input_length, input_dim))
    basic_input = Input(shape=(input_length, input_dim))
    # Convolutional Layer
    conv_output = Conv1D(128, 5, activation='relu',padding='same')(basic_input)
    # pool_output = MaxPooling1D(pool_size=2)(conv_output)
    flatten_output = Flatten()(conv_output)
    # GRU layer
    rnn_output = LSTM(200, return_sequences=False)(basic_input)
    # Concatenate Convolutional and GRU outputs
    concatenated_output = concatenate([flatten_output, rnn_output])
    # Dense layer for compression
    dense_output = Dense(200, activation="relu")(concatenated_output)
    dropout_output = Dropout(0.2)(dense_output)
    # Output layer
    final_output = Dense(1, activation="sigmoid")(dropout_output)
    model = Model(inputs=basic_input, outputs=final_output)
    model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
    history = model.fit(xs_training, ys_training, batch_size=100, epochs=10, verbose=1)
    model.save(out_dir)

    time_learning_done = time.time()
    print("Time for learning (seconds): " +
          str(round(time_learning_done - time_start)))

    print(f"Bug detection model saved to {out_dir}")