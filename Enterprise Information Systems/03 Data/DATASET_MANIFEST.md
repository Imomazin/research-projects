# P2 Dataset Manifest

## 1. NIH ChestX-ray14

**Role:** healthcare cross-institution federation validation  
**Source:** https://nihcc.app.box.com/v/ChestXray-NIHCC  
**Scale:** 112,120 frontal-view radiographs from 30,805 patients in the canonical release  
**Federation plan:** patient-disjoint simulated hospitals with controlled label and prevalence heterogeneity  
**Repository policy:** do not commit raw images; retain source citation, file manifest, checksums, patient-disjoint partition map and preprocessing configuration  
**Status:** source identified, acquisition/preprocessing to be frozen

## 2. ISIC

**Role:** second healthcare imaging domain for cross-domain robustness  
**Official source:** https://challenge.isic-archive.com/data/  
**Initial candidate:** ISIC 2018 Task 3/HAM10000 because it provides a stable labelled lesion-classification benchmark at a tractable scale; final year/task will be frozen after compute and licence review  
**Federation plan:** site-like/client partitions generated without patient/lesion leakage  
**Repository policy:** no raw images; record exact challenge version, licence, checksums and split-generation seed  
**Status:** source identified, benchmark version not yet frozen

## 3. IEEE-CIS Fraud Detection

**Role:** cross-bank financial fraud validation  
**Source:** https://www.kaggle.com/competitions/ieee-fraud-detection/data  
**Scale:** competition data approximately 1.35 GB; transaction and identity tables joined by `TransactionID`  
**Access:** Kaggle account plus acceptance of competition rules required  
**Federation plan:** simulated banks created from defensible non-IID partitions using product/device/geographic/proxy structure without using the target to manufacture unrealistic clients  
**Repository policy:** competition data is not redistributed; only acquisition instructions, preprocessing code, partition manifests and derived aggregate results are committed  
**Status:** source identified, gated acquisition pending

## Engineering-only smoke tests

MNIST/CIFAR-class data may be used only for CI and rapid algorithm verification. They are not sufficient as the primary empirical evidence for the grant paper because Meridian already has earlier work in that benchmark family.
