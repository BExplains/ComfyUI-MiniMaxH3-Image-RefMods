"""Append VAE-only image references to native MiniMax H3 conditioning."""

from comfy_api.latest import ComfyExtension, io


def encode_references(vae, images):
    from comfy.ldm.minimax.vae import MiniMaxH3ImageVAE
    from comfy_extras.nodes_minimax_h3 import (
        IMAGE_REF_SHORT_EDGE,
        IMAGE_REF_VAE_MAX_SHORT_EDGE,
        _resize_to,
        _size_short_edge,
    )

    if not isinstance(vae.first_stage_model, MiniMaxH3ImageVAE):
        raise ValueError("Connect the MiniMax H3 Image VAE.")

    count = sum(batch.shape[0] for batch in (images or {}).values() if batch is not None and batch.ndim == 4)
    if count > 15:
        raise ValueError("Use at most 15 reference images including batch members.")
    refs = []
    for name in sorted(images or {}, key=lambda name: int(name.rsplit("_", 1)[-1])):
        batch = images[name]
        if batch is None:
            continue
        if batch.ndim != 4 or batch.shape[-1] < 3 or min(batch.shape[:3]) < 1:
            raise ValueError(f"{name} must be a nonempty IMAGE batch [B,H,W,C] with RGB channels.")
        size = _size_short_edge(
            batch.shape[2], batch.shape[1],
            IMAGE_REF_SHORT_EDGE, IMAGE_REF_VAE_MAX_SHORT_EDGE,
        )
        for index in range(batch.shape[0]):
            # A 3D VAE may treat batch images as consecutive video frames.
            # Encoding one still per call preserves independent references.
            pixels = _resize_to(batch[index:index + 1], size)
            latent = vae.encode(pixels)
            if latent.ndim != 5 or tuple(latent.shape[:3]) != (1, 24, 1):
                raise ValueError(
                    f"Expected H3 Image latent [1,24,1,H,W], got {tuple(latent.shape)}."
                )
            refs.append({
                "kind": "image",
                "latent_h": latent.shape[-2],
                "latent_w": latent.shape[-1],
                "latent": latent,
            })
    if not refs:
        raise ValueError("Connect at least one reference image.")
    return refs


class H3ImageReferences(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="BExplainsH3ImageReferences",
            display_name="H3 Image References (BExplains)",
            category="BExplains/MiniMax H3",
            description=(
                "Encode every connected image as an independent H3 Image reference. "
                "Appends references to existing conditioning. Each batch member is a separate "
                "reference. The text encoder receives no pictures from this node."
            ),
            inputs=[
                io.Conditioning.Input("conditioning"),
                io.Vae.Input("vae", tooltip="MiniMax H3 Image VAE."),
                io.Autogrow.Input(
                    "images",
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Image.Input("image"),
                        prefix="image_",
                        min=1,
                        max=15,
                    ),
                ),
            ],
            outputs=[io.Conditioning.Output(display_name="conditioning")],
        )

    @classmethod
    def execute(cls, conditioning, vae, images):
        if not conditioning:
            raise ValueError("Connect H3 text conditioning.")
        refs = encode_references(vae, images)

        result = []
        for embedding, metadata in conditioning:
            values = dict(metadata)
            values["minimax_refs"] = list(metadata.get("minimax_refs", [])) + list(refs)
            result.append([embedding, values])
        return io.NodeOutput(result)


class CreateH3ImageRefMod(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="BExplainsCreateH3ImageRefMod",
            display_name="Create H3 Image RefMod (BExplains)",
            category="BExplains/MiniMax H3",
            description="Encode images with the H3 Image VAE and save one standard RefMod bundle. Outputs normal H3_REF_MODS.",
            inputs=[
                io.Vae.Input("vae"),
                io.String.Input("name", default="my_image_refmod"),
                io.Autogrow.Input("images", template=io.Autogrow.TemplatePrefix(
                    input=io.Image.Input("image"), prefix="image_", min=1, max=15)),
            ],
            outputs=[io.Custom("H3_REF_MODS").Output("mods"), io.String.Output("saved_path")],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, vae, name, images):
        import importlib
        import json
        import os
        import tempfile
        from pathlib import Path
        import folder_paths
        import nodes
        from safetensors.torch import save_file

        name = name.strip()
        if not name or name in (".", "..") or any(c in name for c in '/\\:*?"<>|'):
            raise ValueError("Use a filename without folders or reserved filename characters.")
        if name.lower().endswith(".safetensors"):
            name = name[:-12]
        if not name or name.endswith((".", " ")):
            raise ValueError("Enter a valid RefMod name.")

        loader = nodes.NODE_CLASS_MAPPINGS.get("MiniMaxH3RefModsLoader")
        if loader is None:
            raise ValueError("Install ComfyUI-MiniMaxH3Mod to create compatible RefMod objects.")
        runtime = importlib.import_module(loader.__module__)
        refmod_class = runtime.H3RefMod

        refs = encode_references(vae, images)
        if len(refs) > 15:
            raise ValueError("Use at most 15 reference images including batch members.")
        mods = []
        for index, ref in enumerate(refs):
            latent = ref["latent"].detach().cpu().contiguous().clone()
            mod = refmod_class(
                name=f"{name}_image_{index + 1}", kind="image", latent=latent,
                latent_h=latent.shape[-2], latent_w=latent.shape[-1], latent_t=1,
                mode="encode", source="image",
                source_shape=f"1x{latent.shape[-2]}x{latent.shape[-1]}",
                tags=["1 img, 0 vid"], concept_type="identity",
            )
            mods.append((mod, 1.0))

        roots = folder_paths.get_folder_paths("refmods")
        directory = Path(roots[0]) if roots else Path(folder_paths.models_dir) / "refmods"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{name}.safetensors"
        metadata = {
            "_format_version": 5, "kind": "bundle", "name": name,
            "members": [mod.metadata() for mod, _ in mods],
        }
        tensors = {f"ref_{i}": mod.latent for i, (mod, _) in enumerate(mods)}
        descriptor, temporary = tempfile.mkstemp(prefix=".image-refmod-", suffix=".tmp", dir=directory)
        os.close(descriptor)
        try:
            save_file(tensors, temporary, metadata={"refmod_meta": json.dumps(metadata)})
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return io.NodeOutput(mods, str(path))


class H3ImageReferencesExtension(ComfyExtension):
    async def get_node_list(self):
        return [H3ImageReferences, CreateH3ImageRefMod]


async def comfy_entrypoint():
    return H3ImageReferencesExtension()
