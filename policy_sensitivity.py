"""What does the policy look at? Swap the camera image or the arm state and measure how much the predicted action changes.

Large change when swapping the image  -> the policy uses vision.
Large change only when swapping state -> the policy mostly replays trajectories from proprioception.
shoulder_pan reacting to the image is the key sign that the policy localizes the part.

Usage: .venv/bin/python policy_sensitivity.py <dataset_dir_name> [<dataset_dir_name> ...]
  e.g. .venv/bin/python policy_sensitivity.py so101_pick_20261018_195353 so101_pick_merged25
"""
import sys
from pathlib import Path

import numpy as np
import torch

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors

ROOT = Path.home() / ".cache/huggingface/lerobot/tenyyprn"
NAMES = ["pan", "lift", "elbow", "wflex", "wroll", "grip"]
NUM_SAMPLES = 60


def main(dataset_names: list[str]):
    rng = np.random.default_rng(0)
    for name in dataset_names:
        path = f"outputs/act_{name}/checkpoints/last/pretrained_model"
        policy = ACTPolicy.from_pretrained(path).to("cuda").eval()
        pre, post = make_pre_post_processors(policy.config, pretrained_path=path)
        ds = LeRobotDataset(f"tenyyprn/{name}", root=ROOT / name)

        image_keys = [k for k in policy.config.input_features if k.startswith("observation.images.")]

        def predict(state, images, task):
            batch = {"observation.state": state.unsqueeze(0), "task": [task]}
            batch.update({k: v.unsqueeze(0) for k, v in images.items()})
            with torch.no_grad():
                policy.reset()
                return post(policy.select_action(pre(batch))).cpu().numpy().ravel()

        rows = {"error vs demo": [], "swap arm state": []}
        for k in image_keys:
            rows[f"swap {k.split('.')[-1]} (other)"] = []
            rows[f"swap {k.split('.')[-1]} (black)"] = []
        for i in range(0, len(ds), max(1, len(ds) // NUM_SAMPLES)):
            s, o = ds[i], ds[int(rng.integers(len(ds)))]
            imgs = {k: s[k] for k in image_keys}
            base = predict(s["observation.state"], imgs, s["task"])
            rows["error vs demo"].append(abs(base - s["action"].numpy()))
            rows["swap arm state"].append(abs(base - predict(o["observation.state"], imgs, s["task"])))
            for k in image_keys:
                cam = k.split(".")[-1]
                rows[f"swap {cam} (other)"].append(abs(base - predict(s["observation.state"], {**imgs, k: o[k]}, s["task"])))
                rows[f"swap {cam} (black)"].append(abs(base - predict(s["observation.state"], {**imgs, k: torch.zeros_like(s[k])}, s["task"])))

        print(f"\n{name}  (mean |Δaction|, degrees / gripper %)")
        print(f"  {'':22}" + "".join(f"{n:>7}" for n in NAMES))
        for label, vals in rows.items():
            print(f"  {label:22}" + "".join(f"{v:7.1f}" for v in np.mean(vals, 0)))


if __name__ == "__main__":
    main(sys.argv[1:])
