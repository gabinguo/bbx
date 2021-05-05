import json
from tqdm import tqdm

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Can't find module rich, try using `pip install rich`")
import argparse


def read_squad_file(filepath, field="data"):
    """
        Get the data field of squad-like file
    """
    with open(filepath, 'r') as f:
        queries = json.load(f)[field]
    return queries


def check_integrity(queries):
    qa_count = 0
    qa_check_count = 0
    qa_not_check_count = 0
    qa_not_answerable_count = 0
    answer_count = 0
    not_check_pool = []
    paragraph_pool = set()
    id_pool = set()
    title_pool = set()

    answer_pool = []
    question_pool = []

    for index, query in enumerate(tqdm(queries)):
        title_pool.add(query["title"])
        for paragraph in query["paragraphs"]:
            context = paragraph["context"]
            paragraph_pool.add(context)
            for qa in paragraph["qas"]:
                qa_count += 1
                qa_id = qa["id"]
                id_pool.add(qa_id)
                question_pool.append(qa["question"])
                if "is_impossible" in qa:
                    if not qa["is_impossible"]:
                        for answer in qa["answers"]:
                            answer_pool.append(answer["text"])
                            answer_count += 1
                            answer_start = answer["answer_start"]
                            answer_len = len(answer["text"])
                            answer_from_context = context[answer_start: answer_start + answer_len]
                            if answer_from_context == answer["text"]:
                                qa_check_count += 1
                            else:
                                qa_not_check_count += 1
                                not_check_pool.append(index)
                    if qa["is_impossible"]:
                        qa_not_answerable_count += 1
                else:
                    for answer in qa["answers"]:
                        answer_pool.append(answer["text"])
                        answer_count += 1
                        answer_start = answer["answer_start"]
                        answer_len = len(answer["text"])
                        answer_from_context = context[answer_start: answer_start + answer_len]
                        if answer_from_context == answer["text"]:
                            qa_check_count += 1
                        else:
                            qa_not_check_count += 1
                            not_check_pool.append(index)
    try:
        assert qa_count == (qa_check_count + qa_not_check_count + qa_not_answerable_count)
    except AssertionError:
        print("Error Assertion: qa_count == (qa_check_count + qa_not_check_count + qa_not_answerable_count)")
        print(f"Possible reason: qa_count equals to {qa_count}, whilst answer_count equals to {answer_count}")

    stats = {
        "qa_count": qa_count,
        "answer_count": answer_count,
        "qa_check_count": qa_check_count,
        "qa_not_check_count": qa_not_check_count,
        "qa_not_answerable_count": qa_not_answerable_count,
        "paragraph_count": len(paragraph_pool),
        "unique_id_count": len(id_pool),
        "unique_article": len(title_pool)
    }
    print_stats(stats)
    for pool, info_type in zip([answer_pool, question_pool, paragraph_pool], ["Answer", "Question", "Passage"]):
        stats = {
            "avg_char_length": round(sum(map(len, pool)) / len(pool), 2),
            "avg_word_length": round(sum(map(len, [p.split() for p in pool])) / len(pool), 2),
            "min_char_length": len(min(pool, key=len)),
            "min_word_length": len(min([p.split() for p in pool], key=len)),
            "max_char_length": len(max(pool, key=len)),
            "max_word_length": len(max([p.split() for p in pool], key=len)),
        }
        print_more_stats(stats, info_type=info_type)
        if info_type != "Passage":
            print(f"min-char-length {info_type}: \n{min(pool, key=len)}")
            print(f"min-word-length {info_type}: \n{min([p.split() for p in pool], key=len)}")

    if not_check_pool:
        print(f"Failed indexes: {not_check_pool}")


def print_stats(stats):
    console = Console()
    table_ds_info = Table(show_header=True, title=f"[bold cyan]Statistics about the dataset (SQuAD-Like)[/bold cyan]")
    table_ds_info.add_column("Total", style="cyan", no_wrap=True, justify="right")
    table_ds_info.add_column("Has_repeat", style="yellow", no_wrap=True, justify="right")
    table_ds_info.add_column("Unique_Article", style="cyan", no_wrap=True, justify="right")
    table_ds_info.add_column("Unique_Paragraph", style="cyan", no_wrap=True, justify="right")
    table_ds_info.add_column("Total_Answer", style="cyan", no_wrap=True, justify="right")
    table_ds_info.add_column("Answerable", style="green", no_wrap=True, justify="right")
    table_ds_info.add_column("Not_Answerable", style="red", no_wrap=True, justify="right")
    table_ds_info.add_column("Passed", style="green", no_wrap=True, justify="right")
    table_ds_info.add_column("Failed", style="red", no_wrap=True, justify="right")
    table_ds_info.add_row(
        f"{stats['qa_count']}",
        f"{'No' if stats['unique_id_count'] == stats['qa_count'] else 'Yes'}",
        f"{stats['unique_article']}",
        f"{stats['paragraph_count']}",
        f"{stats['answer_count']}",
        f"{stats['qa_count'] - stats['qa_not_answerable_count']}",
        f"{stats['qa_not_answerable_count']}",
        f"{stats['qa_check_count']}",
        f"{stats['qa_not_check_count']}"
    )
    print("\n\n")
    console.print(table_ds_info)
    print("\n\n")


def print_more_stats(stats, info_type="Answer"):
    console = Console()
    table_more_info = Table(show_header=True, title=f"[bold cyan]Statistics about the {info_type}[/bold cyan]")
    table_more_info.add_column("Avg_char_length", style="cyan", no_wrap=True, justify="right")
    table_more_info.add_column("Avg_word_length", style="cyan", no_wrap=True, justify="right")
    table_more_info.add_column("Min_char_length", style="cyan", no_wrap=True, justify="right")
    table_more_info.add_column("Min_word_length", style="cyan", no_wrap=True, justify="right")
    table_more_info.add_column("Max_char_length", style="cyan", no_wrap=True, justify="right")
    table_more_info.add_column("Max_word_length", style="cyan", no_wrap=True, justify="right")
    table_more_info.add_row(
        f"{stats['avg_char_length']}",
        f"{stats['avg_word_length']}",
        f"{stats['min_char_length']}",
        f"{stats['min_word_length']}",
        f"{stats['max_char_length']}",
        f"{stats['max_word_length']}"
    )
    print("\n\n")
    console.print(table_more_info)
    print("\n\n")


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--filename", type=str, help="filepath to the squad-like file")
    args_parser.add_argument("--field", type=str, default="data", help="filed to parser examples")
    args = args_parser.parse_args()

    queries = read_squad_file(args.filename, field=args.field)
    check_integrity(queries)
