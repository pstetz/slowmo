root=$1
dst_dir=$2

#tasks="101_fMRI_preproc_GO_NO_GO 102_fMRI_preproc_ODDBALL 103_fMRI_preproc_FACES-CONSCIOUS 104_fMRI_preproc_WORKING_MEMORY 105_fMRI_preproc_FACES-NONCONSCIOUS"
task="FSL_segmentation"
sessions="000_data_archive 001_data_archive"
#filename=wa01_normalized_func_data.nii
filename=w_greymatter_mask_thresh6.nii

for subject_path in $root/* ; do
    subject=$(basename $subject_path)
    for session in $sessions; do
        #for task in $tasks; do
            #task_dir=$subject_path/$session/100_fMRI/$task
        task_dir=$subject_path/$session/200_sMRI/003_FSL_fineFNIRT/$task
        if [ ! -d $task_dir ]; then
            continue
        fi
        num_matches=$(find $task_dir -maxdepth 1 -name $filename* | wc -l)
        if [ $num_matches -eq 0 ]; then
            echo $task_dir
            continue
        fi
        if [ $num_matches -gt 1 ]; then
            echo "Duplicates found in ${task_dir}"
            continue
        fi
        filepath=$(find $task_dir -maxdepth 1 -name $filename*)
        dst=$dst_dir/$session/$subject/$task/$(basename $filepath)
        if [ -f $dst ]; then
            continue
        fi
        if [ ! -d $(dirname $dst) ]; then
            mkdir -p $(dirname $dst)
        fi
        echo $filepath
        cp $filepath $dst
        #done
    done
done
