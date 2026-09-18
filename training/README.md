# Custom Kannada voice training

This directory prepares and documents a custom-voice workflow for recordings
you own or are authorised to use. It is intentionally separate from the web
app and does not commit source audio or generated checkpoints to Git.

## 1. Prepare your recording

Run this from the repository root, supplying your own recording path:

```bash
python3 training/prepare_dataset.py "/path/to/your-recording.mp3"
```

It writes candidate 1.5–12 second WAV clips in `training/data/wavs/` and a
blank `training/data/metadata.csv`. Review every clip: remove music, other
speakers, noise, and clips with inaccurate boundaries. Then fill the
`transcript` field with the exact spoken text.

To create drafts locally, install `faster-whisper` and run:

```bash
python3 training/transcribe_drafts.py training/data
```

This marks rows as `draft_transcript`; every draft must be corrected before
changing its status to `approved`.

For Kannada synthesis, Kannada transcripts and clean Kannada speech are the
most useful training data. The supplied 12-minute recording is enough for a
prototype after careful cleaning, but additional clean recordings improve
naturalness and pronunciation.

## 2. Fine-tune with F5-TTS on a cloud NVIDIA GPU

This Mac is not suitable for fine-tuning: it has 8 GB unified memory and no
installed PyTorch runtime. Use a cloud machine with an NVIDIA GPU, then clone
the official F5-TTS source beside this application:

```bash
git clone https://github.com/SWivid/F5-TTS.git vendor/F5-TTS
```

Follow the upstream training and fine-tuning instructions. Point its dataset
configuration at the reviewed WAV files and transcript manifest from
`training/data/`. Do not start a training run until all transcripts have been
checked: incorrect text teaches pronunciation errors.

### GitHub Actions cloud runner

This repository includes `.github/workflows/f5-tts-cloud-train.yml`. It runs
only on a separately provisioned Ubuntu NVIDIA GPU machine registered with
your repository as a self-hosted Actions runner labelled:

```text
self-hosted, linux, x64, gpu, f5-tts
```

Copy your private `training/data/` folder to `/opt/dhvani-training/data` on
that machine; do not commit it. In `metadata.csv`, review each clip, enter the
exact transcript, and change its status to `approved`. Run the workflow once
with **prepare only** enabled. It will reject missing or unreviewed rows. Only
then run it again with **prepare only** disabled to begin fine-tuning.

## 3. Serve the trained model

After a successful fine-tune, place only the model configuration/checkpoint
reference in an environment-specific location (not Git) and configure the web
server to use that model. Model weights and raw voice recordings are excluded
from this repository to prevent accidental publication.

## Safety and privacy

Only train a voice with the speaker's permission. Before sharing this project,
verify that `training/data/`, model checkpoints, and original recordings are
not staged for commit.
