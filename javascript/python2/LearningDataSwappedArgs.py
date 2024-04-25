import Util
from collections import Counter

from HyperParameters import name_embedding_size, type_embedding_size
from tensorflow.keras.preprocessing.sequence import pad_sequences


class CodePiece(object):
    def __init__(self, callee, arguments, src):
        self.callee = callee
        self.arguments = arguments
        self.src = src

    def to_message(self):
        return str(self.src) + " | " + str(self.callee) + " | " + str(self.arguments)


class LearningData(object):
    def is_known_type(self, t):
        return t == "boolean" or t == "number" or t == "object" or t == "regex" or t == "string"

    def resetStats(self):
        self.stats = {"calls": 0, "calls_with_two_args": 0, "calls_with_known_names": 0,
                      "calls_with_known_base_object": 0, "calls_with_known_types": 0,
                      "calls_with_both_known_types": 0,
                      "calls_with_known_parameters": 0}

    def pre_scan(self, first_data_paths, second_data_paths=[]):
        print("Stats on first data")
        self.gather_stats(first_data_paths)

        if second_data_paths != []:
            print("Stats on second data")
            self.gather_stats(second_data_paths)

    def gather_stats(self, data_paths):
        callee_to_freq = Counter()
        argument_to_freq = Counter()

        for call in Util.DataReader(data_paths):
            callee_to_freq[call["callee"]] += 1
            for argument in call["arguments"]:
                argument_to_freq[argument] += 1

        print("Unique callees        : " + str(len(callee_to_freq)))
        print("  " + "\n  ".join(str(x)
                                 for x in callee_to_freq.most_common(10)))
        Util.analyze_histograms(callee_to_freq)
        print("Unique arguments      : " + str(len(argument_to_freq)))
        print("  " + "\n  ".join(str(x)
                                 for x in argument_to_freq.most_common(10)))
        Util.analyze_histograms(argument_to_freq)

    def code_to_xy_pairs(self, gen_negatives, call, xs, ys, name_to_vector, type_to_vector, node_type_to_vector, calls=None):
        arguments = call["arguments"]
        self.stats["calls"] += 1
        if len(arguments) != 2:
            return
        self.stats["calls_with_two_args"] += 1

        # mandatory information: callee and argument names
        callee_string = call["callee"]
        argument_strings = call["arguments"]
        if not (callee_string in name_to_vector):
            return
        for argument_string in argument_strings:
            if not (argument_string in name_to_vector):
                return
        self.stats["calls_with_known_names"] += 1
        callee_vector = name_to_vector[callee_string]
        argument0_vector = name_to_vector[argument_strings[0]]
        argument1_vector = name_to_vector[argument_strings[1]]

        # optional information: base object, argument types, etc.
        base_string = call["base"]
        base_vector = name_to_vector.get(base_string, [0]*name_embedding_size)
        if base_string in name_to_vector:
            self.stats["calls_with_known_base_object"] += 1

        argument_type_strings = call["argumentTypes"]
        argument0_type_vector = type_to_vector.get(
            argument_type_strings[0], [0]*type_embedding_size)
        argument1_type_vector = type_to_vector.get(
            argument_type_strings[1], [0]*type_embedding_size)
        if (self.is_known_type(argument_type_strings[0]) or self.is_known_type(argument_type_strings[1])):
            self.stats["calls_with_known_types"] += 1
        if (self.is_known_type(argument_type_strings[0]) and self.is_known_type(argument_type_strings[1])):
            self.stats["calls_with_both_known_types"] += 1

        parameter_strings = call["parameters"]
        parameter0_vector = name_to_vector.get(
            parameter_strings[0], [0]*name_embedding_size)
        parameter1_vector = name_to_vector.get(
            parameter_strings[1], [0]*name_embedding_size)
        if (parameter_strings[0] in name_to_vector or parameter_strings[1] in name_to_vector):
            self.stats["calls_with_known_parameters"] += 1

        # for all xy-pairs: y value = probability that incorrect
        argument0_type_vector = [argument0_type_vector]
        argument0_type_vector = pad_sequences(argument0_type_vector, maxlen=200, padding='post')
        argument0_type_vector = argument0_type_vector[0]
        argument1_type_vector = [argument1_type_vector]
        argument1_type_vector = pad_sequences(argument1_type_vector, maxlen=200, padding='post')
        argument1_type_vector = argument1_type_vector[0]
        x_keep = []
        x_keep.append(callee_vector)
        x_keep.append(argument0_vector)
        x_keep.append(argument1_vector)
        x_keep.append(base_vector)
        x_keep.append(argument0_type_vector)
        x_keep.append(argument1_type_vector)
        x_keep.append(parameter0_vector)
        x_keep.append(parameter1_vector)
        #print(str(len(callee_vector))+" "+str(len(argument0_vector))+" "+str(len(argument1_vector))+" "+str(len(base_vector))+" "+ str(len(argument0_type_vector))+" "+ str(len(argument1_type_vector))+" "+str(len(parameter0_vector))+" "+str(len(parameter1_vector)))
        y_keep = [0]
        xs.append(x_keep)
        ys.append(y_keep)
        if calls != None:
            calls.append(
                CodePiece(callee_string, argument_strings, call["src"]))

        # generate negatives
        if gen_negatives:
            x_swap = []
            x_swap.append(callee_vector)
            x_swap.append(argument1_vector)
            x_swap.append(argument0_vector)
            x_swap.append(base_vector)
            x_swap.append(argument1_type_vector)
            x_swap.append(argument0_type_vector)
            x_swap.append(parameter0_vector)
            x_swap.append(parameter1_vector)
            y_swap = [1]
            xs.append(x_swap)
            ys.append(y_swap)
            if calls != None:
                calls.append(
                    CodePiece(callee_string, argument_strings, call["src"]))

    def anomaly_score(self, y_prediction_orig, y_prediction_changed):
        # higher means more likely to be anomaly in current code
        return y_prediction_orig - y_prediction_changed

    def normal_score(self, y_prediction_orig, y_prediction_changed):
        # higher means more likely to be correct in current code
        return y_prediction_changed - y_prediction_orig
