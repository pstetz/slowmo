def fsl_command(command, *args):
    """ Runs an FSL command and returns the response """
    import os
    from subprocess import check_output

    fsldir = os.environ["FSLDIR"]
    command = ["%s/bin/%s" % (fsldir, command)]
    command.extend(args)
    return check_output( command )

if __name__ == "__main__":
    import sys
    command = argv[1]
    args = sys.argv[2:]
    fsl_command(command, args)
