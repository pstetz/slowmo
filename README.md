# MRI SlowMo

author: Patrick Stetz [(gihub)](https://github.com/pstetz)

### Motivation

One problem in MRI imagining is the low resolution temporal resolution of imaging.  There is a physical limit in MRI imaging that snapshots of one layer can only be taken every few seconds.  In addition, it is difficult if not immpossible to have snapshots of different layers of the brain taken at the same time.

This project attempts to alleviate both of these issues by making use of advances in Deep Learning technology.  A team from NVIDIA has created a model that can create high quality slow motion videos from regular videos.  The problems faced here are essentially the same.  We want to create regular videos from extremely choppy snapshots.

### Acknowledgements

The team whose paper heavily inspired me and their [paper](https://people.cs.umass.edu/~hzjiang//projects/superslomo/).

Huaizu Jiang, Deqing Sun, Varun Jampani, Ming-Hsuan Yang, Erik Learned-Miller, Jan Kautz. Super SloMo: High Quality Estimation of Multiple Intermediate Frames for Video Interpolation. CVPR, 2018 (spotlight). [[PDF](https://arxiv.org/pdf/1712.00080.pdf)][[CVPR spotlight video](https://people.cs.umass.edu/~hzjiang//projects/superslomo/superslomo_cvpr18_spotlight_v4.mp4)]