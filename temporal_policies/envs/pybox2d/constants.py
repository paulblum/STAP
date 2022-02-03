ENV_OBJECTS = {
    "playground": {
        "class": "workspace",
        "type": "static",
        "shape_kwargs": {
            "size": [12.0, 8.0],
            "t": 0.1
        },
        "render_kwargs": {
            "color": "black"
        }
    },
    "box": {
        "class": "receptacle",
        "type": "static",
        "shape_kwargs": {
            "size": [3.0, 3.0],
            "t": 0.1,
            "config": -1,
            "dx": -3.5
        },
        "render_kwargs": {
            "color": "brown"
        }
    },
    "obstacle": {
        "class": "block",
        "type": "static",
        "shape_kwargs": {
            "size": [1.0, 1.5],
            "dx": 3.0
        },
        "render_kwargs": {
            "color": "red"
        }
    },
    "item": {
        "class": "block",
        "type": "dynamic",
        "shape_kwargs": {
            "size": [1.0, 1.5],
            "dy": 5.0
        },
        "body_kwargs": {
            "density": 1.0,
            "friction": 0.5,
            "restitution": 0.0
        },
        "render_kwargs": {
            "color": "emerald"
        }
    },
}


COLORS = {
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "rouge": (128, 0, 0),
    "green": (0, 255, 0),
    "emerald": (0, 128, 0),
    "blue": (0, 0, 255),
    "navy": (0, 0, 128),
    "brown": (100, 42, 42), 
    "black": (0, 0, 0)
}
