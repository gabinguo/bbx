import json
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
import argparse

def read_squad_file(filepath):
    """
        Get the data field of squad-like file
    """
    with open(filepath, 'r') as f:
        queries = json.load(f)["data"]
    return queries

def check_integrity(queries):
    qa_count = 0
    qa_check_count = 0
    qa_not_check_count = 0
    qa_not_answerable_count = 0
    answer_count = 0
    
    for query in tqdm(queries):
        for paragraph in query["paragraphs"]:
            context = paragraph["context"]
            for qa in paragraph["qas"]:
                qa_count += 1
                qa_id = qa["id"]
                question = qa["question"]
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
                    if qa["is_impossible"]:
                        qa_not_answerable_count += 1
                else:
                    for answer in qa["answers"]:
                        answer_count += 1
                        answer_start = answer["answer_start"]
                        answer_len = len(answer["text"])
                        answer_from_context = context[answer_start: answer_start+answer_len+1]
                        if answer_from_context == answer["text"]:
                            qa_check_count += 1
                        else:
                            qa_not_check_count += 1
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
        "qa_not_answerable_count": qa_not_answerable_count
    }
    print_stats(stats)
    

def print_stats(stats):
    global console, table
    table.add_row(
        f"{stats['qa_count']}",
        f"{stats['answer_count']}",
        f"{stats['qa_check_count']}",
        f"{stats['qa_not_check_count']}",
        f"{stats['qa_count'] - stats['qa_not_answerable_count']}",
        f"{stats['qa_not_answerable_count']}"
    )
    
    print("\n\n")
    console.print(table)
    print("\n\n")
                            
                
                        
                    

if __name__ == "__main__":
    console = Console()
    table = Table(show_header=True, title=f"[bold cyan]Statistics about the dataset (SQuAD-Like)[/bold cyan]")
    table.add_column("Total", style="cyan", no_wrap=True, justify="right")
    table.add_column("Total_Answer", style="cyan", no_wrap=True, justify="right")
    table.add_column("Passed", style="green", no_wrap=True, justify="right")
    table.add_column("Failed", style="red", no_wrap=True, justify="right")
    table.add_column("Answerable", style="green", no_wrap=True, justify="right")
    table.add_column("Not_Answerable", style="red", no_wrap=True, justify="right")
    
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--filename", type=str, help="filepath to the squad-like file")
    args = args_parser.parse_args()
    
    queries = read_squad_file(args.filename)
    check_integrity(queries)
    
    
    
    
    