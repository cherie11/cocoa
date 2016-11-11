'''
Takes two agent implementations and generates the dialogues.
'''

import argparse
import random
import json
from src.basic.util import read_json
from src.basic.schema import Schema
from src.basic.scenario_db import ScenarioDB, add_scenario_arguments
from src.basic.dataset import add_dataset_arguments
from src.basic.systems.heuristic_system import HeuristicSystem
from src.basic.systems.simple_system import SimpleSystem
from src.basic.systems.neural_system import NeuralSystem
from src.basic.controller import Controller
from src.basic.lexicon import Lexicon

parser = argparse.ArgumentParser()
parser.add_argument('--random-seed', help='Random seed', type=int, default=1)
parser.add_argument('--agents', help='What kind of agent to use {heuristic}', nargs='*')
parser.add_argument('--model-path', help='Path to model (used for neural agents)')
parser.add_argument('--scenario-offset', default=0, type=int, help='Number of scenarios to skip at the beginning')
add_scenario_arguments(parser)
add_dataset_arguments(parser)
args = parser.parse_args()
if args.random_seed:
    random.seed(args.random_seed)

schema = Schema(args.schema_path)
scenario_db = ScenarioDB.from_dict(schema, read_json(args.scenarios_path))
lexicon = Lexicon(schema, learned_lex=False)

def get_system(name):
    if name == 'simple':
        return SimpleSystem()
    elif name == 'heuristic':
        return HeuristicSystem()
    elif name == 'neural':
        assert args.model_path
        return NeuralSystem(schema, lexicon, args.model_path)
    else:
        raise ValueError('Unknown system %s' % name)

if not args.agents:
    args.agents = ['simple', 'simple']
agents = [get_system(name) for name in args.agents]
num_examples = args.scenario_offset

def generate_examples(description, examples_path, max_examples):
    global num_examples
    examples = []
    for i in range(max_examples):
        scenario = scenario_db.scenarios_list[num_examples % len(scenario_db.scenarios_list)]
        sessions = [agents[0].new_session(0, scenario.kbs[0]), agents[1].new_session(1, scenario.kbs[1])]
        controller = Controller(scenario, sessions)
        ex = controller.simulate()
        examples.append(ex)
        num_examples += 1
    with open(examples_path, 'w') as out:
        print >>out, json.dumps([e.to_dict() for e in examples])

if args.train_max_examples:
    generate_examples('train', args.train_examples_paths[0], args.train_max_examples)
if args.test_max_examples:
    generate_examples('test', args.test_examples_paths[0], args.test_max_examples)