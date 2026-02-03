# Vendor: react-body-highlighter

## Source
- **Package**: react-body-highlighter (npm)
- **Repository**: https://github.com/giavinh79/react-body-highlighter
- **Version**: 2.0.5
- **License**: MIT
- **Author**: GV79 (Giavinh)

## Attribution
The SVG polygon data in this directory was extracted from the `react-body-highlighter` 
npm package. The original polygons were leveraged from `react-native-body-highlighter` 
by HichamELBSI (https://github.com/HichamELBSI/react-native-body-highlighter).

## What's Included
- `LICENSE` - Original MIT license from react-body-highlighter
- `body_anterior.svg` - Front view body diagram (converted from anteriorData)
- `body_posterior.svg` - Back view body diagram (converted from posteriorData)
- `ATTRIBUTION.md` - This file

## Modifications Made
1. Converted polygon point strings to SVG `<polygon>` elements
2. Added CSS classes for styling integration
3. Added `data-muscle` attributes for JavaScript interaction
4. Wrapped in proper SVG container with viewBox
5. Added bilateral mirroring (left/right sides share same muscle key)

## Original Muscle Slugs
The upstream library uses these muscle identifiers:

### Front (Anterior)
- chest
- abs
- obliques
- biceps
- triceps
- neck
- front-deltoids
- head
- abductors (thigh abductors)
- quadriceps
- knees
- calves
- forearm

### Back (Posterior)
- head
- trapezius
- back-deltoids
- upper-back
- triceps
- lower-back
- forearm
- gluteal
- abductor (hip abductor)
- hamstring
- knees
- calves
- left-soleus
- right-soleus

## Mapping to Canonical Keys
See `docs/muscle_selector_vendor.md` for the complete mapping between 
upstream slugs and our canonical muscle keys.
