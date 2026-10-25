"""Does the policy aim at the sponge? Offline test on the first frame of every episode.

For each episode, feed the first frame and read the predicted action chunk STEP frames ahead
(the arm should be heading to the sponge by then). Compare the predicted shoulder_pan with
what the demonstration actually did at that time. If the policy localizes the sponge, the
prediction follows the demo across episodes (high correlation). Then swap the top image with
another episode's: a policy that looks at the sponge changes its aim with the image.

Usage: .venv/bin/python policy_reach_test.py <dataset_dir_name> [<dataset_dir_name> ...]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors

ROOT = Path.home() / ".cache/huggingface/lerobot/tenyyprn"
STEP = 60  # frames ahead (2 s at 30 fps)
PAN = 0


def main(dataset_names: list[str]):
    for name in dataset_names:
        path = f"outputs/act_{name}/checkpoints/last/pretrained_model"
        policy = ACTPolicy.from_pretrained(path).to("cuda").eval()
        pre, post = make_pre_post_processors(policy.config, pretrained_path=path)
        ds = LeRobotDataset(f"tenyyprn/{name}", root=ROOT / name)
        image_keys = [k for k in policy.config.input_features if k.startswith("observation.images.")]
        df = pd.read_parquet(sorted((ROOT / name / "data").rglob("*.parquet")))
        starts = df.groupby("episode_index")["index"].min().tolist()

        def aim(sample, images):
            batch = {"observation.state": sample["observation.state"].unsqueeze(0), "task": [sample["task"]]}
            batch.update({k: v.unsqueeze(0) for k, v in images.items()})
            with torch.no_grad():
                chunk = policy.predict_action_chunk(pre(batch))  # (1, chunk, 6), normalized
                actions = post(chunk[0])  # (chunk, 6) in degrees
            return actions[min(STEP, actions.shape[0] - 1), PAN].item()

        demo, pred, swapped = [], [], []
        for n, i in enumerate(starts):
            s = ds[i]
            o = ds[starts[(n + len(starts) // 2) % len(starts)]]  # a different episode
            imgs = {k: s[k] for k in image_keys}
            demo.append(ds[i + STEP]["action"][PAN].item())
            pred.append(aim(s, imgs))
            swapped.append(aim(s, {**imgs, "observation.images.top": o["observation.images.top"]}))
        demo, pred, swapped = map(np.array, (demo, pred, swapped))
        print(f"\n{name}: shoulder_pan {STEP / 30:.0f} s after the start, {len(starts)} episodes")
        print(f"  demo spread (std)            : {demo.std():5.1f} deg")
        print(f"  prediction spread (std)      : {pred.std():5.1f} deg")
        print(f"  |prediction - demo| (mean)   : {abs(pred - demo).mean():5.1f} deg")
        print(f"  correlation prediction/demo  : {np.corrcoef(pred, demo)[0, 1]:5.2f}")
        print(f"  change when top image swapped: {abs(swapped - pred).mean():5.1f} deg")


if __name__ == "__main__":
    main(sys.argv[1:])
