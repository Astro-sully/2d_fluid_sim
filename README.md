# 2D Fluid Simulation Demo

An interactive 2D fluid simulation written in Python with Pygame. The demo
combines a laminar left-to-right inflow with the ability to draw solid
obstacles that interact with the flow in real time.

## Features

- Stable fluids style solver with configurable grid resolution.
- Velocity magnitude visualization overlay (toggleable).
- Brush and eraser tools for painting obstacles directly into the flow field.
- Adjustable brush radius using the mouse scroll wheel.
- Reset control to clear the simulation state.

## Requirements

- Python 3.10+
- [Pygame](https://www.pygame.org/docs/)
- NumPy

Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Running the demo

```bash
python main.py
```

Use the left panel to select brushes, adjust resolution, and toggle the
velocity overlay. Left-click and drag in the main viewport to paint obstacles,
right-click to erase, and use the scroll wheel to change the brush size.

Press `R` to reset the simulation at any time.
