from turtle import clear
from matplotlib.pyplot import step
import numpy as np
from gym import Env
from abc import (ABC, abstractmethod)
from skimage import draw
from PIL import Image

from .generator import Generator
from .utils import (rigid_body_2d, shape_to_vertices, to_homogenous)
from .constants import COLORS


class Box2DBase(ABC, Env, Generator):

    @abstractmethod
    def __init__(self, 
                 max_episode_steps,
                 steps_per_action, 
                 time_steps=1.0/60.0, 
                 vel_iters=10, 
                 pos_iters=10,
                 **kwargs):
        """Box2D environment base class.

        args:
            max_episode_steps: maximum number per episode
            steps_per_action: number of simulation steps per action
            time_steps: simulation frequency
            vel_iters: Box2D velocity numerical solver iterations per time step  
            pos_iters: Box2D positional numerical solver iterations per time step  
        """
        Generator.__init__(self, **kwargs)
        self._max_episode_steps = max_episode_steps
        self._steps_per_action = steps_per_action
        self._time_steps = time_steps
        self._vel_iters = vel_iters
        self._pos_iters = pos_iters
        self._setup_spaces()
        self._render_setup()
    
    @classmethod
    def load(cls,
             env,
             **kwargs,
        ):
        """Load environment from pre-existing b2World.

        args:
            env: Gym environment sublcass of Box2DBase
            **kwargs: keyword arguments of Box2DBase
        """
        env_kwargs = {
            "env": env.env,
            "world": env.world,
            "geometry_params": {
                "global_x": env._t_global[0],
                "global_y": env._t_global[1]
            }
        }
        env_kwargs.update(kwargs)
        env = cls(**env_kwargs)
        return env

    @abstractmethod
    def reset(self):
        """Reset environment state.
        """
        if self.world is not None:
            for body in self.world.bodies:
                self.world.DestroyBody(body) 

        self.steps = 0
        is_valid = False
        while not is_valid:
            next(self)
            self._setup_spaces()
            is_valid = self._is_valid()
        self._render_setup()
        observation = self._get_observation()
        return observation

    @abstractmethod
    def step(self, clear_forces=True):
        """Take environment steps at self._time_steps frequency.
        """
        self.simulate(self._steps_per_action, clear_forces=clear_forces)
        self.steps += 1
        steps_exceeded = self.steps >= self._max_episode_steps
        return steps_exceeded
    
    def simulate(self, time_steps, clear_forces=True):
        for _ in range(time_steps):
            self.world.Step(self._time_steps, self._vel_iters, self._pos_iters)
            if clear_forces: self.world.ClearForces()
        self.world.ClearForces()

    @abstractmethod
    def _setup_spaces(self):
        """Setup observation space, action space, and supporting attributes.
        """
        raise NotImplementedError
            
    @abstractmethod
    def _get_observation(self):
        """Observation model.
        """
        raise NotImplementedError

    @abstractmethod
    def _get_reward(self, observation):
        """Scalar reward function.
        """
        raise NotImplementedError
    
    @abstractmethod
    def _is_done(self):
        """Returns True if terminal state has been reached.
        """

    @abstractmethod
    def _is_valid(self):
        """Check if start state is valid.
        """

    def _render_setup(self, mode="human"):
        """Initialize rendering parameters.
        """
        if mode == "human" or mode == "rgb_array":
            # Get image dimensions according the playground size
            workspace = self._get_shape_kwargs("playground")
            (w, h), t = workspace["size"], workspace["t"]
            r = 1 / t
            assert r.is_integer()
            y_range = int((w + 2*t) * r)
            x_range = int((h + t) * r)
            image = np.ones((x_range + 1, y_range + 1, 3), dtype=np.float32) * 255

            # Resolve reference frame transforms
            global_to_workspace = rigid_body_2d(0, -self._t_global[0], -self._t_global[1], r)
            workspace_to_image = rigid_body_2d(np.pi/2, h, w/2 + t, r)
            global_to_image_px = workspace_to_image @ global_to_workspace

            # Render static world bodies
            static_image = image.copy()
            for object_name, object_data in self.env.items():
                if object_data["type"] != "static": continue
                for _, shape_data in object_data["shapes"].items():
                    vertices = to_homogenous(shape_to_vertices(**shape_data))
                    vertices[:, :2] *= r
                    vertices_px = np.floor(global_to_image_px @ vertices.T).astype(int)
                    x_idx, y_idx = draw.polygon(vertices_px[0, :], vertices_px[1, :])

                    # Avoid rendering overlapping static objects
                    if object_data["class"] != "workspace":
                        static_mask = np.amin(static_image, axis=2) == 255
                        idx_filter = static_mask[x_idx, y_idx]
                        x_idx, y_idx = x_idx[idx_filter], y_idx[idx_filter]

                    color = object_data["render_kwargs"]["color"] if "render_kwargs" in object_data else "black"
                    static_image[x_idx, y_idx] = COLORS[color]

            # Rendering attributes
            self._r = r
            self._global_to_image_px = global_to_image_px
            self._image = image
            self._static_image = static_image
        
    def render(self, mode="human", width=None, height=None):
        """Render sprites on all 2D bodies and set background to white.
        """
        if mode == "human" or mode == "rgb_array":
        
            # Render all world shapes
            dynamic_image = self._image.copy()
            for _, object_data in self.env.items():
                if object_data["type"] == "static": continue
                for shape_name, shape_data in object_data["shapes"].items():
                    position = np.array(object_data["bodies"][shape_name].position, dtype=np.float32)
                    vertices = to_homogenous(shape_to_vertices(np.zeros_like(position), shape_data["box"])).T
                    # Must orient vertices by angle about object centroid
                    angle = object_data["bodies"][shape_name].angle
                    vertices = rigid_body_2d(angle, 0, 0) @ vertices
                    vertices[:2, :] = (vertices[:2, :] + np.expand_dims(position, 1)) * self._r

                    vertices_px = np.floor(self._global_to_image_px @ vertices).astype(int)
                    x_idx, y_idx = draw.polygon(vertices_px[0, :], vertices_px[1, :], dynamic_image.shape)
                    color = object_data["render_kwargs"]["color"] if "render_kwargs" in object_data else "navy"
                    dynamic_image[x_idx, y_idx] = COLORS[color]
            
            x_idx, y_idx = np.where(np.amin(dynamic_image, axis=2) < 255)
            image = self._static_image.copy()
            image[x_idx, y_idx, :] = dynamic_image[x_idx, y_idx, :]

            image = Image.fromarray(np.round(image).astype(np.uint8), "RGB")
            if width is not None or height is not None:
                width = width if width is not None else image.shape[1]
                height = height if height is not None else image.shape[0]
                image = image.resize((width, height))

            return np.array(image, dtype=np.uint8)
