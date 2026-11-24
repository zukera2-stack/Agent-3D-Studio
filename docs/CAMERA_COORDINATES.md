# Stage 02 camera axes, unit grids and registration

World: right-handed X = transverse width, +Y = front of vehicle, Z = height, with 1 Blender-compatible BU unit (not assumed metre or Factorio tile). Screen origin upper-left; pixel centers are x+0.5, y+0.5.

Camera basis: forward = normalize(target - position), right = normalize(forward cross up_hint), up = right cross forward. Positive camera depth = point towards scene. Orthographic scale = image_height_px / vertical_span_BU. Perspective focal pixels = height / (2*tan(FOV_y/2)), divided by positive depth.

Canonical views:
- side: from world +X, image horizontal = +Y, upward = +Z.
- top: from world +Z, image horizontal = +X, upward = +Y.
- front: from world +Y, image horizontal = -X, upward = +Z.
- rear: from world -Y, image horizontal = +X, upward = +Z.
- hero: perspective camera (+X,+Y,+Z); not used for orthographic measurement.

Grid: SVG embeds actual camera render PNG, with world origin at 0,0,0. Minor lines are every 0.1 BU, major every 1 BU. SVG is regenerated from the 3D source; it is NOT a two-way editable engineering drawing.

Calibration: a3ds.calibration.fit_landmarks receives measured world U/V and image pixel X/Y anchors, fits one positive isotropic pixels-per-BU scale and two translations. U increases pixel-right, V pixel-up. RMS is reported and optional max_rms_pixels rejects contradictory landmarks. This is manual coordinate calibration only; do not claim hidden geometry is recoverable or that the artist sketch supplies exact ortho dimensions.

Near/far triangle clipping occurs in camera coordinates before perspective division. RGB and mask are rendered by CPU triangles with Z-buffer. No antialiasing, physically based rendering, real-time editor or automatic fit at Stage 02.
