import Util
from collections import namedtuple
import random

from HyperParameters import name_embedding_size, type_embedding_size
from tensorflow.keras.preprocessing.sequence import pad_sequences


# assumption: even number and <= identifierContextWindowSize in JS data extractor
nb_context_ids = 6


class CodePiece(object):
    def __init__(self, lhs, rhs, src):
        self.lhs = lhs
        self.rhs = rhs
        self.src = src

    def to_message(self):
        return str(self.src) + " | " + str(self.lhs) + " | " + str(self.rhs)


RHS = namedtuple('Assignment', ['rhs', 'type'])


class LearningData(object):
    def __init__(self):
        self.file_to_RHSs = dict()  # string to set of RHSs
        self.stats = {}

    def resetStats(self):
        self.stats = {}

    def pre_scan(self, training_data_paths, validation_data_paths=[]):
        for assignment in Util.DataReader(training_data_paths):
            file = assignment["src"].split(" : ")[0]
            rhsides = self.file_to_RHSs.setdefault(file, set())
            rhsides.add(RHS(assignment["rhs"], assignment["rhsType"]))

        for assignment in Util.DataReader(validation_data_paths):
            file = assignment["src"].split(" : ")[0]
            rhsides = self.file_to_RHSs.setdefault(file, set())
            rhsides.add(RHS(assignment["rhs"], assignment["rhsType"]))

    def select_context_ids(self, lhs, rhs, context):
        middle_idx = int(len(context) / 2)
        # search in pre-context for unseen identifiers, starting from the end
        pre_context = []
        for identifier in context[0:middle_idx][::-1]:
            if len(pre_context) >= nb_context_ids/2:
                break
            if (not (identifier in pre_context)) and identifier != lhs and identifier != rhs:
                pre_context.append(identifier)
        post_context = []
        # search in post-context for unseen identifiers, starting from the beginning
        for identifier in context[middle_idx:]:
            if len(post_context) >= nb_context_ids/2:
                break
            if (not (identifier in post_context)) and identifier != lhs and identifier != rhs:
                post_context.append(identifier)
        # construct list of all unique context ids (for negative example)
        all_context = []
        for identifier in context:
            if (not (identifier in all_context)) and identifier != lhs and identifier != rhs:
                all_context.append(identifier)
        return (pre_context, post_context, all_context)

    def pad_with_default(self, vector, target_len, default):
        while len(vector) < target_len:
            vector.append(default)

    def context_ids_to_embeddings(self, pre_context, post_context, name_to_vector):
        context_vector = []
        for context_id in pre_context:
            if context_id in name_to_vector:
                context_vector += name_to_vector[context_id]
            else:
                context_vector += [0]*name_embedding_size
        self.pad_with_default(
            context_vector, (nb_context_ids/2) * name_embedding_size, 0)
        for context_id in post_context:
            if context_id in name_to_vector:
                context_vector += name_to_vector[context_id]
            else:
                context_vector += [0]*name_embedding_size
        self.pad_with_default(
            context_vector, nb_context_ids * name_embedding_size, 0)
        return context_vector

    def code_to_xy_pairs(self, gen_negatives, assignment, xs, ys, name_to_vector, type_to_vector, node_type_to_vector, code_pieces):
        lhs = assignment["lhs"]
        rhs = assignment["rhs"]
        rhs_type = assignment["rhsType"]
        parent = assignment["parent"]
        grand_parent = assignment["grandParent"]
        context = assignment["context"]
        src = assignment["src"]
        if not (lhs in name_to_vector):
            return
        if not (rhs in name_to_vector):
            return

        lhs_vector = name_to_vector[lhs]
        rhs_vector = name_to_vector[rhs]
        rhs_type_vector = [type_to_vector.get(rhs_type, [0]*type_embedding_size)]
        rhs_type_vector = pad_sequences(rhs_type_vector, maxlen=200, padding='post')

        parent_vector = [node_type_to_vector[parent]]
        parent_vector = pad_sequences(parent_vector,maxlen=200,padding='post')

        grand_parent_vector = [node_type_to_vector[grand_parent]]
        grand_parent_vector = pad_sequences(grand_parent_vector, maxlen=200, padding='post')

        # transform context into embedding vectors (0 if not available)
        (pre_context, post_context, all_context) = self.select_context_ids(
            lhs, rhs, context)
        context_vector = [self.context_ids_to_embeddings(
            pre_context, post_context, name_to_vector)]
        context_vector = pad_sequences(context_vector, maxlen=200, padding='post')

        # for all xy-pairs: y value = probability that incorrect
        #x_correct = lhs_vector + rhs_vector + rhs_type_vector + \
        #    parent_vector + grand_parent_vector + context_vector
        x_correct=[]
        x_correct.append(lhs_vector)
        x_correct.append(rhs_vector)
        x_correct.append(rhs_type_vector[0])
        # x_correct.append(parent_vector[0])
        # x_correct.append(grand_parent_vector[0])
        # x_correct.append(context_vector[0])
        y_correct = [0]
        xs.append(x_correct)
        ys.append(y_correct)
        code_pieces.append(CodePiece(lhs, rhs, src))

        # pick an alternative rhs from the context ids
        if gen_negatives:
            if len(all_context) == 0:
                return
            tries_left = 100
            found = False
            other_rhs = None
            while (not found) and tries_left > 0:
                other_rhs = random.choice(all_context)
                if other_rhs in name_to_vector:
                    found = True
                tries_left -= 1
            if not found:
                return
            other_rhs_vector = name_to_vector[other_rhs]
            other_rhs_type_vector = [type_to_vector["unknown"]]
            other_rhs_type_vector = pad_sequences(other_rhs_type_vector, maxlen=200, padding='post')

            #x_incorrect = lhs_vector + other_rhs_vector + other_rhs_type_vector + \
            #    parent_vector + grand_parent_vector + context_vector
            
            x_incorrect=[]
            x_incorrect.append(lhs_vector)
            x_incorrect.append(other_rhs_vector)
            x_incorrect.append(other_rhs_type_vector[0])
            # x_incorrect.append(parent_vector[0])
            # x_incorrect.append(grand_parent_vector[0])
            # x_correct.append(context_vector[0])
            y_incorrect = [1]
            xs.append(x_incorrect)
            ys.append(y_incorrect)
            code_pieces.append(CodePiece(lhs, rhs, src))

    def anomaly_score(self, y_prediction_orig, y_prediction_changed):
        return y_prediction_orig

    def normal_score(self, y_prediction_orig, y_prediction_changed):
        return y_prediction_changed
