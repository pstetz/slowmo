# MRI SlowMo

author: Patrick Stetz [(gihub)](https://github.com/pstetz)


### Motivation

One problem in MRI imagining is the low resolution temporal resolution of imaging.  There is a physical limit in MRI imaging that snapshots of one layer can only be taken every few seconds.  In addition, it is difficult if not immpossible to have snapshots of different layers of the brain taken at the same time.

This project attempts to alleviate both of these issues by making use of advances in Deep Learning technology.  A team from NVIDIA has created a model that can create high quality slow motion videos from regular videos.  The problems faced here are essentially the same.  We want to create regular videos from extremely choppy snapshots.

### Introduction
In the original SlowMo [paper presented here](https://people.cs.umass.edu/~hzjiang//projects/superslomo/) [and here](https://arxiv.org/abs/1712.00080), the team trained on 1,132 Youtube videos or 300K individual frames.

While this sounds like a lot we have just as much.  CONNECTOME, ENGAGE, and RAD have a combined ~1,500 sessions on Flywheel and a estimate of 3 tasks per session and 150 volumes per task mean we have 675,000 individual frames


### Classes

There are 4 classes that are helpful to abstract away a lot of details

- Button.  Gathers all relevant button logs and can filter from there.
- Cloud.   Pulls data from flywheel
- (unused) Dicom.   This is helpful, so I don't need to remember pydicom details.  Also it will load all dicoms and gather relevant information by specifying a dicom directory
- (unused) Model.   Helps load and save the model.  This is useful because this will run over several weeks maybe and I want to checkpoint progress


### Todo

- Get more comfortable with either tensorflow or pytorch
- Make the nifti movies more stylistic (add flashes when updating, work on colors, 3 dimensional, structural image in background)
- Collect all demographic information that should go in model
- Filter out subjects by movement
- Create a mask list (perhaps multiple options)
  - I'm thinking panlabs mask list and a probability mask (z scores for amygdala for instance)
- Search Flywheel or dicoms and gather all information on task
  - slice order, operator, date, time, etc (get more than I plan to use)
- Gather the movement for all tasks in the same CSV
- Account for subjects that use average onsets

### Done
- Decide if modeling on dicoms is better or if processed images would work
  - Nifti are better I think although ones that are not slice time corrected might be better.

### Notes
- Feather does support float 16
- Going from float64 to float32 had a memory saving from 1.18 GB to 593.6 MB

### Acknowledgements

The team whose paper heavily inspired me and their [paper](https://people.cs.umass.edu/~hzjiang//projects/superslomo/).

Helpful tensorflow links:  
- [Learning regression](https://www.tensorflow.org/tutorials/keras/basic_regression)  
-

Huaizu Jiang, Deqing Sun, Varun Jampani, Ming-Hsuan Yang, Erik Learned-Miller, Jan Kautz. Super SloMo: High Quality Estimation of Multiple Intermediate Frames for Video Interpolation. CVPR, 2018 (spotlight). [[PDF](https://arxiv.org/pdf/1712.00080.pdf)][[CVPR spotlight video](https://people.cs.umass.edu/~hzjiang//projects/superslomo/superslomo_cvpr18_spotlight_v4.mp4)]
