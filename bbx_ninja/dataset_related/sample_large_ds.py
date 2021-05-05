import json
import random
import argparse

random.seed = 42


def read_filename(filename=""):
    with open(filename, 'r') as f:
        queries = json.load(f)["data"]
    return queries


def sample_from_large_dataset(queries, count=2000):
    sample_size = min(len(queries[:count]), count)
    return random.sample(queries, count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, help="Path to the filename to sample.")
    parser.add_argument("--output_filename", type=str, default="sampled_ds.json",
                        help="Path to output sampled dataset.")
    args = parser.parse_args()

    queries = read_filename(args.filename)
    sampled_queries = sample_from_large_dataset(queries, 2000)

    with open(f"./{output_filename}", 'w') as f:
        json.dump({"version": "sampled_dataset", "data": sampled_queries}, f)
