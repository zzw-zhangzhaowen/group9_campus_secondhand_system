# Design B layered illustrations

These illustrations were drawn from geometric shapes by `gui_gao/tools/build_scene_art.py`. They do not use third-party photos, site screenshots or trademarks.

Each scene has transparent `*-base.png` and `*-float.png` layers at 840 × 600 pixels. Floating layers provide short hover motion. The login floating layer is the lamp beam, initially hidden.

The enquiry route and activity clock use the base PNG plus independently drawn SVG or Tk Canvas markers/hands. This allows animation, pause and reduced motion without rotating the whole illustration. They do not show transaction progress or real time.

Colours are blue, navy, lime, cream and apricot. The art is decorative, not a real item photo. The browser uses the `home` scene; the desktop homepage uses a collage of item illustrations.

The app reads the PNGs directly. Regeneration is optional and requires Pillow and the font configured in the generator; adjust the font path to your development machine.
