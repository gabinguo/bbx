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

    for index, query in enumerate(tqdm(queries)):
        title_pool.add(query["title"])
        for paragraph in query["paragraphs"]:
            context = paragraph["context"]
            paragraph_pool.add(context)
            for qa in paragraph["qas"]:
                qa_count += 1
                qa_id = qa["id"]
                id_pool.add(qa_id)
                if "is_impossible" in qa:
                    if not qa["is_impossible"]:
                        for answer in qa["answers"]:
                            answer_count += 1
                            answer_start = answer["answer_start"]
                            answer_len = len(answer["text"])
                            answer_from_context = context[answer_start: answer_start+answer_len]
                            if answer_from_context == answer["text"]:
                                qa_check_count += 1
                            else:
                                qa_not_check_count += 1
                                not_check_pool.append(index)
                    if qa["is_impossible"]:
                        qa_not_answerable_count += 1
                else:
                    for answer in qa["answers"]:
                        answer_count += 1
                        answer_start = answer["answer_start"]
                        answer_len = len(answer["text"])
                        answer_from_context = context[answer_start: answer_start+answer_len]
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
    if not_check_pool:
        print(f"Failed indexes: {not_check_pool}")


def print_stats(stats):
    global console, table
    table.add_row(
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
    console.print(table)
    print("\n\n")





if __name__ == "__main__":
    console = Console()
    table = Table(show_header=True, title=f"[bold cyan]Statistics about the dataset (SQuAD-Like)[/bold cyan]")
    table.add_column("Total", style="cyan", no_wrap=True, justify="right")
    table.add_column("Has_repeat", style="yellow", no_wrap=True, justify="right")
    table.add_column("Unique_Article", style="cyan", no_wrap=True, justify="right")
    table.add_column("Unique_Paragraph", style="cyan", no_wrap=True, justify="right")
    table.add_column("Total_Answer", style="cyan", no_wrap=True, justify="right")
    table.add_column("Answerable", style="green", no_wrap=True, justify="right")
    table.add_column("Not_Answerable", style="red", no_wrap=True, justify="right")
    table.add_column("Passed", style="green", no_wrap=True, justify="right")
    table.add_column("Failed", style="red", no_wrap=True, justify="right")

    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--filename", type=str, help="filepath to the squad-like file")
    args_parser.add_argument("--field", type=str, default="data", help="filed to parser examples")
    args = args_parser.parse_args()

    queries = read_squad_file(args.filename, field=args.field)
    check_integrity(queries)





