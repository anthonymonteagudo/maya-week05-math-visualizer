# Jettelly notes and teaching decisions

Source: Fabrizio Espindola, *Visualizing Equations: Essential Math for Game Devs*, Vol. 1, v0.0.8, supplied PDF. Page numbers below are printed pages. These are instructor adaptations, not instructions copied from the book.

- **p. 16: visible directions, explicit reference point.** The dot example derives two normalized directions from a common point. Our connected S-to-E and E-to-W arrows serve the arm example, but must be identified explicitly; the joint's interior angle is not the angle between those consecutive arrows. A future facing demo should use two common-origin arrows.
- **p. 56: reset supports experimentation.** The cross tool exposes inputs, output, and a reset button. Keep reset obvious, scope it to the active lesson, and explain each preset by what students should observe.
- **p. 94: simple geometry makes rotation visible.** The quaternion example rotates cube vertices. Use a simple asymmetric object or marked corner. A realistic hand is optional context, not a prerequisite for understanding rotation. The degree/radian conversion is an API requirement of that implementation, not a universal quaternion rule.
- **p. 123: use a direction indicator.** The Euler example transforms a direction arrow along with its axes. An unmarked symmetric object can hide orientation changes. Keep the marked proxy and explain its purpose.

## Simplicity rules for this tool

One question, a small number of inputs, one visible result. Keep spaces and the optional coding exercise out of the basic vector workflow. Name examples by their mathematical consequence, apply them immediately, and state that dragging changes the initial example. Do not add anatomy, skinning, materials, or another motion while explaining orientation interpolation.

The current rotation comparison is **Euler-angle linear interpolation versus quaternion SLERP**. Euler is a representation, whereas SLERP is an interpolation method; they are not equivalent categories. Both methods use the same endpoints and a stationary marked proxy. At t=0.5, Euler LERP gives XYZ (45,45,0); quaternion SLERP generally gives a different orientation. Uniform t gives constant angular speed along the quaternion SLERP arc. This is not a proof of gimbal lock, which needs its own example.

SLERP is supplementary to the book's worked tools. See the official [Unreal quaternion SLERP reference](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Math/Quat/Slerp_Quat) and [Microsoft quaternion SLERP reference](https://learn.microsoft.com/en-us/dotnet/api/system.numerics.quaternion.slerp).

Model recommendation: keep two rigid arm segments and a clear wrist/hand direction. If a recognizable hand is added later, use a simple palm plus thumb silhouette as an optional context view. Detailed anatomical modeling and deformation would distract from this lesson's vector, space, and rotation questions.
