#!/bin/sh
# untar all .nii.tar.gz files and
# renames them to fit current format

cwd=$(pwd)

# Input
ROOT=$1

# Settings
time_sessions="000 2MO 6MO 12MO 24MO"
tasks="gonogo conscious nonconscious"
# Main loop
for time_session in $time_sessions ; do
    echo $time_session
    for subject_path in $ROOT/$time_session/* ; do
        subject=$(basename "$subject_path")
        for task in $tasks; do
            targz=$subject_path/$task/*.nii.tar.gz # FIXME
            if [ ! ${#targz[@]} -eq 1 ]; then
                echo "Multiple or no files found for $task"
            elif [ -e ${targz[0]} ]; then
                old_name=${targz[0]}
                echo "untarring ${old_name}"
                cd $subject_path/$task
                tar -xvzf $old_name
                rm $old_name
                mv wa01_normalized_func_data.nii warped.nii
                gzip warped.nii
            else
                echo "Found no files for $time_session $subject $task"
            fi
        done
    done
done

cd $cwd
