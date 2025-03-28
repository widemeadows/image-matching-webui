import sys
from pathlib import Path
import subprocess
import torch

from ..utils.base_model import BaseModel

lanet_path = Path(__file__).parent / '../../third_party/lanet'
sys.path.append(str(lanet_path))
from network_v0.model import PointModel
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class LANet(BaseModel):
    default_conf = {
        'model_name': 'v0',
        'keypoint_threshold': 0.1,
    }
    required_inputs = ['image']
    def _init(self, conf):
        model_path = lanet_path / 'checkpoints' / f'PointModel_{conf["model_name"]}.pth'
        if not model_path.exists():
            print(f"No model found at {model_path}")
        self.net = PointModel(is_test=True)
        state_dict = torch.load(model_path, map_location='cpu')
        self.net.load_state_dict(state_dict['model_state'])

    def _forward(self, data):
        image = data['image']
        keypoints, scores, descriptors = self.net(image)
        _, _, Hc, Wc = descriptors.shape

        # Scores & Descriptors
        kpts_score = torch.cat([keypoints, scores], dim=1).view(3, -1).t().cpu().detach().numpy()
        descriptors = descriptors.view(256, Hc, Wc).view(256, -1).t().cpu().detach().numpy()
        
        # Filter based on confidence threshold
        descriptors = descriptors[kpts_score[:, 0] > self.conf['keypoint_threshold'], :]
        kpts_score = kpts_score[kpts_score[:, 0] > self.conf['keypoint_threshold'], :]
        keypoints = kpts_score[:, 1:]
        scores = kpts_score[:, 0]

        return {
            'keypoints': torch.from_numpy(keypoints)[None],
            'scores': torch.from_numpy(scores)[None],
            'descriptors': torch.from_numpy(descriptors.T)[None],
        }
