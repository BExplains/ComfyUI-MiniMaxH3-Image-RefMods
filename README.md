# H3 Image RefMods — BExplains

**Package multiple image references into one reusable RefMod for MiniMax H3 Image.**

Create the reference once, save it as a `.safetensors` file, and reuse it in a normal H3 Image text-to-image workflow through the existing H3 RefMod loading and application nodes.

A character can have portraits, character sheets, different views, and different outfits in the same asset. You do not need separate RefMods for every outfit or an image-index selector to use the pack.

Inspired by **[ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod)** by **[Luisa / Luisacaotica](https://github.com/Luisacaotica)**. This extension uses that project's RefMod objects and version-5 bundle format. Install the original project alongside this extension: it supplies the standard loader and Apply nodes.

## Contents

- [Features](#features)
- [Requirements and installation](#requirements-and-installation)
- [Quick start](#quick-start)
- [Node reference](#node-reference)
- [Tested prompts](#tested-prompts)
- [How it works](#how-it-works)
- [Compatibility](#compatibility)
- [Resolution and performance](#resolution-and-performance)
- [Validation](#validation)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Reporting problems](#reporting-problems)
- [Credits](#credits)

## Features

- Encodes images with the **MiniMax H3 Image VAE**.
- Stores each image as an independent reference inside **one file**.
- Accepts expanding image inputs and IMAGE batches, up to **15 images total**.
- Supports different image dimensions across separate inputs.
- Uses ComfyUI's native H3 Image reference resizing.
- Outputs ordinary `H3_REF_MODS` for the original project's Apply node.
- Saves a standard version-5 RefMod bundle for later loading.
- Includes an alternative inline node that appends references to conditioning without saving.

Creating a pack needs the image VAE and source images. It does not require a video diffusion checkpoint, video VAE, audio model, or Qwen for extraction. Final image generation still needs your normal H3 Image checkpoint, text encoder, sampler, and decoder.

This is reference encoding, not LoRA training. It does not modify model weights or learn trigger words.

## Requirements and installation

Requires current ComfyUI with native H3 Image support, the **H3 Image VAE**, and [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod).

From your ComfyUI installation directory:

```bash
cd custom_nodes
git clone https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod.git
git clone <IMAGE_REFMOD_REPOSITORY_URL> BExplains_H3_Image_References
```

Skip the first clone if you already have ComfyUI-MiniMaxH3Mod installed. Follow its [dependency installation instructions](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod#install) if this is a new installation.

Restart ComfyUI and refresh the browser. Find **Create H3 Image RefMod (BExplains)** under **BExplains / MiniMax H3**.

Use the **image VAE** in the creator. No video checkpoint, video VAE, or audio model is needed.

<!-- Before publication: replace IMAGE_REFMOD_REPOSITORY_URL with this repository's actual GitHub clone URL. -->

## Quick start

### Create a pack

1. Add **Create H3 Image RefMod (BExplains)**.
2. Connect **Load VAE**, selecting the H3 Image VAE, to `vae`.
3. Connect your reference images to the expanding image inputs.
4. Enter a name, such as `my_character`.
5. Queue the workflow.

The node writes `my_character.safetensors` into the first registered RefMod directory, falling back to `ComfyUI/models/refmods/`. The `saved_path` output reports the full destination.

The creator is an output node, so saving works without a sampler connected. It always saves when it executes; this version has no save toggle.

**An existing file with the same name is replaced.** Use a different name to preserve an earlier variant. File replacement is atomic.

### Use the result immediately

Connect the creator's `mods` output to the normal **Apply H3 RefMod** node. Connect your normal H3 text conditioning to Apply, then use its resulting conditioning in the H3 Image sampling workflow.

Start with neutral/default Apply controls and strength `1.0` for a comparison baseline. The original extension provides the Apply controls; this creator does not add sampling controls.

### Load it in another workflow

1. Add the original **Load H3 RefMods** node.
2. Refresh the available RefMods and select the saved file.
3. Connect the loaded `mods` to **Apply H3 RefMod**.
4. Apply it to your normal H3 Image text conditioning.
5. Generate an image.

You no longer need the original source images or creator in the generation graph. Avoid applying the same pack through both the creator output and a loader in the same run unless duplicate conditioning is intentional.

## Node reference

### Create H3 Image RefMod (BExplains)

Internal ID: `BExplainsCreateH3ImageRefMod`.

| Input                     | Meaning                                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `vae`                     | MiniMax H3 Image VAE.                                                                                                          |
| `name`                    | Filename stem. An optional `.safetensors` suffix is accepted. Folder separators and reserved filename characters are rejected. |
| Expanding `image_` inputs | References. Every IMAGE batch member becomes a separate reference.                                                             |

| Output       | Meaning                                           |
| ------------ | ------------------------------------------------- |
| `mods`       | Normal `H3_REF_MODS` for the original Apply node. |
| `saved_path` | Full path to the saved file.                      |

This version does not expose compression, refinement steps, masks, per-image descriptions, a save toggle, or a subfolder setting. The name is a filename, not a path.

### H3 Image References (BExplains)

Internal ID: `BExplainsH3ImageReferences`.

An alternative for direct experiments without creating a saved pack.

| Connection             | Meaning                                        |
| ---------------------- | ---------------------------------------------- |
| `conditioning` input   | Existing H3 text conditioning.                 |
| `vae`                  | MiniMax H3 Image VAE.                          |
| Expanding image inputs | References to encode.                          |
| `conditioning` output  | Conditioning with the new references appended. |

This node preserves the text embedding and existing metadata, appending image references to `minimax_refs`. It does not replace references already present.

The original RefMod extension is required by the **creator** and the normal Load/Apply workflow. The inline node itself uses native conditioning and does not import that extension at execution time.

## Tested prompts

These prompts were used in the reported character tests. Keep the prompt and sampling settings identical when comparing direct references with a saved pack.

### Police uniform

```text
subject_definitions:
<Subject 1> is one woman represented across all supplied references. The different views and outfits depict the same person. She has shoulder-length wavy dark brown hair and wears the navy police uniform shown in the references.

description:
<Subject 1> walking cautiously down an alley, looking around as if searching for clues.
```

### Summer outfit, same pack

```text
subject_definitions:
<Subject 1> is one woman represented across all supplied references. The different views and outfits depict the same person. She has shoulder-length wavy dark brown hair and wears a summer outfit shown in the references.

description:
<Subject 1> walking cautiously down an alley, looking around as if searching for clues.
```

Only the outfit phrase changes. The references stay in the same packaged asset.

The creator does not insert these definitions, rewrite the prompt, assign subject IDs, or select outfits automatically. Ordinary Apply injects visual latents into diffusion conditioning; it does not send the source pictures to Qwen.

For multiple character packs, define the characters clearly and test the association. This creator does not implement automatic pack-to-`<Subject n>` binding. Reliable multi-character generation has not been validated here.

## How it works

For every supplied image, the extension:

1. Determines its reference size and resizes it with native H3 Image helpers.
2. Calls the H3 Image VAE on that single image.
3. Validates the latent shape as `[1, 24, 1, H, W]`.
4. Creates an image-kind reference with its own latent dimensions.
5. Saves all references together in one standard RefMod bundle.

That shape represents one reference: batch size `1`, `24` latent channels, and a singleton temporal dimension. The singleton is part of the expected tensor layout, not a requirement to generate video or install video weights.

IMAGE batches are iterated image by image. Independent references are not concatenated into a multi-frame video latent. A character sheet supplied as one image remains one image containing several views; the extension does not detect people or split sheets into crops.

| File component | Representation                   |
| -------------- | -------------------------------- |
| Metadata       | `refmod_meta` JSON               |
| Format version | `5`                              |
| Container kind | `bundle`                         |
| Member kind    | `image`                          |
| Tensor keys    | `ref_0`, `ref_1`, and so on      |
| Member data    | Independent H3 Image VAE latents |

Latents are detached, copied to CPU, and stored contiguously. The creator returns upstream `H3RefMod` objects at strength `1.0`.

This is unpooled reference encoding. It does not optimize a compressed grid or semantically remove clothing, backgrounds, or composition. Those attributes can still influence generation.

## Compatibility

| Scenario                                    | Status                                                            |
| ------------------------------------------- | ----------------------------------------------------------------- |
| H3 Image VAE creation                       | Implemented and exercised in the reported generation tests.       |
| Normal Apply with creator output            | Supported through upstream `H3_REF_MODS` objects.                 |
| Normal Load of a saved pack                 | Uses the upstream version-5 bundle format.                        |
| Several outfits in one character pack       | Demonstrated with police and summer prompts.                      |
| Different dimensions across inputs          | Supported.                                                        |
| IMAGE batches                               | Each member is encoded separately; total maximum remains 15.      |
| Conversion of existing video-VAE packs      | Not implemented; recreate from source images using the image VAE. |
| Video generation from these image-VAE packs | Not validated.                                                    |
| Reliable automatic multi-character binding  | Not implemented or validated.                                     |
| Audio, motion extraction, compression       | Outside the current scope.                                        |

Container compatibility is different from VAE latent-space compatibility. A loader accepting a file does not establish that another model can interpret its tensors correctly.

The creator discovers the upstream class through `MiniMaxH3RefModsLoader`. Changes to that dependency's internal exports may require an extension update.

## Resolution and performance

### Reference size and output size are separate

Reference preprocessing follows the installed ComfyUI implementation. This creator has no reference-resolution slider. Generation resolution controls the output, not the encoding of these source images.

Upsizing an existing source does not recover missing detail. Badges, lettering, jewelry, and other small features can vary. The reported tests measure principal subject count and outfit selection, not exact reproduction of every emblem.

### Fifteen images includes batch members

Three single-image inputs plus a four-image batch use seven references. A sheet counts as one input image even when it depicts multiple views.

This check applies to this node's inputs. Loading other packs or appending references elsewhere can increase the final conditioning count.

### Saved references still cost attention

A saved pack avoids repeated VAE encoding of the original pictures. During generation, the diffusion model still processes the retained reference tokens. More references and larger latents can increase memory use and sampling time.

The creator does not expose a token budget, pool latents, or silently truncate inputs. More than 15 input images raises an error. No minimum VRAM or measured speedup is claimed.

### Storage

The first registered `refmods` directory is used, including roots configured through ComfyUI's model-path configuration. The fallback is `ComfyUI/models/refmods/`. The directory is created when necessary. A write failure is reported rather than silently choosing another drive.

Keep original source images if you may need to recreate a pack. The saved file contains latents and metadata, not copies of the original PNG/JPEG files.

## Validation

Initial reported generation results used one character pack containing different views and outfits:

| Test                            | Observed result                                                                 |
| ------------------------------- | ------------------------------------------------------------------------------- |
| Police-uniform prompt           | 5 of 5 shown seeds produced one principal woman in the requested uniform.       |
| Summer-outfit prompt, same pack | 3 of 3 shown seeds produced one principal woman in the requested summer outfit. |

These results demonstrate repeatability within the tested workflow and outfit selection from one asset. They are not a general success-rate estimate across all characters and settings.

Development checks with simulated components covered schema, ordering, batch handling, metadata preservation, bundle structure, filename validation, and atomic replacement. They complement the real generation tests rather than measuring model quality themselves.

Earlier experiments produced duplicated women, mixed outfits, and character-sheet layouts. The working creator uses the image VAE, native preprocessing, and independent image members. The experiments did not isolate which individual difference caused the improvement; a temporal dimension alone has not been established as the cause of those failures.

## Troubleshooting

| Problem                               | Check                                                                                                                                                                            |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Node missing from search              | Restart the backend, refresh the browser, check startup errors, and ensure `__init__.py` is directly inside the extension folder. Search the full display name or `BExplains`.   |
| Wrong-VAE error                       | Select the MiniMax H3 Image VAE, not a video VAE or another model family's VAE.                                                                                                  |
| Install-RefMod error                  | Install the original dependency and confirm its loader registered successfully. Restart after installation.                                                                      |
| RefMod class import error             | Check the original extension's installation/version and retain the complete traceback.                                                                                           |
| More-than-15 error                    | Count batch members, not just connected sockets.                                                                                                                                 |
| Saved pack missing from loader        | Check `saved_path`, refresh RefMods/node definitions, and confirm that directory is searched. Restart if necessary.                                                              |
| Older asset replaced                  | Matching filenames are overwritten. Give preserved variants different names.                                                                                                     |
| Multiple women or copied sheet layout | Verify the selected pack and image VAE; check for duplicate application; compare against the documented prompt using identical settings. Sheets are not automatically segmented. |
| Wrong outfit                          | Specify the intended outfit in the prompt. The creator stores the references but does not choose between outfits.                                                                |
| Small emblem differences              | Inspect source detail and encoding size. Identity consistency is not pixel-exact reproduction.                                                                                   |
| Slow generation or high VRAM          | Check active reference count, latent sizes, other packs, and output resolution.                                                                                                  |

For a fair comparison, keep checkpoint, VAE, prompt, seed, dimensions, steps, CFG, and Apply settings constant. Change one factor at a time.

## FAQ

### Is a RefMod a LoRA?

No. It stores VAE reference latents rather than trained diffusion-weight changes.

### Do I need an existing image to edit?

No. Use text-to-image. The supplied pictures are references, not a required starting canvas.

### Can I keep several outfits in one file?

Yes. The police and summer tests use the same asset and change the outfit phrase in the prompt.

### Do I need to select an image index?

No. The ordinary workflow loads and applies the complete pack.

### Does Qwen see the images inside it?

Not through this creator and ordinary Apply. The diffusion model receives the reference latents. A separate vision-aware text encoder is a different prompt-processing path.

### Can I use character sheets?

Yes; the demonstrated pack included them. A sheet remains one image containing several views. This does not guarantee that every sheet avoids layout transfer.

### Can I rename a video RefMod to make it an image RefMod?

No. Renaming does not change its encoding. Recreate it with source images and the image VAE.

### Are all seeds guaranteed to work?

The shown seeds succeeded across two outfit prompts. Broader reliability depends on references, model, prompt, and settings.

## Reporting problems

Include:

- ComfyUI version/commit and this extension's version.
- ComfyUI-MiniMaxH3Mod version.
- Exact H3 Image checkpoint and VAE filenames.
- Workflow JSON or an image containing workflow metadata.
- Prompt, seed, dimensions, sampling settings, and Apply controls.
- Source count, batch sizes, and whether any references are sheets.
- Full traceback for execution errors or representative outputs for visual failures.

Remove private information from shared workflows. For original loader/Apply behavior, consult [ComfyUI-MiniMaxH3Mod's issues](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod/issues) and identify whether it reproduces without this creator.

## Credits

- **[Luisa / Luisacaotica](https://github.com/Luisacaotica)** — [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod), the inspiration and provider of the compatible classes and format. Read the original [README](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod#readme) and [license](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod/blob/main/LICENSE).
- **[ComfyUI contributors](https://github.com/Comfy-Org/ComfyUI)** — native H3 Image support, VAE integration, reference preprocessing, and conditioning infrastructure.
- **MiniMax** — the H3 model family.
- **BExplains** — image-specific creation and the documented character/outfit tests.

This is a separate extension; attribution does not imply endorsement by the original author, ComfyUI, or MiniMax. The original project's license applies to its own code. Supply a separate license for this repository before public distribution.
