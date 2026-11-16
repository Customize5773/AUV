# Pool visual assets (2027)

Generated locally by `bash tools/ros.sh python tools/prepare_pool_assets.py` from `ros2_ws`. No external art or runtime download.

- `water.obj`: two triangles at z=0; normal-map UV repeats every metre. Placed at z=0.005 by the arena generator.
- `water-normal.png`: periodic, static tangent-space ripples, 128×128 RGB.
- `liner.obj`: six triangles matching the existing 2027 bathymetry, 1 mm above the collision floor. UV repeats every 0.5 m.
- `tile.png`: neutral blue-grey tile/grout, 128×128 RGB.

These are visual assets only: no displacement, moving waves, refraction, calibrated turbidity or hydrodynamic force. See [report 66](../../../../../plan/66-visual-air-dan-kolam.md).
