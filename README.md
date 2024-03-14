Research Paper:http://software-lab.org/publications/oopsla2018_DeepBugs.pdf

## Dependencies

To train the model, the following dependencies are required:

### System Dependencies
- Node.js
- npm modules: acorn, estraverse, walk-sync
- Python 3.9.18

### Python Packages
- keras 2.12.0
- numpy 1.23.5
- sklearn 1.3.0
- scipy 1.11.4
- tensorflow 2.12.0
- gensim 4.3.0Dependencies required in the system to train the model:
-----------------------------------------------
Dependencies to install to train the model:
Node.js
npm modules : acorn, estraverse, walk-sync
Python 3.9.18

Python Packages :
keras 2.12.0
numpy 1.23.5
sklearn - 1.3.0
scipy 1.11.4
tensorflow  2.12.0
gensim  4.3.0


## Creating Embeddings for Identifiers

The bug detectors rely on a vector representation for identifier names and literals, which is stored in `token_to_vector.json` file. It is generated as follows.

1) `node javascript/extractFromJS.js tokens --parallel 4 data/js/programs_50_training.txt data/js/programs_50`

  * The command produces `tokens_*.json` files.
  
2) `python3 python/TokensToTopTokens.py tokens_*.json`
  
  * The command produces `encoded_tokens_*.json` files and a file `token_to_number_*.json` that assigns a number to each identifier and literal.

3) `python3 python/EmbeddingLearnerWord2Vec.py token_to_number_*.json encoded_tokens_*.json`

  * The command produces the file `token_to_vector_*.json`.

## Training the model

#### Step 1: Extract positive and negative training examples
`node javascript/extractFromJS.js calls --parallel 4 data/js/programs_50_training.txt data/js/programs_50`
  * `programs_50_training.txt` contains files to include (one file per line).
  * The last argument is a directory that gets recursively scanned for .js files.
  * The command produces `calls_*.json` files, which is data suitable for the `SwappedArgs` bug detector. For the other bug two detectors, replace `calls` with `binOps` in the above command.

#### Step 2: Train a classifier to identify bugs
`python3 python/BugLearn.py --pattern SwappedArgs --token_emb token_to_vector.json --type_emb type_to_vector.json --node_emb node_type_to_vector.json --training_data calls_xx*.json`
* The first argument selects the bug pattern.
* The next three arguments are vector representations for tokens (here: identifiers and literals), for types, and for AST node types. These files are provided in the repository.
* The remaining arguments are two lists of .json files. They contain the training and validation data extracted in Step 1.


## Testing the model
`node javascript/extractFromJS.js calls --files <list of files>`
* Creates the calls_xx* file for testing dataset
`python3 python/BugFind.py --pattern SwappedArgs --threshold 0.95 --model some/dir --token_emb token_to_vector.json --type_emb type_to_vector.json --node_emb node_type_to_vector.json --testing_data calls_xx*.json`
* replace `some/dir` with model directory and pass generated calls_xx* in the arguments ...replace treshold if required 
* This predicts the bug in the specific file and gives the probability that the given function call is buggy or not


