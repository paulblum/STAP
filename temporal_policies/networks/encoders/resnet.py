import gym  # type: ignore
import numpy as np  # type: ignore
import torch  # type: ignore

from temporal_policies import envs
from temporal_policies.networks.encoders.base import Encoder


class ResNet(Encoder):
    """ResNet encoder."""

    def __init__(
        self,
        env: envs.Env,
        out_features: int,
        variant: str = "resnet18",
        pretrained: bool = True,
        freeze: bool = False,
    ):
        state_space = gym.spaces.Box(
            low=-float("inf"),
            high=float("inf"),
            shape=(out_features,),
            dtype=np.float32,
        )
        super().__init__(env, state_space)

        if variant in ("resnet18", "resnet34"):
            dim_conv4_out = 256
        elif variant in ("resnet50", "resnet101", "resnet152"):
            dim_conv4_out = 1024
        else:
            raise NotImplementedError

        resnet = torch.hub.load(
            "pytorch/vision:v0.10.0", variant, pretrained=pretrained
        )
        if freeze:
            for param in resnet.parameters():
                param.requires_grad = False

        # First four layers of ResNet (output of conv4).
        resnet_conv4 = list(resnet.children())[:-3]
        self.features = torch.nn.Sequential(*resnet_conv4)

        # Reduce to single pixel.
        self.avgpool = torch.nn.AdaptiveAvgPool2d((1, 1))

        # Output required feature dimensions.
        self.fc = torch.nn.Linear(dim_conv4_out, out_features)

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        # [B, 3, H, W] => [B, 512, H / 16, W / 16].
        x = self.features(observation)

        # [B, 512, H / 16, W / 16] => [B, conv4_out].
        x = self.avgpool(x).squeeze(-1).squeeze(-1)

        # [B, conv4_out, 1, 1] => [B, out_features].
        x = self.fc(x)

        return x
