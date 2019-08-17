def main(masks_dir, masks_path):
    with open(masks_path) as f:
        mask_names = f.readlines()
        mask_names = [m[:-1] for m in mask_names] # remove \n character
    masks = [os.path.join(masks_dir, m + ".nii") for m in mask_names]
    return masks
