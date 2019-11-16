from log_parser import log_parser
from txt_parser import txt_parser

def parser(filepath, outdir, task):
    if filepath.endswith(".txt"):
        txt_parser(filepath, outdir, task)
    elif filepath.endswith(".log"):
        log_parser(filepath, outdir, task)
    else:
        raise Exception("Unsure how to parse %s" % filepath)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    log_filepath = args[0]
    output_directory = args[1]
    task = args[2]
    parser(log_filepath, output_directory, task)

