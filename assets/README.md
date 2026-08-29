# Assets

Four images, three of them in the README. This says how they were made,
because the next one has to match and nothing else in the repository
records it.

| file | where | job |
|---|---|---|
| `banner.jpg` | README, top | the hero, alone on the first screen |
| `ceremony.jpg` | README, after the first command block | the sitting, cropped to a band |
| `icon.png` | README footer | the seal, at 96 px — transparent, so it sits on either theme |
| `icon.jpg` | nothing references it | superseded by the PNG when the seal lost its opaque square; kept only if a surface that cannot take transparency needs it |
| `social-preview.jpg` | a repository *setting*, uploaded in Settings → General; no file references it | the card a link unfurls into |

## How they were made

**Synthesised, then graded.** The illustrations were generated with a
commercial image model and are not hand-drawn; nothing here depends on
that and no attribution is required, but a maintainer who needs a fifth
image should know it rather than guess.

**The palette is not the generator's.** It comes from the sibling
repository's measured night: in `journeyman`'s banner the dark regions
carry a blue-minus-red difference of about +39, while generated frames
arrived at +2..+12 — a warm coffee-black that reads as a different house.
Rather than argue with the model, the frames are corrected afterwards by
a deterministic pass and verified on the same measure.

Two things that pass were learned the expensive way and are worth
repeating:

- **Navy belongs only in the floor.** An early pass pushed it up into the
  mid-tones and flattened the one legible region of the banner: its lit
  area fell from 2.5% to 0.9%, against about 7.2% in the reference. A
  colour metric can go green while the picture dies, so the lit-area
  fraction is measured too.
- **Look at the file.** Both faults above passed the metric and were
  caught by opening the result.

The grading pass and the social-card generator live in Codechu's internal
tooling rather than here — they operate on source frames this repository
does not carry. If you need a matching asset and cannot reach them, the
two numbers above are the whole specification: blue-minus-red ≈ +39 in the
darks, lit area ≈ 7% of the frame.
